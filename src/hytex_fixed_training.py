"""Explicit LOCAL training choices from PROTOCOLO_HYTEX_ADAPTACION_FMD, not source defaults."""
import numpy as np
import torch
from hytex_reference import HyTexFusionHead


def fit_head(features, labels, n_classes, *, epochs=100):
    x = torch.as_tensor(np.asarray(features), dtype=torch.float32)
    y = torch.as_tensor(np.asarray(labels), dtype=torch.long)
    if (x.ndim != 2 or x.shape[1] != 1538 or len(x) != len(y) or len(y) < 2
            or not torch.isfinite(x).all() or y.ndim != 1
            or set(y.tolist()) != set(range(n_classes)) or epochs < 1):
        raise ValueError('aligned finite HyTex1538 training data with all classes required')
    torch.manual_seed(42)
    head = HyTexFusionHead(n_classes).cpu()
    generator = torch.Generator().manual_seed(42)
    optimizer = torch.optim.Adam(head.parameters(), lr=.001, betas=(.9, .999), weight_decay=.0001)
    criterion = torch.nn.CrossEntropyLoss()
    history = []
    for epoch in range(epochs):
        head.train()
        order = torch.randperm(len(x), generator=generator)
        total = 0.
        for start in range(0, len(x), 32):
            ids = order[start:start + 32]
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(head(x[ids]), y[ids])
            if not torch.isfinite(loss):
                raise ValueError('nonfinite fit loss')
            loss.backward()
            optimizer.step()
            total += float(loss.detach()) * len(ids)
        history.append({'epoch': epoch + 1, 'fit_cross_entropy': total / len(x)})
        if epoch % 10 == 0:
            print(f'head epoch {epoch + 1}/{epochs}', flush=True)
    return head.eval(), history
