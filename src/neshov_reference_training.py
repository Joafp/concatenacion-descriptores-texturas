"""Fixed, fit-only MLP training and producer-fold checks for the reference pilot."""
import numpy as np
import torch
from torch import nn
from neshov_beit_reference import ReferenceMLP


def validate_partition_panel(folds):
    """Require one complete producer OOF pass with complementary fit sets."""
    validations = [int(i) for f in folds for i in f["validation_indices"]]
    if len(validations) != len(set(validations)):
        raise ValueError("producer validation images repeat")
    universe = set(validations)
    for f in folds:
        fit, val = set(f["fit_indices"]), set(f["validation_indices"])
        if fit & val or fit | val != universe:
            raise ValueError("producer folds overlap or do not cover the same development set")
        if len(fit) != len(f["fit_indices"]) or len(val) != len(f["validation_indices"]):
            raise ValueError("repeated fit/validation indices")
    return np.asarray(sorted(universe), dtype=np.int64)


def fit_fixed_head(x_fit, y_fit, n_classes, *, epochs=100, batch_size=32, seed=42):
    """No validation arguments or epoch selection. Return the final epoch's head."""
    x_fit = torch.as_tensor(np.asarray(x_fit), dtype=torch.float32)
    y_fit = torch.as_tensor(np.asarray(y_fit), dtype=torch.long)
    if x_fit.ndim != 2 or len(x_fit) != len(y_fit) or len(x_fit) < 2:
        raise ValueError("aligned training matrix with at least two rows required")
    if epochs < 1 or batch_size < 2 or len(x_fit) % batch_size == 1:
        raise ValueError("positive epochs and no singleton BatchNorm batch required")
    if not torch.isfinite(x_fit).all() or y_fit.min() < 0 or y_fit.max() >= n_classes:
        raise ValueError("invalid training features or labels")
    torch.manual_seed(seed)
    head = ReferenceMLP(x_fit.shape[1], n_classes)
    generator = torch.Generator().manual_seed(seed)
    optimizer = torch.optim.Adam(head.parameters(), lr=1e-3, weight_decay=1e-4,
                                 betas=(.9, .999))
    loss_fn, history = nn.CrossEntropyLoss(), []
    for epoch in range(epochs):
        head.train()
        order = torch.randperm(len(x_fit), generator=generator)
        total = 0.
        for start in range(0, len(order), batch_size):
            ids = order[start:start + batch_size]
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(head(x_fit[ids]), y_fit[ids])
            if not torch.isfinite(loss):
                raise ValueError("non-finite training loss")
            loss.backward()
            optimizer.step()
            total += float(loss.detach()) * len(ids)
        history.append({"epoch": epoch + 1, "fit_cross_entropy": total / len(x_fit)})
    head.eval()
    return head, history
