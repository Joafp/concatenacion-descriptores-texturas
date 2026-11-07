#!/usr/bin/env python3
"""HyTexNet (Gupta, Mishra and Shrivastava, Knowl.-Based Syst. 338:115482, 2026), timed.

No code is published, so the method is transcribed from Sections 3.1-3.5 and
the final row of Table 6:

* every image is resized to 128x128 RGB; both streams start from it;
* the HyTex descriptor (514-D) on its grey levels: HyTexS, the 8-neighbour
  sign code of a 3x3 window (Eq. 1-2); HyTexM, the magnitude code |I_p - I_c|
  thresholded at its 75th percentile, the smallest t with at least six of the
  eight magnitudes <= t (Eq. 3-6, which reproduces the T75 column of Table 1);
  HyTexC, whether the centre is at least the image mean (Eq. 7-8); each a
  normalised histogram (256, 256 and 2 bins);
* DenseNet-121 pretrained on ImageNet, global average pooling (1024-D), with
  its last dense block fine-tuned (Table 6, row 4) and the rest frozen;
* the 1538-D concatenation, a 256-unit ReLU layer, dropout 0.5 and softmax,
  trained end-to-end with Adam on the cross-entropy loss.

The paper does not give the learning rate, the batch size, the number of
epochs or any augmentation.  Batch 32 and Keras-style initialisation follow the
Keras vocabulary of Section 3.5; there is no augmentation; the learning rate is
chosen from ``--lrs`` on the validation part of the first split and then fixed;
training stops when validation accuracy has not improved for ``--patience``
epochs and keeps the best epoch.  Validation comes from the protocol:

``DTD``        the official splits: fit on train, stop on validation, test on
               test (the paper averages 10 train/validation/test splits);
``KTHTIPS2b``  the RADAM splits, three physical samples train and one tests,
               which the paper does not use.  The epoch count is found by
               holding out one training sample and the model is refitted on
               all three.  ``--kth-protocol paper`` checks the replica on the
               paper's own protocol instead: two poses, three illuminations and
               six scales of all four samples train (a third of the images)
               and the rest tests.  The paper does not say which, so five
               random draws are made, with 10% of the training images held
               out to stop early.

``--size`` replaces the 128x128 input, only as a sensitivity check; its runs
are written apart (``hytexnet_runs_<size>.csv``).

The HyTex extraction time over every image is added to the dataset's
``extraction_times.json`` as ``hytex``; the DenseNet forward passes belong to
the network and are timed with it.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from PIL import Image
from torch import nn

SRC = Path(__file__).resolve().parent
REPO = SRC.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from benchmark_kth_methods import scores, sync  # noqa: E402
from time_extraction import DATASETS, image_path, read_images, stored_sha256  # noqa: E402

SIZE = 128
# Clockwise from the top-left neighbour; the order only permutes histogram bins.
OFFSETS = ((-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1))
WEIGHTS = (1 << np.arange(8)).reshape(8, 1, 1)
MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)


def hytex(gray: np.ndarray) -> np.ndarray:
    g = gray.astype(np.int16)
    h, w = g.shape
    centre = g[1:-1, 1:-1]
    neighbours = np.stack([g[1 + dy:h - 1 + dy, 1 + dx:w - 1 + dx] for dy, dx in OFFSETS])
    sign = ((neighbours >= centre) * WEIGHTS).sum(0)
    magnitude = np.abs(neighbours - centre)
    t75 = np.sort(magnitude, axis=0)[5]
    mag_code = ((magnitude >= t75) * WEIGHTS).sum(0)
    bright = (centre >= g.mean()).astype(np.int64)
    n = centre.size
    return np.concatenate([np.bincount(sign.ravel(), minlength=256) / n,
                           np.bincount(mag_code.ravel(), minlength=256) / n,
                           np.bincount(bright.ravel(), minlength=2) / n]).astype(np.float32)


def prepare(images, size=SIZE):
    """Resize to size x size and compute HyTex: the per-image work before the network."""
    t0 = time.perf_counter()
    small, hist = [], []
    for rgb in images:
        img = Image.fromarray(rgb).resize((size, size), Image.BILINEAR)
        small.append(np.asarray(img))
        hist.append(hytex(np.asarray(img.convert("L"))))
    return np.stack(small), np.stack(hist), time.perf_counter() - t0


class HyTexNet(nn.Module):
    TUNED = ("denseblock4", "norm5")

    def __init__(self, n_classes: int):
        super().__init__()
        from torchvision.models import DenseNet121_Weights, densenet121
        self.features = densenet121(weights=DenseNet121_Weights.IMAGENET1K_V1).features
        for name, module in self.features.named_children():
            for p in module.parameters():
                p.requires_grad = name in self.TUNED
        self.head = nn.Sequential(nn.Linear(1024 + 514, 256), nn.ReLU(), nn.Dropout(0.5),
                                  nn.Linear(256, n_classes))
        for layer in self.head:
            if isinstance(layer, nn.Linear):  # Keras Dense defaults
                nn.init.xavier_uniform_(layer.weight)
                nn.init.zeros_(layer.bias)

    def train(self, mode: bool = True):
        super().train(mode)
        # Frozen layers keep their ImageNet statistics, as frozen Keras layers do.
        for name, module in self.features.named_children():
            if name not in self.TUNED:
                module.eval()
        return self

    def forward(self, x, h):
        f = F.adaptive_avg_pool2d(F.relu(self.features(x)), 1).flatten(1)
        return self.head(torch.cat([f, h], dim=1))


def batches(n, size, generator=None):
    order = torch.randperm(n, generator=generator) if generator is not None else torch.arange(n)
    return [order[i:i + size] for i in range(0, n, size)]


def predict(model, x, h, idx):
    model.eval()
    out = []
    with torch.inference_mode():
        for b in batches(len(idx), 128):
            j = idx[b.to(idx.device)]
            out.append(model((x[j].float() / 255 - MEAN) / STD, h[j]).argmax(1).cpu())
    return torch.cat(out).numpy()


def fit(x, h, y, train, n_classes, lr, seed, batch_size, epochs, val=None, patience=0):
    """Train; with ``val``, stop early and return the best epoch's weights."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = HyTexNet(n_classes).to(x.device)
    optimizer = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=lr)
    gen = torch.Generator().manual_seed(seed)
    tr = torch.as_tensor(train, device=x.device)
    best, best_epoch, best_state = -1.0, 0, None
    for epoch in range(1, epochs + 1):
        model.train()
        for b in batches(len(tr), batch_size, gen):
            j = tr[b.to(x.device)]
            optimizer.zero_grad(set_to_none=True)
            F.cross_entropy(model((x[j].float() / 255 - MEAN) / STD, h[j]), y[j]).backward()
            optimizer.step()
        if val is None:
            continue
        acc = float((predict(model, x, h, torch.as_tensor(val, device=x.device))
                     == y[val].cpu().numpy()).mean())
        if acc > best:
            best, best_epoch, best_state = acc, epoch, copy.deepcopy(model.state_dict())
        elif epoch - best_epoch >= patience:
            break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model, best_epoch or epochs, best


