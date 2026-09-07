"""
ResMLP-style classifier (Touvron et al. 2021) para embeddings pre-extraídos.
Implementación con PyTorch, wrap en API sklearn-compatible (fit/predict).

Arquitectura:
- Proyección inicial: Linear(emb_dim, hidden_dim) + LayerNorm + GELU
- N bloques residuales: Linear -> GELU -> Dropout, con skip connection
- Cabeza de clasificación: Linear(hidden_dim, num_classes)
"""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.base import BaseEstimator, ClassifierMixin


class _ResMLPBlock(nn.Module):
    """Bloque residual: x + Dropout(Linear(GELU(Linear(LayerNorm(x)))))"""

    def __init__(self, dim: int, dropout: float = 0.1):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.fc1 = nn.Linear(dim, dim)
        self.fc2 = nn.Linear(dim, dim)
        self.drop = nn.Dropout(dropout)
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.norm(x)
        h = self.fc1(h)
        h = self.act(h)
        h = self.drop(h)
        h = self.fc2(h)
        h = self.drop(h)
        return x + h


class _ResMLPNet(nn.Module):
    """Red ResMLP completa."""

    def __init__(self, in_dim: int, num_classes: int, hidden_dim: int = 256, n_blocks: int = 3, dropout: float = 0.1):
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.blocks = nn.Sequential(*[_ResMLPBlock(hidden_dim, dropout) for _ in range(n_blocks)])
        self.norm_out = nn.LayerNorm(hidden_dim)
        self.head = nn.Linear(hidden_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.proj(x)
        x = self.blocks(x)
        x = self.norm_out(x)
        return self.head(x)


class ResMLPClassifier(BaseEstimator, ClassifierMixin):
    """ResMLP-style classifier sklearn-compatible para embeddings."""

    def __init__(
        self,
        hidden_dim: int = 256,
        n_blocks: int = 3,
        dropout: float = 0.1,
        lr: float = 1e-3,
        weight_decay: float = 1e-4,
        max_epochs: int = 100,
        batch_size: int = 256,
        patience: int = 10,
        random_state: int = 42,
        device: str | None = None,
    ):
        self.hidden_dim = hidden_dim
        self.n_blocks = n_blocks
        self.dropout = dropout
        self.lr = lr
        self.weight_decay = weight_decay
        self.max_epochs = max_epochs
        self.batch_size = batch_size
        self.patience = patience
        self.random_state = random_state
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def fit(self, X, y):
        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)

        self.classes_ = np.unique(y)
        num_classes = len(self.classes_)
        in_dim = X.shape[1]

        X_t = torch.tensor(X, dtype=torch.float32, device=self.device)
        y_t = torch.tensor(y, dtype=torch.long, device=self.device)

        self.net_ = _ResMLPNet(in_dim, num_classes, self.hidden_dim, self.n_blocks, self.dropout).to(self.device)
        opt = torch.optim.AdamW(self.net_.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        crit = nn.CrossEntropyLoss()

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
                logits = self.net_(X_t[idx])
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

    def predict(self, X):
        self.net_.eval()
        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32, device=self.device)
            logits = self.net_(X_t)
            preds = logits.argmax(dim=1).cpu().numpy()
        return self.classes_[preds]

    def predict_proba(self, X):
        self.net_.eval()
        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32, device=self.device)
            logits = self.net_(X_t)
            probs = F.softmax(logits, dim=1).cpu().numpy()
        return probs