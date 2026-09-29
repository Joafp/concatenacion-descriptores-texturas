"""
DynaTex - Dynamic Mixture of Descriptors (MoD) Classifier
==========================================================
Original contribution for texture descriptor fusion.

Solves the key limitations identified in recent 2026 literature (AsTexNet, HyTexNet):
1. Replaces static/offline weighting (alpha, beta) with a dynamic, per-sample Gating Network.
2. Projects heterogeneous families (classical, CNN, Transformer, SSL) into balanced latent spaces.
3. Applies a Cosine-Normalized classification head to prevent norm/dimension domination.
4. Provides full sample-level interpretability (gating weights per family).
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.base import BaseEstimator, ClassifierMixin


class _DynaTexMoDNet(nn.Module):
    def __init__(
        self,
        family_dims: dict[str, int],
        num_classes: int,
        proj_dim: int = 128,
        hidden_dim: int = 256,
        dropout: float = 0.1,
        temperature: float = 1.0,
        initial_scale: float = 16.0,
    ):
        super().__init__()
        self.family_names = sorted(family_dims.keys())
        self.num_families = len(self.family_names)
        self.proj_dim = proj_dim
        self.temperature = temperature

        # 1. Proyección balanceada por familia
        self.projections = nn.ModuleDict({
            fam: nn.Sequential(
                nn.Linear(dim, proj_dim),
                nn.LayerNorm(proj_dim),
                nn.GELU(),
                nn.Dropout(dropout),
            )
            for fam, dim in family_dims.items()
        })

        # 2. Red de compuertas (Gating Network)
        gate_in_dim = self.num_families * proj_dim
        self.gating = nn.Sequential(
            nn.Linear(gate_in_dim, gate_in_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(gate_in_dim // 2, self.num_families),
        )

        # 3. Capa de fusión refinada (Residual Projection)
        fused_dim = self.num_families * proj_dim
        self.refine = nn.Sequential(
            nn.Linear(fused_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
        )

        # 4. Cabeza de clasificación normalizada por coseno
        self.scale = nn.Parameter(torch.tensor(initial_scale))
        self.weight = nn.Parameter(torch.empty(num_classes, hidden_dim))
        nn.init.kaiming_uniform_(self.weight, a=np.sqrt(5))

    def compute_gates_and_features(self, family_inputs: dict[str, torch.Tensor]):
        # Proyectar cada familia
        projected = [self.projections[fam](family_inputs[fam]) for fam in self.family_names]
        concat_proj = torch.cat(projected, dim=-1)

        # Predecir compuertas dinámicas
        gate_logits = self.gating(concat_proj) / self.temperature
        gates = F.softmax(gate_logits, dim=-1)  # (B, num_families)

        # Ponderación dinámica de cada representación
        gated_feats = []
        for i, proj in enumerate(projected):
            g = gates[:, i : i + 1]  # (B, 1)
            gated_feats.append(proj * g)

        fused = torch.cat(gated_feats, dim=-1)
        z = self.refine(fused)
        return z, gates

    def forward(self, family_inputs: dict[str, torch.Tensor]) -> torch.Tensor:
        z, _ = self.compute_gates_and_features(family_inputs)
        z_norm = F.normalize(z, p=2, dim=-1)
        w_norm = F.normalize(self.weight, p=2, dim=-1)
        logits = self.scale * F.linear(z_norm, w_norm)
        return logits


class DynaTexMoDClassifier(BaseEstimator, ClassifierMixin):
    """
    Clasificador DynaTex MoD sklearn-compatible para descriptores heterogéneos.
    """

    def __init__(
        self,
        family_slices: dict[str, tuple[int, int]],
        proj_dim: int = 128,
        hidden_dim: int = 256,
        dropout: float = 0.1,
        temperature: float = 1.0,
        initial_scale: float = 16.0,
        lr: float = 1e-3,
        weight_decay: float = 1e-4,
        max_epochs: int = 100,
        batch_size: int = 128,
        patience: int = 12,
        random_state: int = 42,
        device: str | None = None,
    ):
        self.family_slices = family_slices
        self.proj_dim = proj_dim
        self.hidden_dim = hidden_dim
        self.dropout = dropout
        self.temperature = temperature
        self.initial_scale = initial_scale
        self.lr = lr
        self.weight_decay = weight_decay
        self.max_epochs = max_epochs
        self.batch_size = batch_size
        self.patience = patience
        self.random_state = random_state
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def _split_families(self, X_t: torch.Tensor) -> dict[str, torch.Tensor]:
        return {
            fam: X_t[:, start:end]
            for fam, (start, end) in self.family_slices.items()
        }

    def fit(self, X: np.ndarray, y: np.ndarray):
        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)

        self.classes_ = np.unique(y)
        num_classes = len(self.classes_)
        family_dims = {fam: end - start for fam, (start, end) in self.family_slices.items()}

        X_t = torch.tensor(X, dtype=torch.float32, device=self.device)
        y_t = torch.tensor(y, dtype=torch.long, device=self.device)

        self.net_ = _DynaTexMoDNet(
            family_dims=family_dims,
            num_classes=num_classes,
            proj_dim=self.proj_dim,
            hidden_dim=self.hidden_dim,
            dropout=self.dropout,
            temperature=self.temperature,
            initial_scale=self.initial_scale,
        ).to(self.device)

        opt = torch.optim.AdamW(self.net_.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        # Label smoothing as recommended in AsTexNet (epsilon=0.1)
        crit = nn.CrossEntropyLoss(label_smoothing=0.1)

        n = X_t.shape[0]
        best_loss = float("inf")
        best_state = None
        bad = 0

        self.net_.train()
        for epoch in range(self.max_epochs):
            perm = torch.randperm(n, device=self.device)
            total = 0.0
            for i in range(0, n, self.batch_size):
                idx = perm[i : i + self.batch_size]
                batch_dict = {fam: t[idx] for fam, t in self._split_families(X_t).items()}
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
            family_dict = self._split_families(X_t)
            logits = self.net_(family_dict)
            preds = logits.argmax(dim=1).cpu().numpy()
        return self.classes_[preds]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        self.net_.eval()
        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32, device=self.device)
            family_dict = self._split_families(X_t)
            logits = self.net_(family_dict)
            probs = F.softmax(logits, dim=1).cpu().numpy()
        return probs

    def get_gating_weights(self, X: np.ndarray) -> dict[str, np.ndarray]:
        """Devuelve los pesos de compuerta por familia para cada muestra."""
        self.net_.eval()
        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32, device=self.device)
            family_dict = self._split_families(X_t)
            _, gates = self.net_.compute_gates_and_features(family_dict)
            gates_np = gates.cpu().numpy()
        return {fam: gates_np[:, i] for i, fam in enumerate(self.net_.family_names)}
