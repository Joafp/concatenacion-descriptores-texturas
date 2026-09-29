#!/usr/bin/env python3
"""
Estudio de Ablación Científica de Componentes de DynaTex-MoD
=============================================================
Evalúa el aporte individual y sinérgico de cada componente:
1. Baseline: Concatenación Plana (ResMLP estándar, cabeza lineal)
2. Ablación 1: Solo Proyecciones Balanceadas (fusión uniforme fija, cabeza lineal)
3. Ablación 2: Proyecciones Balanceadas + Compuertas Dinámicas (cabeza lineal)
4. Ablación 3: Proyecciones Balanceadas + Cabeza Cosine-Normalized (fusión uniforme fija)
5. DynaTex-MoD Completo: Proyecciones Balanceadas + Compuertas Dinámicas + Cabeza Cosine-Normalized
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from run_confirmatory_nested import FAMILIES, load_dataset, load_manifest


class AblationNet(nn.Module):
    def __init__(
        self,
        family_dims: dict[str, int],
        num_classes: int,
        proj_dim: int = 128,
        hidden_dim: int = 256,
        dropout: float = 0.15,
        use_projections: bool = True,
        use_gating: bool = True,
        use_cosine_head: bool = True,
        temperature: float = 0.5,
        initial_scale: float = 16.0,
    ):
        super().__init__()
        self.family_names = sorted(family_dims.keys())
        self.num_families = len(self.family_names)
        self.proj_dim = proj_dim
        self.use_projections = use_projections
        self.use_gating = use_gating
        self.use_cosine_head = use_cosine_head
        self.temperature = temperature

        total_input_dim = sum(family_dims.values())

        # 1. Proyecciones
        if use_projections:
            self.projections = nn.ModuleDict({
                fam: nn.Sequential(
                    nn.Linear(dim, proj_dim),
                    nn.LayerNorm(proj_dim),
                    nn.GELU(),
                    nn.Dropout(dropout),
                )
                for fam, dim in family_dims.items()
            })
            fused_in_dim = self.num_families * proj_dim
        else:
            # Sin proyecciones: entrada directa concatenada
            self.linear_in = nn.Sequential(
                nn.Linear(total_input_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.GELU(),
                nn.Dropout(dropout),
            )
            fused_in_dim = hidden_dim

        # 2. Compuertas
        if use_projections and use_gating:
            gate_in_dim = self.num_families * proj_dim
            self.gating = nn.Sequential(
                nn.Linear(gate_in_dim, gate_in_dim // 2),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(gate_in_dim // 2, self.num_families),
            )

        # 3. Refinamiento
        if use_projections:
            self.refine = nn.Sequential(
                nn.Linear(fused_in_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
            )
        else:
            self.refine = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.GELU(),
                nn.Dropout(dropout),
            )

        # 4. Cabeza clasificadora
        if use_cosine_head:
            self.scale = nn.Parameter(torch.tensor(initial_scale))
            self.weight = nn.Parameter(torch.empty(num_classes, hidden_dim))
            nn.init.kaiming_uniform_(self.weight, a=np.sqrt(5))
        else:
            self.head = nn.Linear(hidden_dim, num_classes)

    def forward(self, family_inputs: dict[str, torch.Tensor]) -> torch.Tensor:
        B = next(iter(family_inputs.values())).shape[0]

        if not self.use_projections:
            # Concatenación cruda
            concat_raw = torch.cat([family_inputs[f] for f in self.family_names], dim=-1)
            h = self.linear_in(concat_raw)
            z = self.refine(h)
        else:
            proj_list = [self.projections[f](family_inputs[f]) for f in self.family_names]

            if self.use_gating:
                concat_p = torch.cat(proj_list, dim=-1)
                logits_g = self.gating(concat_p) / self.temperature
                gates = F.softmax(logits_g, dim=-1)
                gated_proj = [proj * gates[:, i : i + 1] for i, proj in enumerate(proj_list)]
                fused = torch.cat(gated_proj, dim=-1)
            else:
                # Fusión uniforme fija (sin compuertas: 1/M para cada una)
                fused = torch.cat([p * (1.0 / self.num_families) for p in proj_list], dim=-1)

            z = self.refine(fused)

        if self.use_cosine_head:
            z_norm = F.normalize(z, p=2, dim=-1)
            w_norm = F.normalize(self.weight, p=2, dim=-1)
            return self.scale * F.linear(z_norm, w_norm)
        else:
            return self.head(z)


class AblationClassifier(BaseEstimator, ClassifierMixin):
    def __init__(
        self,
        family_slices: dict[str, tuple[int, int]],
        proj_dim: int = 128,
        hidden_dim: int = 256,
        dropout: float = 0.15,
        use_projections: bool = True,
        use_gating: bool = True,
        use_cosine_head: bool = True,
        temperature: float = 0.5,
        lr: float = 5e-4,
        weight_decay: float = 1e-3,
        max_epochs: int = 80,
        batch_size: int = 64,
        patience: int = 14,
        random_state: int = 42,
    ):
        self.family_slices = family_slices
        self.proj_dim = proj_dim
        self.hidden_dim = hidden_dim
        self.dropout = dropout
        self.use_projections = use_projections
        self.use_gating = use_gating
        self.use_cosine_head = use_cosine_head
        self.temperature = temperature
        self.lr = lr
        self.weight_decay = weight_decay
        self.max_epochs = max_epochs
        self.batch_size = batch_size
        self.patience = patience
        self.random_state = random_state
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def _split(self, X_t: torch.Tensor) -> dict[str, torch.Tensor]:
        return {fam: X_t[:, s:e] for fam, (s, e) in self.family_slices.items()}

    def fit(self, X: np.ndarray, y: np.ndarray):
        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)
        self.classes_ = np.unique(y)
        family_dims = {fam: e - s for fam, (s, e) in self.family_slices.items()}

        X_t = torch.tensor(X, dtype=torch.float32, device=self.device)
        y_t = torch.tensor(y, dtype=torch.long, device=self.device)

        self.net_ = AblationNet(
            family_dims=family_dims,
            num_classes=len(self.classes_),
            proj_dim=self.proj_dim,
            hidden_dim=self.hidden_dim,
            dropout=self.dropout,
            use_projections=self.use_projections,
            use_gating=self.use_gating,
            use_cosine_head=self.use_cosine_head,
            temperature=self.temperature,
        ).to(self.device)

        opt = torch.optim.AdamW(self.net_.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        crit = nn.CrossEntropyLoss(label_smoothing=0.1)

        n = X_t.shape[0]
        best_loss = float("inf")
        best_state = None
        bad = 0

        split_X_t = self._split(X_t)
        self.net_.train()
        for epoch in range(self.max_epochs):
            perm = torch.randperm(n, device=self.device)
            total = 0.0
            for i in range(0, n, self.batch_size):
                idx = perm[i : i + self.batch_size]
                batch_dict = {fam: t[idx] for fam, t in split_X_t.items()}
                logits = self.net_(batch_dict)
                loss = crit(logits, y_t[idx])
                opt.zero_grad()
                loss.backward()
                opt.step()
                total += loss.item() * idx.shape[0]

            avg = total / n
            if avg < best_loss - 1e-4:
                best_loss = avg
                best_state = {k: v.detach().clone() for k, v in self.net_.state_dict().items()}
                bad = 0
            else:
                bad += 1
                if bad >= self.patience:
                    break

        if best_state is not None:
            self.net_.load_state_dict(best_state)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        self.net_.eval()
        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32, device=self.device)
            logits = self.net_(self._split(X_t))
            preds = logits.argmax(dim=1).cpu().numpy()
        return self.classes_[preds]


def evaluate_dataset_ablations(dataset_name: str, embedding_root: Path | None = None, manifest_dir: Path | None = None):
    print(f"\n================================================================================")
    print(f"  ESTUDIO DE ABLACIÓN DE COMPONENTES: {dataset_name}")
    print(f"================================================================================")

    cache, y = load_dataset(REPO, dataset_name, embedding_root=embedding_root)
    groups, rows = load_manifest(manifest_dir or (REPO / "results/confirmatory"), dataset_name, y)

    family_blocks = {"classical": [], "cnn": [], "transformer": [], "self_supervised": []}
    for name in sorted(cache.keys()):
        fam = FAMILIES.get(name, "other")
        if fam in family_blocks:
            family_blocks[fam].append(cache[name])

    X_parts = []
    family_slices = {}
    curr_dim = 0
    for fam in sorted(family_blocks.keys()):
        arr = np.concatenate(family_blocks[fam], axis=1)
        dim = arr.shape[1]
        family_slices[fam] = (curr_dim, curr_dim + dim)
        curr_dim += dim
        X_parts.append(arr)
    X_full = np.concatenate(X_parts, axis=1)

    configurations = [
        ("1. ResMLP (Plana cruda, lineal)", {"proj": False, "gate": False, "cos": False}),
        ("2. Solo Proy. Balanceadas",       {"proj": True,  "gate": False, "cos": False}),
        ("3. Proy. + Compuertas",           {"proj": True,  "gate": True,  "cos": False}),
        ("4. Proy. + Cosine Head",          {"proj": True,  "gate": False, "cos": True}),
        ("5. DynaTex-MoD Completo (Todos)", {"proj": True,  "gate": True,  "cos": True}),
    ]

    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)

    for label, cfg in configurations:
        t0 = time.time()
        f1s, accs = [], []
        for tr, te in sgkf.split(X_full, y, groups):
            clf = AblationClassifier(
                family_slices=family_slices,
                proj_dim=128 if dataset_name != "SoilOriginal" else 256,
                hidden_dim=256,
                use_projections=cfg["proj"],
                use_gating=cfg["gate"],
                use_cosine_head=cfg["cos"],
                temperature=0.5,
                dropout=0.15,
                lr=5e-4,
                weight_decay=1e-3,
                batch_size=64,
                max_epochs=80,
                patience=14,
                random_state=42,
            )
            clf.fit(X_full[tr], y[tr])
            preds = clf.predict(X_full[te])
            f1s.append(f1_score(y[te], preds, average="macro"))
            accs.append(accuracy_score(y[te], preds))

        elapsed = time.time() - t0
        print(f"  {label:35s}: Macro-F1 = {np.mean(f1s):.4f} ± {np.std(f1s):.4f} | Acc = {np.mean(accs):.4f} ({elapsed:.1f}s)")


def main():
    # 1. FMD (Materiales)
    evaluate_dataset_ablations("FMD")
    # 2. SoilOriginal (Suelos)
    evaluate_dataset_ablations(
        "SoilOriginal",
        embedding_root=REPO / "embeddings_extensions",
        manifest_dir=REPO / "results/extensions/soil_original",
    )


if __name__ == "__main__":
    main()
