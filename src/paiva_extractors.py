"""
paiva_extractors.py
===================
Descriptores de Paiva et al. 2023 no cubiertos en la biblioteca de 20.

Implementa fiel a Tabla 3 de Paiva (docs/2023_7_rgb_pixel_ngrams.pdf:7):
  - EHD (Edge Histogram Descriptor) — 80 dims, 16 sub-imágenes 4×4 × 5 tipos de borde
  - DCD (Dominant Color Descriptor) — k=4 en CIE-Luv, random_state=10
  - CLD (Color Layout Descriptor) — DCT sobre layout 8×8 (sin parámetros, compacto)
  - G-E / G-V (Granulometría) — structuring element sizes {0..15}
  - MC-V (Morphological Covariance Volume) — distancias {1,5,9,13}, orientaciones {0,45,90,135}
  - BoVW-S / BoVW-P — k-Means k=50, random_state=1 (SIFT / patches)

Fase 1: EHD, DCD, CLD (más fáciles). Fase 2: G-E/G-V/MC-V y BoVW.

Cada clase sigue el contrato de ClassicalExtractor: __init__(cfg) + extract(image_paths).
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _load_rgb(path: str, image_size: int) -> np.ndarray:
    """Carga RGB redimensionada a image_size×image_size, uint8."""
    img = Image.open(path).convert("RGB")
    img = img.resize((image_size, image_size), Image.BILINEAR)
    return np.array(img, dtype=np.uint8)


def _load_gray(path: str, image_size: int) -> np.ndarray:
    from skimage.color import rgb2gray
    rgb = _load_rgb(path, image_size)
    gray = rgb2gray(rgb)
    return (gray * 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# EHD — Edge Histogram Descriptor (80 dims)
# ---------------------------------------------------------------------------

class EHDExtractor:
    """EHD MPEG-7 simplificado pero fiel en dimensionalidad.

    - 4×4 = 16 sub-imágenes
    - Por sub-imagen, 5 bins: vertical, horizontal, 45°, 135°, no-direccional
    - Implementación: Sobel gx/gy por bloque, luego histograma por orientación.
    """

    def __init__(self, cfg: dict):
        self.image_size = cfg.get("image_size", 256)
        # thresholds
        self.edge_thresh = cfg.get("edge_thresh", 30)  # magnitud mínima para considerar borde
        self.angle_bins = {
            "vertical": (-22.5, 22.5),      # + 180 ±22.5
            "horizontal": (67.5, 112.5),
            "diag45": (22.5, 67.5),
            "diag135": (112.5, 157.5),
        }

    def _ehd_single(self, gray: np.ndarray) -> np.ndarray:
        from scipy.ndimage import sobel
        # Sobel en x e y
        gx = sobel(gray.astype(np.float32), axis=1, mode="reflect")
        gy = sobel(gray.astype(np.float32), axis=0, mode="reflect")
        magnitude = np.hypot(gx, gy)
        angle = np.degrees(np.arctan2(gy, gx)) % 180  # 0-180

        h, w = gray.shape
        sub_h, sub_w = h // 4, w // 4
        hist = np.zeros(80, dtype=np.float32)

        for si in range(4):
            for sj in range(4):
                r0, r1 = si * sub_h, (si + 1) * sub_h
                c0, c1 = sj * sub_w, (sj + 1) * sub_w
                mag_block = magnitude[r0:r1, c0:c1]
                ang_block = angle[r0:r1, c0:c1]

                # máscara de borde
                edge_mask = mag_block > self.edge_thresh
                if not np.any(edge_mask):
                    continue
                angs = ang_block[edge_mask]

                # Clasificar por orientación
                counts = np.zeros(5, dtype=np.float32)
                # vertical: [0,22.5) U [157.5,180)
                counts[0] = np.sum(((angs >= 0) & (angs < 22.5)) | (angs >= 157.5))
                counts[1] = np.sum((angs >= 67.5) & (angs < 112.5))  # horizontal
                counts[2] = np.sum((angs >= 22.5) & (angs < 67.5))   # 45°
                counts[3] = np.sum((angs >= 112.5) & (angs < 157.5)) # 135°
                # no-direccional: se estima como isotrópico cuando la varianza de ángulo es alta
                # simplificación: lo que no cae claro en los 4 anteriores ya está contado;
                # para no-direccional usamos pixeles con magnitud alta pero baja coherencia -> aproximamos como resto
                # En MPEG-7 el 5to bin es no-direccional; aquí lo derivamos como complemento normalizado
                # Si sum != total, la diferencia va a no-direccional
                total = counts[:4].sum()
                remainder = max(0, edge_mask.sum() - total)
                # heurística: parte del remainder + 10% de los bordes ambiguos
                counts[4] = remainder + 0.1 * total

                # normalizar por área del bloque (densidad)
                counts /= max(1, sub_h * sub_w)
                idx = (si * 4 + sj) * 5
                hist[idx:idx + 5] = counts

        # L2-normalizar final para compatibilidad con el pipeline
        n = np.linalg.norm(hist)
        if n > 1e-9:
            hist /= n
        return hist

    def extract(self, image_paths: list[str], batch_size: int = 16) -> np.ndarray:
        from joblib import Parallel, delayed
        import os
        n_jobs = max(1, min(8, (os.cpu_count() or 4) - 1))

        def _one(p):
            g = _load_gray(p, self.image_size)
            return self._ehd_single(g)

        t0 = time.time()
        feats = Parallel(n_jobs=n_jobs, verbose=0)(delayed(_one)(p) for p in image_paths)
        elapsed = time.time() - t0
        print(f"  [paiva/ehd] {len(image_paths)}/{len(image_paths)} ({elapsed:.1f}s, n_jobs={n_jobs})")
        return np.stack(feats, axis=0)


# ---------------------------------------------------------------------------
# DCD — Dominant Color Descriptor (16 dims: 4 colores × Luv(3) + 4 pesos)
# ---------------------------------------------------------------------------

class DCDExtractor:
    """DCD según Paiva Tabla 3: k-Means k=4, random_state=10 tras RGB→CIE-Luv."""

    def __init__(self, cfg: dict):
        self.image_size = cfg.get("image_size", 128)
        self.k = cfg.get("k", 4)
        self.random_state = cfg.get("random_state", 10)

    def _dcd_single(self, rgb: np.ndarray) -> np.ndarray:
        from skimage.color import rgb2luv
        from sklearn.cluster import KMeans
        # rgb uint8 -> Luv (requiere float 0-1)
        luv = rgb2luv(rgb.astype(np.float32) / 255.0)  # shape H×W×3
        pixels = luv.reshape(-1, 3)
        # submuestrear para k-means si imagen grande (acelera sin perder mucho)
        if len(pixels) > 4096:
            rng = np.random.default_rng(self.random_state)
            idx = rng.choice(len(pixels), 4096, replace=False)
            sample = pixels[idx]
        else:
            sample = pixels
        kmeans = KMeans(n_clusters=self.k, random_state=self.random_state, n_init=10)
        kmeans.fit(sample)
        labels = kmeans.predict(pixels)
        # porcentaje por cluster
        counts = np.bincount(labels, minlength=self.k).astype(np.float32)
        counts /= counts.sum()
        # ordenar por porcentaje descendente (dominancia)
        order = np.argsort(-counts)
        centers = kmeans.cluster_centers_[order]  # 4×3
        weights = counts[order]  # 4
        # feature: 12 centros aplanados + 4 pesos = 16
        feat = np.concatenate([centers.flatten(), weights])
        # normalizar Luv centros por rango aprox para que no domine escala
        # L in [0,100], u/v in [-100,100] -> dividir por 100
        feat[:12] /= 100.0
        return feat.astype(np.float32)

    def extract(self, image_paths: list[str], batch_size: int = 16) -> np.ndarray:
        from joblib import Parallel, delayed
        import os
        n_jobs = max(1, min(8, (os.cpu_count() or 4) - 1))

        def _one(p):
            rgb = _load_rgb(p, self.image_size)
            return self._dcd_single(rgb)

        t0 = time.time()
        feats = Parallel(n_jobs=n_jobs, verbose=0)(delayed(_one)(p) for p in image_paths)
        elapsed = time.time() - t0
        print(f"  [paiva/dcd] {len(image_paths)}/{len(image_paths)} ({elapsed:.1f}s, n_jobs={n_jobs})")
        return np.stack(feats, axis=0)


# ---------------------------------------------------------------------------
# CLD — Color Layout Descriptor (33 dims: Y 18 + Cb 7 + Cr 8 aprox, simplificado a 36)
# ---------------------------------------------------------------------------

class CLDExtractor:
    """CLD MPEG-7 simplificado.

    - Divide en 8×8 =64 bloques, promedio de color por bloque
    - Convierte a YCbCr, aplica DCT 2D por canal y toma coeficientes zigzag
    """

    def __init__(self, cfg: dict):
        self.image_size = cfg.get("image_size", 128)
        # cuántos coeffs guardar por canal (zigzag)
        self.n_y = cfg.get("n_y", 18)
        self.n_cb = cfg.get("n_cb", 9)
        self.n_cr = cfg.get("n_cr", 9)

    def _cld_single(self, rgb: np.ndarray) -> np.ndarray:
        from scipy.fft import dct
        # 8×8 block average
        h, w, _ = rgb.shape
        bh, bw = h // 8, w // 8
        # average per block using vectorized mean
        small = rgb.reshape(8, bh, 8, bw, 3).mean(axis=(1, 3))  # 8×8×3
        # RGB -> YCbCr (ITU-R BT.601)
        r, g, b = small[:, :, 0].astype(np.float32), small[:, :, 1].astype(np.float32), small[:, :, 2].astype(np.float32)
        y  = 0.299 * r + 0.587 * g + 0.114 * b
        cb = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b
        cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b
        # DCT 2D por canal
        def dct2(x):
            return dct(dct(x, axis=0, norm="ortho"), axis=1, norm="ortho")

        y_dct  = dct2(y)
        cb_dct = dct2(cb)
        cr_dct = dct2(cr)

        # zigzag order 8×8
        zigzag = [
            (0,0),(0,1),(1,0),(2,0),(1,1),(0,2),(0,3),(1,2),
            (2,1),(3,0),(4,0),(3,1),(2,2),(1,3),(0,4),(0,5),
            (1,4),(2,3),(3,2),(4,1),(5,0),(6,0),(5,1),(4,2),
            (3,3),(2,4),(1,5),(0,6),(0,7),(1,6),(2,5),(3,4),
            (4,3),(5,2),(6,1),(7,0),(7,1),(6,2),(5,3),(4,4),
            (3,5),(2,6),(1,7),(2,7),(3,6),(4,5),(5,4),(6,3),
            (7,2),(7,3),(6,4),(5,5),(4,6),(3,7),(4,7),(5,6),
            (6,5),(7,4),(7,5),(6,6),(5,7),(6,7),(7,6),(7,7),
        ]
        def zigzag_take(dct_mat, n):
            return np.array([dct_mat[i, j] for i, j in zigzag[:n]], dtype=np.float32)

        y_feat  = zigzag_take(y_dct, self.n_y)
        cb_feat = zigzag_take(cb_dct, self.n_cb)
        cr_feat = zigzag_take(cr_dct, self.n_cr)
        feat = np.concatenate([y_feat, cb_feat, cr_feat])
        # cuantización simple: dividir por 100 para rango
        feat /= 100.0
        return feat

    def extract(self, image_paths: list[str], batch_size: int = 16) -> np.ndarray:
        from joblib import Parallel, delayed
        import os
        n_jobs = max(1, min(8, (os.cpu_count() or 4) - 1))

        def _one(p):
            rgb = _load_rgb(p, self.image_size)
            return self._cld_single(rgb)

        t0 = time.time()
        feats = Parallel(n_jobs=n_jobs, verbose=0)(delayed(_one)(p) for p in image_paths)
        elapsed = time.time() - t0
        print(f"  [paiva/cld] {len(image_paths)}/{len(image_paths)} ({elapsed:.1f}s, n_jobs={n_jobs})")
        return np.stack(feats, axis=0)


# ---------------------------------------------------------------------------
# BoVW-S / BoVW-P — Bag of Visual Words (k-Means k=50, random_state=1)
# ---------------------------------------------------------------------------

class BoVWExtractor:
    """BoVW genérico. mode='sift' -> BoVW-S, mode='patch' -> BoVW-P.

    Simplificación respecto a Paiva: vocabulario se construye con k-means
    sobre descriptores de todas las imágenes provistas (muestra de 20000),
    no por fold. Para la tesis, la comparabilidad relativa se mantiene;
    se documenta como aproximación.
    """

    def __init__(self, cfg: dict):
        self.image_size = cfg.get("image_size", 128)
        self.k = cfg.get("k", 50)
        self.random_state = cfg.get("random_state", 1)
        self.mode = cfg.get("mode", "sift")  # sift o patch
        self.patch_size = cfg.get("patch_size", 16)
        self.n_patches = cfg.get("n_patches", 64)  # patches por imagen para BoVW-P
        self._codebook = None
        self._kmeans = None

    def _sift_descriptors(self, gray: np.ndarray) -> np.ndarray:
        import cv2
        sift = cv2.SIFT_create()
        kps, des = sift.detectAndCompute(gray, None)
        if des is None or len(des) == 0:
            return np.zeros((0, 128), dtype=np.float32)
        return des.astype(np.float32)

    def _patch_descriptors(self, gray: np.ndarray) -> np.ndarray:
        # Muestreo denso de patches y descriptor = patch aplanado normalizado
        h, w = gray.shape
        ps = self.patch_size
        # grid de n_patches posiciones
        n_side = int(np.sqrt(self.n_patches))
        ys = np.linspace(0, h - ps, n_side, dtype=int)
        xs = np.linspace(0, w - ps, n_side, dtype=int)
        descs = []
        for y in ys:
            for x in xs:
                p = gray[y:y+ps, x:x+ps].astype(np.float32).flatten()
                p = (p - p.mean()) / (p.std() + 1e-6)  # normalizado
                descs.append(p)
        return np.stack(descs, axis=0) if descs else np.zeros((0, ps*ps), dtype=np.float32)

    def _build_codebook(self, all_descriptors: np.ndarray):
        from sklearn.cluster import KMeans
        # submuestrear si demasiados
        if len(all_descriptors) > 20000:
            rng = np.random.default_rng(self.random_state)
            idx = rng.choice(len(all_descriptors), 20000, replace=False)
            sample = all_descriptors[idx]
        else:
            sample = all_descriptors
        kmeans = KMeans(n_clusters=self.k, random_state=self.random_state, n_init=10)
        kmeans.fit(sample)
        self._kmeans = kmeans

    def extract(self, image_paths: list[str], batch_size: int = 16) -> np.ndarray:
        import os
        # 1. Extraer descriptores de todas las imágenes
        all_descs_list = []
        per_image_descs = []
        for p in image_paths:
            gray = _load_gray(p, self.image_size)
            if self.mode == "sift":
                des = self._sift_descriptors(gray)
            else:
                des = self._patch_descriptors(gray)
            per_image_descs.append(des)
            if len(des) > 0:
                # limitar para no explotar memoria
                if len(des) > 200:
                    rng = np.random.default_rng(0)
                    des = des[rng.choice(len(des), 200, replace=False)]
                all_descs_list.append(des)
        if not all_descs_list:
            return np.zeros((len(image_paths), self.k), dtype=np.float32)
        all_descs = np.concatenate(all_descs_list, axis=0)
        # 2. Construir vocabulario
        t0 = time.time()
        self._build_codebook(all_descs)
        # 3. Asignar histograma por imagen
        feats = []
        for des in per_image_descs:
            if len(des) == 0 or self._kmeans is None:
                hist = np.zeros(self.k, dtype=np.float32)
            else:
                words = self._kmeans.predict(des)
                hist, _ = np.histogram(words, bins=self.k, range=(0, self.k), density=False)
                hist = hist.astype(np.float32)
                if hist.sum() > 0:
                    hist /= hist.sum()
            feats.append(hist)
        elapsed = time.time() - t0
        print(f"  [paiva/bovw_{self.mode}] {len(image_paths)}/{len(image_paths)} ({elapsed:.1f}s, k={self.k})")
        return np.stack(feats, axis=0)


# ---------------------------------------------------------------------------
# Morfológicos — MC-V, Granulometría E/V
# ---------------------------------------------------------------------------

class MCVExtractor:
    """MC-V: Morphological Covariance Volume.

    Distancias {1,5,9,13}, orientaciones {0,45,90,135}, medida volumen.
    Simplificado: para cada (d, theta) apertura con segmento lineal de longitud d.
    """

    def __init__(self, cfg: dict):
        self.image_size = cfg.get("image_size", 128)
        self.distances = cfg.get("distances", [1, 5, 9, 13])
        self.orientations = cfg.get("orientations", [0, 45, 90, 135])

    def _line_selem(self, length: int, angle_deg: int) -> np.ndarray:
        # segmento discreto de longitud 'length' y orientación angle_deg
        # aproximado con footprint rectangular rotado
        import math
        # tamaño del footprint: length × 1
        size = max(1, length)
        # crear línea horizontal y rotar
        selem = np.zeros((size, size), dtype=bool)
        # dibujar línea en el centro
        mid = size // 2
        for i in range(size):
            selem[mid, i] = True
        if angle_deg == 0:
            return selem[mid:mid+1, :]  # 1×size
        if angle_deg == 90:
            return selem[:, mid:mid+1]  # size×1
        # para 45/135, usar línea diagonal
        selem = np.eye(size, dtype=bool)
        if angle_deg == 135:
            selem = np.fliplr(selem)
        return selem

    def _mcv_single(self, gray: np.ndarray) -> np.ndarray:
        from skimage.morphology import opening
        feats = []
        for d in self.distances:
            for theta in self.orientations:
                selem = self._line_selem(d, theta)
                opened = opening(gray, selem)
                vol = float(opened.sum()) / (255.0 * gray.size)  # volumen normalizado
                feats.append(vol)
        return np.array(feats, dtype=np.float32)

    def extract(self, image_paths: list[str], batch_size: int = 16) -> np.ndarray:
        from joblib import Parallel, delayed
        import os
        n_jobs = max(1, min(8, (os.cpu_count() or 4) - 1))

        def _one(p):
            g = _load_gray(p, self.image_size)
            return self._mcv_single(g)

        t0 = time.time()
        feats = Parallel(n_jobs=n_jobs, verbose=0)(delayed(_one)(p) for p in image_paths)
        elapsed = time.time() - t0
        print(f"  [paiva/mc_v] {len(image_paths)}/{len(image_paths)} ({elapsed:.1f}s, n_jobs={n_jobs})")
        return np.stack(feats, axis=0)


class GranulometryExtractor:
    """Granulometría con tamaños {0..15}, medida volumen o energía."""

    def __init__(self, cfg: dict):
        self.image_size = cfg.get("image_size", 128)
        self.sizes = cfg.get("sizes", list(range(16)))
        self.measure = cfg.get("measure", "volume")  # volume o energy

    def _gran_single(self, gray: np.ndarray) -> np.ndarray:
        from skimage.morphology import opening, disk
        feats = []
        for s in self.sizes:
            if s == 0:
                opened = gray
            else:
                selem = disk(s)
                opened = opening(gray, selem)
            if self.measure == "volume":
                val = float(opened.sum()) / (255.0 * gray.size)
            else:  # energy = sum of squares
                val = float((opened.astype(np.float32) ** 2).sum()) / (255.0**2 * gray.size)
            feats.append(val)
        return np.array(feats, dtype=np.float32)

    def extract(self, image_paths: list[str], batch_size: int = 16) -> np.ndarray:
        from joblib import Parallel, delayed
        import os
        n_jobs = max(1, min(8, (os.cpu_count() or 4) - 1))

        def _one(p):
            g = _load_gray(p, self.image_size)
            return self._gran_single(g)

        t0 = time.time()
        feats = Parallel(n_jobs=n_jobs, verbose=0)(delayed(_one)(p) for p in image_paths)
        elapsed = time.time() - t0
        print(f"  [paiva/gran_{self.measure}] {len(image_paths)}/{len(image_paths)} ({elapsed:.1f}s, n_jobs={n_jobs})")
        return np.stack(feats, axis=0)


# ---------------------------------------------------------------------------
# Registro para el pipeline (nombre -> clase + cfg por defecto)
# ---------------------------------------------------------------------------

PAIVA_EXTRACTORS = {
    "ehd":       (EHDExtractor,  {"image_size": 256}),
    "dcd":       (DCDExtractor,  {"image_size": 128, "k": 4, "random_state": 10}),
    "cld":       (CLDExtractor,  {"image_size": 128, "n_y": 18, "n_cb": 9, "n_cr": 9}),
    "bovw_s":    (BoVWExtractor, {"image_size": 128, "k": 50, "random_state": 1, "mode": "sift"}),
    "bovw_p":    (BoVWExtractor, {"image_size": 128, "k": 50, "random_state": 1, "mode": "patch", "patch_size": 16, "n_patches": 64}),
    "mc_v":      (MCVExtractor,  {"image_size": 128, "distances": [1, 5, 9, 13], "orientations": [0, 45, 90, 135]}),
    "gran_e":    (GranulometryExtractor, {"image_size": 128, "sizes": list(range(16)), "measure": "energy"}),
    "gran_v":    (GranulometryExtractor, {"image_size": 128, "sizes": list(range(16)), "measure": "volume"}),
}