def kth_conditions(rows):
    """Pose, illumination and scale of each KTH-TIPS2 image (its Table 5 labelling)."""
    import re
    out = []
    for r in rows:
        scale, image = map(int, re.search(r"scale_(\d+)_im_(\d+)", r["source_path"]).groups())
        # Images 1-9: three poses (rows) by three lamp directions (columns);
        # 10-12: the three poses under ambient light.
        pose, light = ((image - 1) // 3, (image - 1) % 3) if image <= 9 else (image - 10, 3)
        out.append((pose, light, scale))
    return np.asarray(out)


def splits(dataset, rows, kth_protocol="radam"):
    """(label, train, validation, test, refit) per split; refit marks KTH's inner run."""
    groups = np.asarray([r["group"] for r in rows])
    if dataset == "KTHTIPS2b" and kth_protocol == "paper":
        from sklearn.model_selection import train_test_split
        cond = kth_conditions(rows)
        labels = np.asarray([r["label"] for r in rows])
        for draw in range(1, 6):
            rng = np.random.default_rng(draw)
            poses, lights = rng.choice(3, 2, replace=False), rng.choice(4, 3, replace=False)
            scales = rng.choice(np.arange(2, 11), 6, replace=False)
            chosen = (np.isin(cond[:, 0], poses) & np.isin(cond[:, 1], lights)
                      & np.isin(cond[:, 2], scales))
            train, val = train_test_split(np.flatnonzero(chosen), test_size=0.1,
                                          stratify=labels[chosen], random_state=draw)
            yield f"p{draw}", train, val, np.flatnonzero(~chosen), False
        return
    if dataset == "DTD":
        for s in range(1, 11):
            roles = np.asarray([r[f"split_{s}"] for r in rows])
            test = np.flatnonzero(roles == "test")
            clean = ~np.isin(groups, groups[test])  # byte-identical copies of test images
            yield (str(s), np.flatnonzero((roles == "train") & clean),
                   np.flatnonzero((roles == "val") & clean), test, False)
    else:
        samples = np.asarray([r["sample"] for r in rows])
        for s in range(1, 5):
            roles = np.asarray([r[f"split_{s}"] for r in rows])
            # RADAM: the official training sample becomes the test sample.
            train, test = np.flatnonzero(roles == "test"), np.flatnonzero(roles == "train")
            held = sorted(set(samples[train]))[0]
            yield (str(s), train[samples[train] != held], train[samples[train] == held], test, True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", choices=("DTD", "KTHTIPS2b"), required=True)
    parser.add_argument("--lrs", type=float, nargs="+", default=[1e-3, 1e-4])
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-epochs", type=int, default=50)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--kth-protocol", choices=("radam", "paper"), default="radam")
    parser.add_argument("--size", type=int, default=SIZE,
                        help="input side; the paper uses 128, other values are a sensitivity check")
    parser.add_argument("--splits", nargs="+", help="default: every split")
    parser.add_argument("--output", type=Path, help="default: results/exploratory/sota_timing/<dataset>")
    args = parser.parse_args()
    manifest, _, slug = DATASETS[args.dataset]
    output = args.output or REPO / "results/exploratory/sota_timing" / slug
    output.mkdir(parents=True, exist_ok=True)
    paper = args.dataset == "KTHTIPS2b" and args.kth_protocol == "paper"
    suffix = ("_paper_protocol" if paper else "") + (f"_{args.size}" if args.size != SIZE else "")
    block = "hytex" if args.size == SIZE else f"hytex_{args.size}"
    device = torch.device("cuda")

    with (REPO / manifest).open(newline="", encoding="utf-8") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: int(r["row_id"]))
    _, labels = np.unique([r["label"] for r in rows], return_inverse=True)
    n_classes = int(labels.max()) + 1
    images, read_s, decode_s = read_images([image_path(r, None) for r in rows],
                                           [stored_sha256(r) for r in rows])
    small, hist, prep_s = prepare(images, args.size)
    del images
    print(f"leer {read_s:.1f} s, decodificar {decode_s:.1f} s, {args.size}x{args.size} + HyTex {prep_s:.1f} s", flush=True)
    times_path = output / "extraction_times.json"
    times = json.loads(times_path.read_text()) if times_path.exists() else {}
    times[block] = {"images": len(rows), "device": "cpu x1", "load_seconds": 0.0,
                      "extract_seconds": prep_s, "ms_per_image": 1000 * prep_s / len(rows),
                      "images_per_second": len(rows) / prep_s, "dimensions": 514,
                      "matches_stored": None,
                      "note": f"resize to {args.size}x{args.size} and HyTex histograms; DenseNet is timed in the network"}
    times_path.write_text(json.dumps(times, indent=2) + "\n", encoding="utf-8")

    x = torch.from_numpy(small).permute(0, 3, 1, 2).contiguous().to(device)
    h = torch.from_numpy(hist).to(device)
    y = torch.from_numpy(labels).long().to(device)
    global MEAN, STD
    MEAN, STD = MEAN.to(device), STD.to(device)
    torch.backends.cudnn.benchmark = False
    plan = list(splits(args.dataset, rows, args.kth_protocol))
    if args.splits:
        plan = [p for p in plan if p[0] in args.splits]

    # Learning rate: validation accuracy on the first split, then fixed.
    choice = {}
    t0 = time.perf_counter()
    _, train, val, _, _ = plan[0]
    for lr in args.lrs:
        _, epoch, acc = fit(x, h, y, train, n_classes, lr, 42, args.batch_size, args.max_epochs,
                            val, args.patience)
        choice[lr] = (acc, epoch)
        print(f"lr {lr:g}: validación {acc:.4f} en la época {epoch}", flush=True)
    lr = max(choice, key=lambda k: choice[k][0])
    lr_s = time.perf_counter() - t0
    (output / f"hytexnet_lr_choice{suffix}.json").write_text(json.dumps(
        {"chosen": lr, "seconds": lr_s, "split": plan[0][0],
         "validation": {f"{k:g}": {"accuracy": a, "best_epoch": e} for k, (a, e) in choice.items()}},
        indent=2) + "\n", encoding="utf-8")

    records = []
    for split, train, val, test, refit in plan:
        sync()
        t0 = time.perf_counter()
        model, epoch, val_acc = fit(x, h, y, train, n_classes, lr, 42, args.batch_size,
                                    args.max_epochs, val, args.patience)
        sync()
        select_s = time.perf_counter() - t0
        fit_s = 0.0
        if refit:  # KTH: refit on the three training samples for the chosen epochs
            del model
            full = np.concatenate([train, val])
            t0 = time.perf_counter()
            model, _, _ = fit(x, h, y, full, n_classes, lr, 42, args.batch_size, epoch)
            sync()
            fit_s = time.perf_counter() - t0
            train = full
        else:
            select_s, fit_s = 0.0, select_s
        t0 = time.perf_counter()
        pred = predict(model, x, h, torch.as_tensor(test, device=device))
        sync()
        predict_s = time.perf_counter() - t0
        del model
        torch.cuda.empty_cache()
        records.append({"split": split, "method": "hytexnet", "classifier": "mlp", "blocks": block,
                        **scores(labels[test], pred), "selection_seconds": select_s,
                        "fit_seconds": fit_s, "train_seconds": select_s + fit_s,
                        "predict_seconds": predict_s, "models": 1, "dimensions": 1538,
                        "n_train": len(train), "n_test": len(test), "lr": lr, "epochs": epoch,
                        "val_accuracy": val_acc})
        r = records[-1]
        print(f"split {split}: acc {r['accuracy']:.4f}  épocas {epoch}  entrenar "
              f"{r['train_seconds']:.1f} s  predecir {predict_s:.2f} s", flush=True)
        pd.DataFrame(records).to_csv(output / f"hytexnet_runs{suffix}.csv", index=False)
    frame = pd.DataFrame(records)
    print(f"media {frame.accuracy.mean():.4f} ± {frame.accuracy.std():.4f}")


if __name__ == "__main__":
    main()
