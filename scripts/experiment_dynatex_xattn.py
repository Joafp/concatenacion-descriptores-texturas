#!/usr/bin/env python3
"""
Experimentación Avanzada: DynaTex con Cross-Family Attention (X-Attn)
=====================================================================
Compara:
1. DynaTex-Gating (Default T=1.0)
2. DynaTex-Gating Sharpened (T=0.5)
3. DynaTex-XAttn (Cross-Family Multi-Head Attention entre los 4 tokens de familia)
4. DynaTex-GatedXAttn (Cross-Family Attention + Compuertas Dinámicas)
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


class CrossFamilyAttentionBlock(nn.Module):
    def __init__(self, num_families: int = 4, d_model: int = 128, nhead: int = 4, dropout: float = 0.1):
        super().__init__()
        self.fam_embed = nn.Parameter(torch.randn(num_families, d_model) * 0.02)
        self.attn = nn.MultiheadAttention(embed_dim=d_model, num_heads=nhead, dropout=dropout, batch_first=True)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 2, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, tokens: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # tokens: (B, num_families, d_model)
        x = tokens + self.fam_embed.unsqueeze(0)
        attn_out, attn_weights = self.attn(x, x, x)
        x = self.norm1(tokens + attn_out)
        out = self.norm2(x + self.ffn(x))
        return out, attn_weights


class AdvancedDynaTexNet(nn.Module):
    def __init__(
        self,
        family_dims: dict[str, int],
        num_classes: int,
        proj_dim: int = 128,
        hidden_dim: int = 256,
        dropout: float = 0.1,
        temperature: float = 1.0,
        fusion_mode: str = "gating",  # 'gating', 'xattn', 'gated_xattn'
        initial_scale: float = 16.0,
    ):
        super().__init__()
        self.family_names = sorted(family_dims.keys())
        self.num_families = len(self.family_names)
        self.proj_dim = proj_dim
        self.temperature = temperature
        self.fusion_mode = fusion_mode

        # 1. Proyecciones balanceadas por familia
        self.projections = nn.ModuleDict({
            fam: nn.Sequential(
                nn.Linear(dim, proj_dim),
                nn.LayerNorm(proj_dim),
                nn.GELU(),
                nn.Dropout(dropout),
            )
            for fam, dim in family_dims.items()
        })

        # 2. Módulos de fusión según modo
        if "xattn" in fusion_mode:
            self.xattn = CrossFamilyAttentionBlock(num_families=self.num_families, d_model=proj_dim, nhead=4, dropout=dropout)

        if "gating" in fusion_mode or "gated" in fusion_mode:
            gate_in_dim = self.num_families * proj_dim
            self.gating = nn.Sequential(
                nn.Linear(gate_in_dim, gate_in_dim // 2),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(gate_in_dim // 2, self.num_families),
            )

        # 3. Refinamiento
        fused_dim = self.num_families * proj_dim
        self.refine = nn.Sequential(
            nn.Linear(fused_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
        )

        # 4. Clasificador Cosine-Normalized
        self.scale = nn.Parameter(torch.tensor(initial_scale))
        self.weight = nn.Parameter(torch.empty(num_classes, hidden_dim))
        nn.init.kaiming_uniform_(self.weight, a=np.sqrt(5))

    def forward_features(self, family_inputs: dict[str, torch.Tensor]) -> tuple[torch.Tensor, dict]:
        B = next(iter(family_inputs.values())).shape[0]
        # Proyectar familias
        proj_list = [self.projections[fam](family_inputs[fam]) for fam in self.family_names]  # list of (B, proj_dim)
        stacked = torch.stack(proj_list, dim=1)  # (B, num_families, proj_dim)

        diag = {}
        if self.fusion_mode == "gating":
            concat_proj = torch.cat(proj_list, dim=-1)
            logits_g = self.gating(concat_proj) / self.temperature
            gates = F.softmax(logits_g, dim=-1)  # (B, num_families)
            diag["gates"] = gates
            gated = torch.cat([proj * gates[:, i : i + 1] for i, proj in enumerate(proj_list)], dim=-1)
            fused = gated

        elif self.fusion_mode == "xattn":
            tokens_out, attn_matrix = self.xattn(stacked)  # (B, num_families, proj_dim), (B, num_fams, num_fams)
            diag["attn_matrix"] = attn_matrix
            fused = tokens_out.reshape(B, -1)

        elif self.fusion_mode == "gated_xattn":
            # Primero Cross-Family Attention
            tokens_out, attn_matrix = self.xattn(stacked)
            diag["attn_matrix"] = attn_matrix
            # Luego compuerta sobre los tokens refinados
            concat_tokens = tokens_out.reshape(B, -1)
            logits_g = self.gating(concat_tokens) / self.temperature
            gates = F.softmax(logits_g, dim=-1)
            diag["gates"] = gates
            gated = torch.cat([tokens_out[:, i] * gates[:, i : i + 1] for i in range(self.num_families)], dim=-1)
            fused = gated

        z = self.refine(fused)
        return z, diag

    def forward(self, family_inputs: dict[str, torch.Tensor]) -> torch.Tensor:
        z, _ = self.forward_features(family_inputs)
        z_norm = F.normalize(z, p=2, dim=-1)
        w_norm = F.normalize(self.weight, p=2, dim=-1)
        return self.scale * F.linear(z_norm, w_norm)


class AdvancedDynaTexClassifier(BaseEstimator, ClassifierMixin):
    def __init__(
        self,
        family_slices: dict[str, tuple[int, int]],
        proj_dim: int = 128,
        hidden_dim: int = 256,
        dropout: float = 0.15,
        temperature: float = 1.0,
        fusion_mode: str = "gating",
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
        self.temperature = temperature
        self.fusion_mode = fusion_mode
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

        self.net_ = AdvancedDynaTexNet(
            family_dims=family_dims,
            num_classes=len(self.classes_),
            proj_dim=self.proj_dim,
            hidden_dim=self.hidden_dim,
            dropout=self.dropout,
            temperature=self.temperature,
            fusion_mode=self.fusion_mode,
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


def evaluate_dataset(dataset_name: str, embedding_root: Path | None = None, manifest_dir: Path | None = None):
    print(f"\n=======================================================")
    print(f" EXPERIMENTO DE VARIANTES ARQUITECTURALES: {dataset_name}")
    print(f"=======================================================")

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

    variants = [
        ("1. DynaTex-Gating (T=1.0)", {"fusion_mode": "gating", "temperature": 1.0, "proj_dim": 128}),
        ("2. DynaTex-Sharpened (T=0.5)", {"fusion_mode": "gating", "temperature": 0.5, "proj_dim": 128}),
        ("3. DynaTex-CrossAttn (Multihead)", {"fusion_mode": "xattn", "temperature": 1.0, "proj_dim": 128}),
        ("4. DynaTex-GatedXAttn (Híbrido)", {"fusion_mode": "gated_xattn", "temperature": 0.5, "proj_dim": 128}),
    ]

    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)

    for label, cfg in variants:
        t0 = time.time()
        f1s, accs = [], []
        for tr, te in sgkf.split(X_full, y, groups):
            clf = AdvancedDynaTexClassifier(
                family_slices=family_slices,
                proj_dim=cfg["proj_dim"],
                temperature=cfg["temperature"],
                fusion_mode=cfg["fusion_mode"],
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
        print(f"{label:35s}: Macro-F1 = {np.mean(f1s):.4f} ± {np.std(f1s):.4f} | Acc = {np.mean(accs):.4f} ({elapsed:.1f}s)")


def main():
    # Evaluamos en FMD (materiales fotográficos)
    evaluate_dataset("FMD")
    # Evaluamos en SoilOriginal (suelos agrícolas)
    evaluate_dataset(
        "SoilOriginal",
        embedding_root=REPO / "embeddings_extensions",
        manifest_dir=REPO / "results/extensions/soil_original",
    )


if __name__ == "__main__":
    main()
