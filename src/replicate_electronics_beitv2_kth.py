#!/usr/bin/env python3
"""Closest executable replication of Electronics 2025 BEiTv2 KTH classifier.

Fixed components transcribed from Sections 3.1, 4.2, 4.4 and 4.5: frozen
BEiTv2 descriptors, MLP 64 -> BatchNorm -> ReLU -> Dropout(.2) -> classes,
Adam lr 1e-3 / beta1 .9 / wd 1e-4, batch 32, 100 epochs, seed 42.
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from run_confirmatory_nested import audit_gate, load_dataset, load_manifest, official_split_indices


class PaperMLP(nn.Module):
    def __init__(self, dimensions: int, n_classes: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(dimensions, 64), nn.BatchNorm1d(64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, n_classes),
        )

    def forward(self, x):
        return self.layers(x)


def deterministic(seed: int) -> None:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--descriptor", choices=("beitv2_base_final", "beitv2_base_multilayer"), required=True)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--embedding-root", type=Path, default=Path("embeddings_extensions"))
    parser.add_argument("--output", type=Path,
                        default=Path("results/extensions/kth_tips2b/beitv2_electronics_replica_radam_3train_raw"))
    args = parser.parse_args()
    repo = args.repo.resolve()
    root = args.embedding_root if args.embedding_root.is_absolute() else repo / args.embedding_root
    output = args.output if args.output.is_absolute() else repo / args.output
    audit_gate(repo / "results/extensions/kth_tips2b", "KTHTIPS2b")
    cache, y = load_dataset(repo, "KTH-TIPS2-b", root)
    groups, rows = load_manifest(repo / "results/extensions/kth_tips2b", "KTHTIPS2b", y)
    # The common thesis loader L2-normalizes each descriptor. Electronics does
    # not report that operation: it feeds raw GAP features to a BatchNorm MLP.
    raw_path = root / "KTH-TIPS2-b" / f"{args.descriptor}.npy"
    x = np.load(raw_path, allow_pickle=False).astype(np.float32, copy=False)
    if x.ndim != 2 or len(x) != len(y) or not np.isfinite(x).all():
        raise ValueError(f"invalid raw descriptor: {raw_path}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    records = []
    for split in range(1, 5):
        deterministic(42)
        # Our manifest records the conservative 1-train/3-test orientation.
        # RADAM's PredefinedSplit uses the held-out sample as test, hence the
        # exact inverse: three physical samples train and one sample tests.
        manifest_train, manifest_test = official_split_indices(rows, split)
        train, test = manifest_test, manifest_train
        if set(groups[train]).intersection(groups[test]):
            raise AssertionError("outer group leakage")
        train_x = torch.from_numpy(x[train]); train_y = torch.from_numpy(y[train]).long()
        generator = torch.Generator().manual_seed(42)
        loader = DataLoader(TensorDataset(train_x, train_y), batch_size=32, shuffle=True,
                            generator=generator, num_workers=0)
        model = PaperMLP(x.shape[1], len(np.unique(y))).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, betas=(.9, .999), weight_decay=1e-4)
        loss_fn = nn.CrossEntropyLoss()
        model.train()
        for _ in range(100):
            for batch_x, batch_y in loader:
                optimizer.zero_grad(set_to_none=True)
                loss = loss_fn(model(batch_x.to(device)), batch_y.to(device))
                loss.backward(); optimizer.step()
        model.eval()
        with torch.inference_mode():
            prediction = model(torch.from_numpy(x[test]).to(device)).argmax(dim=1).cpu().numpy()
        record = {
            "dataset": "KTHTIPS2b", "split": split, "descriptor": args.descriptor,
            "macro_f1": float(f1_score(y[test], prediction, average="macro")),
            "accuracy": float(accuracy_score(y[test], prediction)), "train_rows": len(train),
            "test_rows": len(test), "protocol": "radam_predefined_split_3train_1test",
            "feature_normalization": "raw_gap_no_l2", "seed": 42, "epochs": 100, "batch_size": 32,
            "hidden_units": 64, "dropout": .2, "learning_rate": 1e-3, "weight_decay": 1e-4,
        }
        records.append(record)
        print(record, flush=True)
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{args.descriptor}.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=records[0].keys())
        writer.writeheader(); writer.writerows(records)
    print({"descriptor": args.descriptor, "accuracy_mean": float(np.mean([r["accuracy"] for r in records])),
           "accuracy_std": float(np.std([r["accuracy"] for r in records], ddof=1))})


if __name__ == "__main__":
    main()
