"""Modelo de costos de hardware para FSC-Tex.

Modela y cuantifica el costo incremental de extracción Delta t(a | S)
y el costo acumulado por estado, soportando tanto costos unitarios abstractos (control)
como latencias físicas calibradas en GPU (milisegundos).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set

# Latencias de inferencia calibradas por extractor en GPU RTX 4060 (milisegundos por imagen)
# Fuentes: mediciones de Outex / KTH archivadas en results/exploratory/
DEFAULT_HARDWARE_LATENCY_MS: Dict[str, float] = {
    # Muy rápidos (< 15 ms)
    "hog": 2.30,
    "siglip_base": 11.68,
    "resnet50": 11.94,
    "vgg16": 12.05,
    "beitv2_base_final": 12.22,
    "mae_base": 12.76,
    "efficientnet_b0": 14.39,
    # Moderados (15 - 30 ms)
    "deit_s": 15.38,
    "convnext_v2_t": 15.68,
    "eva02_base": 19.32,
    "swin_t": 21.42,
    "resnet101": 21.49,
    "dinov2_small": 24.60,
    "densenet121": 26.70,
    "vit_b16": 26.85,
    # Medios (30 - 100 ms)
    "glcm": 41.03,
    "lbp": 50.61,
    "dinov2": 57.65,
    "drlbp": 83.34,
    # Pesados (> 100 ms)
    "dinov2_large": 177.30,
    "gabor": 1029.21,
    # Color secuencial (SVD inference)
    "rgb_ngram_svd": 18.50,
}

# Costo promedio de evaluación del clasificador lineal y compuerta de decisión por estado (ms)
DEFAULT_POLICY_OVERHEAD_MS: float = 0.45


class HardwareCostModel:
    """Modelo de costos para la política de adquisición secuencial."""

    def __init__(
        self,
        cost_mode: str = "hardware",
        custom_latencies: Dict[str, float] | None = None,
        policy_overhead_ms: float = DEFAULT_POLICY_OVERHEAD_MS,
        normalize_by: str | None = None,
    ):
        """
        Parámetros:
          cost_mode: 'hardware' (latencia real en ms), 'unit' (costo constante 1.0 por bloque).
          custom_latencies: diccionario opcional {nombre_bloque: latencia_ms}.
          policy_overhead_ms: sobrecosto de evaluar la compuerta y el clasificador por paso.
          normalize_by: nombre del bloque de referencia para normalizar costo (ej. 'resnet50').
        """
        if cost_mode not in ("hardware", "unit"):
            raise ValueError(f"cost_mode desconocido: {cost_mode}")
        self.cost_mode = cost_mode
        self.latencies = dict(DEFAULT_HARDWARE_LATENCY_MS)
        if custom_latencies is not None:
            self.latencies.update(custom_latencies)
        self.policy_overhead_ms = policy_overhead_ms
        self.normalize_by = normalize_by

    @classmethod
    def from_json(cls, path: Path, cost_mode: str = "hardware", normalize_by: str | None = None) -> "HardwareCostModel":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        latencies = {}
        if "per_descriptor_latency_ms" in data:
            for k, v in data["per_descriptor_latency_ms"].items():
                if isinstance(v, dict):
                    val = v.get("median", v.get("mean"))
                    if val is None:
                        raise KeyError(f"No se encontró 'median' ni 'mean' para el extractor '{k}' en {path}")
                    latencies[k] = float(val)
                else:
                    latencies[k] = float(v)
        return cls(cost_mode=cost_mode, custom_latencies=latencies, normalize_by=normalize_by)

    def incremental_cost_ms(self, action: str, current_state_blocks: Set[str] | List[str] | None = None) -> float:
        """Calcula el costo incremental físico en milisegundos Delta t_ms(a | S)."""
        if action == "STOP":
            return 0.0
        if action not in self.latencies:
            raise KeyError(
                f"Latencia desconocida para el extractor '{action}'. "
                f"No se permite fallback silencioso; registre el extractor en DEFAULT_HARDWARE_LATENCY_MS o custom_latencies."
            )
        return self.latencies[action] + self.policy_overhead_ms

    def incremental_cost(self, action: str, current_state_blocks: Set[str] | List[str] | None = None) -> float:
        """Calcula el costo adicional Delta t(a | S) de ejecutar una acción."""
        if action == "STOP":
            return 0.0
        if self.cost_mode == "unit":
            return 1.0
        
        # Modo hardware
        if action not in self.latencies:
            raise KeyError(
                f"Latencia desconocida para el extractor '{action}'. "
                f"No se permite fallback silencioso; registre el extractor en DEFAULT_HARDWARE_LATENCY_MS o custom_latencies."
            )
        block_lat = self.latencies[action] + self.policy_overhead_ms
        if self.normalize_by is not None:
            if self.normalize_by not in self.latencies:
                raise KeyError(f"Extractor de normalización '{self.normalize_by}' no registrado en latencias.")
            ref_lat = self.latencies[self.normalize_by] + self.policy_overhead_ms
            return block_lat / ref_lat
        return block_lat

    def cumulative_cost(self, state_blocks: Set[str] | List[str]) -> float:
        """Calcula el costo acumulado de haber adquirido los bloques en S (en la escala del modelo)."""
        if self.cost_mode == "unit":
            return float(len(state_blocks))
        for b in state_blocks:
            if b not in self.latencies:
                raise KeyError(f"Latencia desconocida para el extractor '{b}'. No se permite fallback silencioso.")
        total_ms = sum(self.latencies[b] for b in state_blocks)
        total_ms += len(state_blocks) * self.policy_overhead_ms
        if self.normalize_by is not None:
            if self.normalize_by not in self.latencies:
                raise KeyError(f"Extractor de normalización '{self.normalize_by}' no registrado en latencias.")
            ref_lat = self.latencies[self.normalize_by] + self.policy_overhead_ms
            return total_ms / ref_lat
        return total_ms

    def cumulative_cost_ms(self, state_blocks: Set[str] | List[str]) -> float:
        """Calcula la latencia física total acumulada en milisegundos."""
        for b in state_blocks:
            if b not in self.latencies:
                raise KeyError(f"Latencia desconocida para el extractor '{b}'. No se permite fallback silencioso.")
        total_ms = sum(self.latencies[b] for b in state_blocks)
        total_ms += len(state_blocks) * self.policy_overhead_ms
        return total_ms
