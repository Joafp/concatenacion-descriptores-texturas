"""Políticas de Adquisición Secuencial para FSC-Tex.

Implementa:
1. Política de Cascada de Dos Etapas (Control de referencia por umbral de margen).
2. Política Miope (Horizonte 1): balancea la ganancia esperada inmediata g(s, a) contra lambda * Delta t.
3. Política No Miope (Horizonte 2 y 3): recurrencia de Bellman con parada explicita STOP.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from fsc_tex.cost_model import HardwareCostModel
from fsc_tex.state_graph import State, StateGraph


class BaselineTwoStageCascadePolicy:
    """Control de referencia: Cascada estática de dos etapas.
    
    Clasifica con la base. Si el margen es inferior a un umbral tau,
    adquiere de golpe el subconjunto de bloques Top-k; si es superior, ejecuta STOP.
    """

    def __init__(self, target_budget_q: float, threshold_tau: float, topk_blocks: List[str]):
        self.target_budget_q = target_budget_q
        self.threshold_tau = threshold_tau
        self.topk_blocks = list(topk_blocks)

    def decide(self, margin: float) -> str:
        """Devuelve 'STOP' o 'ACQUIRE_TOPK'."""
        if margin < self.threshold_tau:
            return "ACQUIRE_TOPK"
        return "STOP"


class SequentialAcquisitionPolicy:
    """Política de Adquisición Secuencial FSC-Tex (Horizonte 1 a 3)."""

    def __init__(
        self,
        graph: StateGraph,
        cost_model: HardwareCostModel,
        horizon: int = 1,
        cost_lambda: float = 0.05,
        model_type: str = "ridge",
        random_state: int = 42,
    ):
        """
        Parámetros:
          graph: StateGraph de estados y transiciones.
          cost_model: HardwareCostModel para calcular Delta t(a | s).
          horizon: horizonte de planificación (1: miope, 2 o 3: Bellman no miope).
          cost_lambda: ponderador de costo en la función objetivo (pérdida por unidad de tiempo).
          model_type: 'ridge' o 'mlp'.
        """
        if horizon not in (1, 2, 3):
            raise ValueError(f"Horizonte debe ser 1, 2 o 3, recibido {horizon}")
        self.graph = graph
        self.cost_model = cost_model
        self.horizon = horizon
        self.cost_lambda = cost_lambda
        self.model_type = model_type
        self.random_state = random_state

        # Modelos de valor / ganancia por nivel de horizonte
        # self.value_models[h] es un modelo que estima V_h o Q_h para cada acción
        self.models: Dict[Tuple[int, str], any] = {}
        self.stop_risk_model = None

    def _make_regressor(self):
        if self.model_type == "ridge":
            return Pipeline([
                ("scaler", StandardScaler()),
                ("reg", Ridge(alpha=1.0, random_state=self.random_state)),
            ])
        elif self.model_type == "mlp":
            return Pipeline([
                ("scaler", StandardScaler()),
                ("reg", MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=200, random_state=self.random_state)),
            ])
        else:
            raise ValueError(f"model_type desconocido: {self.model_type}")

    def fit_transitions(
        self,
        features_by_state: Dict[str, np.ndarray],
        losses_by_state: Dict[str, np.ndarray],
        max_budget: float | None = None,
    ):
        """Ajusta los modelos de valor hacia atrás (backward induction) de forma desplegable.
        
        Parámetros:
          features_by_state: {state_id: matriz (N, d_phi) de características observables}.
          losses_by_state: {state_id: vector (N,) de pérdidas 0-1 del clasificador en ese estado}.
          max_budget: presupuesto máximo opcional para filtrar acciones no factibles durante el ajuste.
        """
        initial_id = self.graph.initial_state.id
        n_samples = len(losses_by_state[initial_id])

        # 1. Ajustar modelo de riesgo de parada R_stop(s) = E[Loss(s) | phi(s)]
        all_feats = []
        all_losses = []
        for sid, feats in features_by_state.items():
            if sid in losses_by_state:
                all_feats.append(feats)
                all_losses.append(losses_by_state[sid])
        X_all = np.vstack(all_feats)
        y_all = np.concatenate(all_losses)

        self.stop_risk_model = self._make_regressor()
        self.stop_risk_model.fit(X_all, y_all)

        # 2. Agrupar estados por profundidad (longitud de bloques)
        # depth 1: estado base; depth 2: 2 bloques; depth 3: 3 bloques, etc.
        states_by_depth: Dict[int, List[State]] = {}
        for s in self.graph.states.values():
            d = len(s)
            states_by_depth.setdefault(d, []).append(s)

        max_d = max(states_by_depth.keys())

        # 3. Inducción hacia atrás por nivel de horizonte h = 1 .. self.horizon
        for h in range(1, self.horizon + 1):
            for d in range(max_d - 1, 0, -1):
                for curr_state in states_by_depth.get(d, []):
                    if curr_state.id not in features_by_state or curr_state.id not in losses_by_state:
                        continue
                    
                    feats_curr = features_by_state[curr_state.id]
                    loss_curr = losses_by_state[curr_state.id]

                    rem_b_curr = None
                    if max_budget is not None:
                        spent_curr = self.cost_model.cumulative_cost(curr_state.blocks)
                        rem_b_curr = max(0.0, max_budget - spent_curr)

                    # Evaluar cada acción candidata factible
                    for cand in self.graph.candidate_blocks:
                        if curr_state.contains(cand):
                            continue
                        nxt_state = curr_state.add(cand)
                        if nxt_state.id not in losses_by_state or nxt_state.id not in features_by_state:
                            continue

                        cost = self.cost_model.incremental_cost(cand, curr_state.blocks)

                        # Máscara de factibilidad presupuestaria:
                        if rem_b_curr is not None and cost > rem_b_curr:
                            continue  # Acción imposible dentro del presupuesto

                        if h == 1:
                            # Miope (H1): valor futuro es la pérdida observada del siguiente estado
                            target_q = self.cost_lambda * cost + losses_by_state[nxt_state.id]
                        else:
                            # No miope (H2 / H3): inducción de Bellman desplegable (sin oráculo).
                            # Evaluamos el valor de continuación V_{h-1}(nxt_state) usando
                            # exclusivamente las predicciones de los modelos ya ajustados.
                            feats_nxt = features_by_state[nxt_state.id]
                            v_stop_nxt = self.stop_risk_model.predict(feats_nxt)
                            continuation_options = [v_stop_nxt]

                            rem_b_nxt = (rem_b_curr - cost) if rem_b_curr is not None else None

                            if len(nxt_state) < self.graph.max_depth:
                                for cand_nxt in self.graph.candidate_blocks:
                                    if nxt_state.contains(cand_nxt):
                                        continue
                                    if rem_b_nxt is not None:
                                        c_nxt = self.cost_model.incremental_cost(cand_nxt, nxt_state.blocks)
                                        if c_nxt > rem_b_nxt:
                                            continue  # Acción imposible en continuación
                                    
                                    m_prev = self.models.get((h - 1, nxt_state.id, cand_nxt)) or self.models.get((h - 1, cand_nxt))
                                    if m_prev is not None:
                                        pred_q_nxt = m_prev.predict(feats_nxt)
                                        continuation_options.append(pred_q_nxt)

                            # V_{h-1}(nxt_state) = min(R_stop, min_{a' factible} Q_{h-1}(nxt_state, a'))
                            v_nxt = np.min(np.column_stack(continuation_options), axis=1)
                            target_q = self.cost_lambda * cost + v_nxt

                        m_q = self._make_regressor()
                        m_q.fit(feats_curr, target_q)
                        self.models[(h, curr_state.id, cand)] = m_q
                        if curr_state.id == initial_id:
                            self.models[(h, cand)] = m_q

    def select_action(
        self,
        current_state: State,
        state_features: np.ndarray,
        remaining_budget: float | None = None,
    ) -> Tuple[str, float]:
        """Elige la acción que minimiza el costo-riesgo esperado V_h(s, b).
        
        Parámetros:
          current_state: Estado actual S.
          state_features: vector phi(s, x) de características observables.
          remaining_budget: Presupuesto remanente disponible (en las mismas unidades que cost_model).
                            Si es None, la búsqueda es sin restricción presupuestaria explícita.
        
        Devuelve: (acción_elegida, valor_esperado).
        """
        feat_row = state_features.reshape(1, -1)
        r_stop = float(self.stop_risk_model.predict(feat_row)[0])

        best_action = "STOP"
        best_val = r_stop

        # Si ya se alcanzó la profundidad máxima o presupuesto <= 0, solo STOP
        if len(current_state) >= self.graph.max_depth or (remaining_budget is not None and remaining_budget <= 0):
            return "STOP", best_val

        # Evaluar acciones factibles
        effective_h = min(self.horizon, self.graph.max_depth - len(current_state))
        if effective_h < 1:
            return "STOP", best_val

        feasible_actions = self.graph.get_actions(current_state, remaining_budget, self.cost_model)

        for cand in feasible_actions:
            if cand == "STOP":
                continue
            
            # Buscar primero modelo específico de estado (effective_h, current_state.id, cand), luego (effective_h, cand)
            key_state = (effective_h, current_state.id, cand)
            key_fallback = (effective_h, cand)

            model = self.models.get(key_state) or self.models.get(key_fallback)
            if model is not None:
                pred_q = float(model.predict(feat_row)[0])
                if pred_q < best_val:
                    best_val = pred_q
                    best_action = cand

        return best_action, best_val

    def rollout_trajectory(
        self,
        initial_state: State,
        get_features_fn,
        budget: float | None = None,
    ) -> Tuple[State, List[str], float]:
        """Ejecuta una trayectoria completa descontando explícitamente el presupuesto en cada paso.
        
        Parámetros:
          initial_state: estado inicial S_0 (típicamente State((base_block,))).
          get_features_fn: función invocable (state, remaining_budget) -> features vector np.ndarray.
          budget: presupuesto total disponible para toda la inferencia. Si es None, no hay tope.
        
        Devuelve: (estado_final, acciones_ejecutadas, costo_total_acumulado).
        """
        curr_state = initial_state
        actions_taken: List[str] = []
        rem_b = budget
        if rem_b is not None:
            spent_init = self.cost_model.cumulative_cost(curr_state.blocks)
            rem_b = max(0.0, rem_b - spent_init)

        while len(curr_state) < self.graph.max_depth and (rem_b is None or rem_b > 0):
            feat = get_features_fn(curr_state, rem_b)
            action, _ = self.select_action(curr_state, feat, remaining_budget=rem_b)
            if action == "STOP":
                break
            inc_c = self.cost_model.incremental_cost(action, curr_state.blocks)
            if rem_b is not None:
                rem_b = max(0.0, rem_b - inc_c)
            curr_state = curr_state.add(action)
            actions_taken.append(action)

        total_cost = self.cost_model.cumulative_cost(curr_state.blocks)
        return curr_state, actions_taken, total_cost
