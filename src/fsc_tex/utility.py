"""Módulo de utilidad y pérdida para FSC-Tex.

Define pérdidas muestrales, cálculo de ganancias bipolares (corrección vs perjuicio)
y extracción de incertidumbre/márgenes de clasificadores lineales.
"""

from __future__ import annotations

import numpy as np


def compute_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_weights: dict[int, float] | None = None,
) -> np.ndarray:
    """Calcula la pérdida 0-1 por muestra, opcionalmente ponderada por clase.
    
    0.0 = predicción correcta
    1.0 (o peso de clase) = predicción errónea
    """
    errors = (y_true != y_pred).astype(np.float32)
    if class_weights is not None:
        weights = np.array([class_weights.get(int(y), 1.0) for y in y_true], dtype=np.float32)
        return errors * weights
    return errors


def compute_gain(loss_base: np.ndarray, loss_augmented: np.ndarray) -> np.ndarray:
    """Calcula la ganancia empírica de utilidad al incorporar un bloque adicional.
    
    g(x, y, S, a) = L_S(x, y) - L_{S union a}(x, y)
    
    Valores:
      +1.0 : Corrección (la base falló, pero el bloque añadido corrigió la predicción)
       0.0 : Sin cambio (ambos acertaron o ambos fallaron)
      -1.0 : Perjuicio / Daño (la base acertó, pero el bloque añadido corrompió la predicción)
    """
    return loss_base.astype(np.float32) - loss_augmented.astype(np.float32)


def compute_margins(decision_function: np.ndarray) -> np.ndarray:
    """Calcula el margen de certeza de separación a partir de los logits/scores.
    
    Para multiclase (N, C): diferencia entre el score del 1er lugar y el 2do lugar.
    Para binario (N,): valor absoluto de la distancia al hiperplano.
    """
    decision_function = np.asarray(decision_function, dtype=np.float32)
    if decision_function.ndim == 1:
        return np.abs(decision_function)
    elif decision_function.shape[1] == 1:
        return np.abs(decision_function.ravel())
    else:
        # Partición para obtener top-2 valores por fila
        top2 = np.partition(decision_function, -2, axis=1)[:, -2:]
        return top2[:, 1] - top2[:, 0]


def summarize_oracle_and_harm(
    loss_base: np.ndarray,
    gains_by_action: dict[str, np.ndarray],
) -> dict[str, float]:
    """Resume el techo del oráculo, tasas de corrección y tasas de perjuicio.
    
    Parámetros:
      loss_base: vector (N,) de pérdidas de la base (0 o 1).
      gains_by_action: diccionario {nombre_accion: vector_ganancias (N,)}.
      
    Retorna métricas diagnósticas por muestra.
    """
    n_samples = len(loss_base)
    action_names = sorted(gains_by_action.keys())
    gain_matrix = np.column_stack([gains_by_action[a] for a in action_names])  # (N, n_actions)
    
    # 1. Desempeño base
    base_error_rate = float(np.mean(loss_base))
    base_accuracy = 1.0 - base_error_rate
    
    # 2. Oráculo con parada: max(0, max_a g_a)
    max_gains = np.max(gain_matrix, axis=1)  # mejor ganancia entre candidatos
    oracle_with_stop_gains = np.maximum(0.0, max_gains)  # si todos dañan, escoge STOP (0.0)
    oracle_error_rate = float(np.mean(loss_base - oracle_with_stop_gains))
    oracle_accuracy = 1.0 - oracle_error_rate
    oracle_margin_gain = float(np.mean(oracle_with_stop_gains))
    
    # 3. Acciones que dañan (perjuicio)
    # Fracción de muestras donde AL MENOS UN bloque causa daño (g < 0)
    harm_any = float(np.mean(np.any(gain_matrix < 0.0, axis=1)))
    # Fracción de muestras donde TODOS los bloques causan daño o son neutrales (ninguno mejora)
    no_repair_possible = float(np.mean(max_gains <= 0.0))
    # Muestras donde la base falló pero el oráculo puede corregirla
    repairable_errors = float(np.sum((loss_base > 0) & (max_gains > 0)) / max(1, np.sum(loss_base > 0)))
    
    # 4. Estadísticas individuales por bloque
    per_action_stats = {}
    for a in action_names:
        g = gains_by_action[a]
        per_action_stats[a] = {
            "repair_rate": float(np.mean(g > 0.0)),
            "harm_rate": float(np.mean(g < 0.0)),
            "net_gain": float(np.mean(g)),
        }
    
    return {
        "n_samples": n_samples,
        "base_accuracy": base_accuracy,
        "base_error_rate": base_error_rate,
        "oracle_with_stop_accuracy": oracle_accuracy,
        "oracle_with_stop_error_rate": oracle_error_rate,
        "oracle_headroom": oracle_margin_gain,
        "repairable_fraction_of_errors": repairable_errors,
        "any_candidate_harms_fraction": harm_any,
        "per_action_stats": per_action_stats,
    }
