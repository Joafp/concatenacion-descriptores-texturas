"""Grafo de estados y representaciones observables para FSC-Tex.

Define los estados S subset {b_1, ..., b_22}, transiciones factibles y
el vector de características phi(S, x) observable por la política.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import numpy as np


@dataclass(frozen=True)
class State:
    """Estado inmutable representado por el conjunto ordenado de bloques adquiridos."""
    blocks: Tuple[str, ...]

    def __post_init__(self):
        # Garantizar orden canónico
        if self.blocks != tuple(sorted(self.blocks)):
            object.__setattr__(self, "blocks", tuple(sorted(self.blocks)))

    @property
    def id(self) -> str:
        return "+".join(self.blocks) if self.blocks else "empty"

    def contains(self, block: str) -> bool:
        return block in self.blocks

    def add(self, block: str) -> "State":
        if block in self.blocks:
            return self
        return State(tuple(sorted(self.blocks + (block,))))

    def __len__(self) -> int:
        return len(self.blocks)


class StateGraph:
    """Grafo acotado de estados y transiciones factibles."""

    def __init__(
        self,
        base_block: str,
        candidate_blocks: List[str],
        max_depth: int = 3,
        canonical_22_allowlist: List[str] | None = None,
    ):
        """
        Parámetros:
          base_block: bloque inicial de la etapa barata (ej. 'resnet50').
          candidate_blocks: lista ordenada de candidatos permitidos para adquisición.
          max_depth: número máximo de bloques acumulados por ruta (ej. 3).
          canonical_22_allowlist: lista de los 22 bloques para fijar índices de máscara.
        """
        self.base_block = base_block
        self.candidate_blocks = [c for c in candidate_blocks if c != base_block]
        self.max_depth = max_depth
        self.allowlist = canonical_22_allowlist or sorted([base_block] + self.candidate_blocks)
        self.block_to_idx = {b: i for i, b in enumerate(self.allowlist)}

        self.initial_state = State((base_block,))
        self.states: Dict[str, State] = {self.initial_state.id: self.initial_state}
        self.transitions: Dict[Tuple[str, str], str] = {}
        self._build_graph()

    def _build_graph(self):
        queue = [self.initial_state]
        while queue:
            curr = queue.pop(0)
            # Acción STOP siempre transiciona a terminal
            self.transitions[(curr.id, "STOP")] = "TERMINAL"

            if len(curr) < self.max_depth:
                for cand in self.candidate_blocks:
                    if not curr.contains(cand):
                        nxt = curr.add(cand)
                        if nxt.id not in self.states:
                            self.states[nxt.id] = nxt
                            queue.append(nxt)
                        self.transitions[(curr.id, cand)] = nxt.id

    def get_actions(self, state: State, remaining_budget: float | None = None, cost_model = None) -> List[str]:
        """Devuelve las acciones factibles desde el estado actual."""
        actions = ["STOP"]
        if len(state) >= self.max_depth or (remaining_budget is not None and remaining_budget <= 0):
            return actions

        if remaining_budget is not None and cost_model is None:
            raise ValueError("Si se proporciona remaining_budget, cost_model debe ser suministrado para comprobar factibilidad.")

        for cand in self.candidate_blocks:
            if not state.contains(cand):
                if remaining_budget is not None and cost_model is not None:
                    c = cost_model.incremental_cost(cand, state.blocks)
                    if c > remaining_budget:
                        continue
                actions.append(cand)
        return actions

    def encode_state_features(
        self,
        state: State,
        margin: float,
        top_scores: np.ndarray,
        remaining_budget: float = 1.0,
        content_embedding: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Construye el vector phi(s, x) observable por la política.
        
        Contenido:
        - Máscara binaria de 22 posiciones (qué bloques están adquiridos)
        - Margen de certeza del clasificador actual
        - Top-3 scores de separación de clases
        - Fracción de presupuesto restante
        - Proyección fija de contenido (opcional para representación enriquecida)
        """
        mask = np.zeros(len(self.allowlist), dtype=np.float32)
        for b in state.blocks:
            if b in self.block_to_idx:
                mask[self.block_to_idx[b]] = 1.0

        scores_pad = np.zeros(3, dtype=np.float32)
        if len(top_scores) > 0:
            n_take = min(3, len(top_scores))
            scores_pad[:n_take] = top_scores[:n_take]

        parts = [
            mask,
            np.array([margin, remaining_budget], dtype=np.float32),
            scores_pad,
        ]
        if content_embedding is not None:
            parts.append(np.asarray(content_embedding, dtype=np.float32).ravel())

        return np.concatenate(parts)

    def encode_state_features_batch(
        self,
        state: State,
        margins: np.ndarray,
        decision_functions: np.ndarray,
        remaining_budgets: np.ndarray | float = 1.0,
        content_embeddings: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Construye la matriz de características phi(s, X) para un lote de N muestras."""
        n_samples = len(margins)
        mask_row = np.zeros(len(self.allowlist), dtype=np.float32)
        for b in state.blocks:
            if b in self.block_to_idx:
                mask_row[self.block_to_idx[b]] = 1.0
        mask_batch = np.tile(mask_row, (n_samples, 1))

        if isinstance(remaining_budgets, (int, float)):
            budget_col = np.full((n_samples, 1), fill_value=float(remaining_budgets), dtype=np.float32)
        else:
            budget_col = np.asarray(remaining_budgets, dtype=np.float32).reshape(-1, 1)

        margin_col = np.asarray(margins, dtype=np.float32).reshape(-1, 1)

        # Top-3 scores ordenados descendentemente
        if decision_functions.ndim == 1 or decision_functions.shape[1] == 1:
            # Caso binario
            top3 = np.zeros((n_samples, 3), dtype=np.float32)
            top3[:, 0] = np.abs(decision_functions.ravel())
        else:
            sorted_scores = np.sort(decision_functions, axis=1)[:, ::-1]
            n_cols = min(3, sorted_scores.shape[1])
            top3 = np.zeros((n_samples, 3), dtype=np.float32)
            top3[:, :n_cols] = sorted_scores[:, :n_cols]

        parts = [mask_batch, margin_col, budget_col, top3]
        if content_embeddings is not None:
            parts.append(np.asarray(content_embeddings, dtype=np.float32))

        return np.hstack(parts)

