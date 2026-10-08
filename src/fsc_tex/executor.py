"""Ejecución Física Bajo Demanda y Benchmark Online para FSC-Tex (Hito R5).

Implementa la medición de eficiencia desde la imagen a la predicción:
1. OnlineExtractorRegistry: carga perezosa de extractores en GPU/CPU con calentamiento y sincronización estricta CUDA.
2. OnlineSequentialPolicyExecutor: extracción adaptativa bajo demanda, midiendo latencia física de extracción,
   sobrecosto de la política (gating) y tiempo del clasificador.
3. run_online_benchmark_condition: benchmark pareado que verifica acuerdo de rutas (route agreement) y
   acuerdo de predicciones (prediction agreement) entre inferencia física y simulación cacheada.
"""

from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np
from PIL import Image

try:
    import torch
    from torchvision import transforms
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from fsc_tex.cost_model import HardwareCostModel
from fsc_tex.crossfit import ProtectedFeatureStore
from fsc_tex.policy import SequentialAcquisitionPolicy
from fsc_tex.state_graph import State, StateGraph
from fsc_tex.utility import compute_margins


class OnlineExtractorRegistry:
    """Registro de modelos residentes en memoria para extracción online en GPU/CPU."""

    def __init__(self, device: Optional[str] = None, seed: int = 42):
        self.device = device or ("cuda" if (HAS_TORCH and torch.cuda.is_available()) else "cpu")
        self.seed = seed
        self._models: Dict[str, Any] = {}
        self._transforms: Dict[str, Any] = {}
        self._extract_fns: Dict[str, Callable[[Any], np.ndarray]] = {}

    def is_cuda(self) -> bool:
        return self.device == "cuda"

    def register_custom_extractor(self, name: str, extract_fn: Callable[[Any], np.ndarray]):
        """Permite registrar funciones de extracción sintéticas o mock para pruebas."""
        self._extract_fns[name] = extract_fn

    def load_extractor(self, name: str) -> Callable[[Any], np.ndarray]:
        """Carga perezosamente el extractor especificado y lo mantiene residente en memoria."""
        if name in self._extract_fns:
            return self._extract_fns[name]

        if not HAS_TORCH:
            raise RuntimeError("PyTorch es requerido para extracción online de modelos profundos.")

        if name == "resnet50":
            import timm
            model = timm.create_model("resnet50.a1_in1k", pretrained=True, num_classes=0).to(self.device).eval()
            cfg = timm.data.resolve_model_data_config(model)
            tf = transforms.Compose([
                transforms.Resize(cfg["input_size"][1:]),
                transforms.CenterCrop(cfg["input_size"][1:]),
                transforms.ToTensor(),
                transforms.Normalize(mean=cfg["mean"], std=cfg["std"]),
            ])

            def extract(img_input: Any) -> np.ndarray:
                img = img_input if isinstance(img_input, Image.Image) else Image.open(img_input).convert("RGB")
                tensor = tf(img).unsqueeze(0).to(self.device)
                with torch.inference_mode():
                    feat = model(tensor)
                if self.is_cuda():
                    torch.cuda.synchronize()
                vec = feat.cpu().numpy().ravel()
                norm = np.linalg.norm(vec)
                return vec / (norm + 1e-12)

            self._extract_fns[name] = extract
            return extract

        elif name == "beitv2_base_final":
            import timm
            model = timm.create_model("beitv2_base_patch16_224.in1k_ft_in22k_in1k", pretrained=True, num_classes=0).to(self.device).eval()
            cfg = timm.data.resolve_model_data_config(model)
            tf = transforms.Compose([
                transforms.Resize(cfg["input_size"][1:]),
                transforms.CenterCrop(cfg["input_size"][1:]),
                transforms.ToTensor(),
                transforms.Normalize(mean=cfg["mean"], std=cfg["std"]),
            ])

            def extract(img_input: Any) -> np.ndarray:
                img = img_input if isinstance(img_input, Image.Image) else Image.open(img_input).convert("RGB")
                tensor = tf(img).unsqueeze(0).to(self.device)
                with torch.inference_mode():
                    feat = model(tensor)
                if self.is_cuda():
                    torch.cuda.synchronize()
                vec = feat.cpu().numpy().ravel()
                norm = np.linalg.norm(vec)
                return vec / (norm + 1e-12)

            self._extract_fns[name] = extract
            return extract

        elif name == "dinov2":
            import timm
            model = timm.create_model("vit_base_patch14_dinov2.lvd142m", pretrained=True, num_classes=0).to(self.device).eval()
            cfg = timm.data.resolve_model_data_config(model)
            tf = transforms.Compose([
                transforms.Resize(cfg["input_size"][1:]),
                transforms.CenterCrop(cfg["input_size"][1:]),
                transforms.ToTensor(),
                transforms.Normalize(mean=cfg["mean"], std=cfg["std"]),
            ])

            def extract(img_input: Any) -> np.ndarray:
                img = img_input if isinstance(img_input, Image.Image) else Image.open(img_input).convert("RGB")
                tensor = tf(img).unsqueeze(0).to(self.device)
                with torch.inference_mode():
                    feat = model(tensor)
                if self.is_cuda():
                    torch.cuda.synchronize()
                vec = feat.cpu().numpy().ravel()
                norm = np.linalg.norm(vec)
                return vec / (norm + 1e-12)

            self._extract_fns[name] = extract
            return extract

        elif name == "siglip_base":
            from transformers import AutoImageProcessor, AutoModel
            processor = AutoImageProcessor.from_pretrained("google/siglip-base-patch16-224")
            model = AutoModel.from_pretrained("google/siglip-base-patch16-224").to(self.device).eval()

            def extract(img_input: Any) -> np.ndarray:
                img = img_input if isinstance(img_input, Image.Image) else Image.open(img_input).convert("RGB")
                inputs = processor(images=img, return_tensors="pt").to(self.device)
                with torch.inference_mode():
                    out = model.get_image_features(**inputs)
                if self.is_cuda():
                    torch.cuda.synchronize()
                vec = out.cpu().numpy().ravel()
                norm = np.linalg.norm(vec)
                return vec / (norm + 1e-12)

            self._extract_fns[name] = extract
            return extract

        else:
            raise KeyError(f"Extractor '{name}' no tiene implementación online registrada en OnlineExtractorRegistry.")

    def warmup(self, extractors: List[str], dummy_image: Optional[Image.Image] = None, n_warmup: int = 3):
        """Ejecuta pasadas de calentamiento para descartar el arranque en frío del timing."""
        if dummy_image is None:
            dummy_image = Image.new("RGB", (224, 224), color=(128, 128, 128))
        for name in extractors:
            fn = self.load_extractor(name)
            for _ in range(n_warmup):
                fn(dummy_image)
        if self.is_cuda():
            torch.cuda.synchronize()


class OnlineSequentialPolicyExecutor:
    """Ejecutor de inferencia adaptativa bajo demanda con medición sincronizada."""

    def __init__(
        self,
        policy: SequentialAcquisitionPolicy,
        state_classifiers: Dict[str, Any],
        graph: StateGraph,
        cost_model: HardwareCostModel,
        extractor_registry: OnlineExtractorRegistry,
        target_budget_ms: float,
    ):
        self.policy = policy
        self.clfs = state_classifiers
        self.graph = graph
        self.cost_model = cost_model
        self.registry = extractor_registry
        self.target_budget_ms = target_budget_ms

    def execute_image(self, image_input: Any) -> Dict[str, Any]:
        """Ejecuta la adquisición secuencial completa sobre una imagen, midiendo tiempos por componente.
        
        Devuelve:
          prediction: clase predicha final
          route: lista de bloques adquiridos
          stop_reason: causa de finalización
          latencies_ms: desglose de tiempos físicos medidos
        """
        curr_state = self.graph.initial_state
        base_block = self.graph.base_block
        rem_b = self.target_budget_ms

        extractor_time_ms = 0.0
        policy_time_ms = 0.0
        clf_time_ms = 0.0

        acquired_vectors: Dict[str, np.ndarray] = {}

        # 1. Extracción del bloque base
        t0 = time.perf_counter()
        fn_base = self.registry.load_extractor(base_block)
        v_base = fn_base(image_input)
        if self.registry.is_cuda():
            torch.cuda.synchronize()
        t1 = time.perf_counter()
        extractor_time_ms += (t1 - t0) * 1000.0
        acquired_vectors[base_block] = v_base

        # Descontar costo del modelo de costos para la base
        base_cost_model = self.cost_model.cumulative_cost_ms(curr_state.blocks)
        rem_b = max(0.0, rem_b - base_cost_model)

        step_num = 0
        stop_reason = "max_depth_reached"

        while True:
            # 2. Evaluación del clasificador en el estado actual
            t_clf_0 = time.perf_counter()
            blocks_data = [acquired_vectors[b] for b in curr_state.blocks]
            X_curr = np.concatenate(blocks_data).reshape(1, -1)
            clf = self.clfs[curr_state.id]
            df = clf.decision_function(X_curr)
            preds_curr = clf.predict(X_curr)[0]
            margins_curr = float(compute_margins(df)[0])
            t_clf_1 = time.perf_counter()
            clf_time_ms += (t_clf_1 - t_clf_0) * 1000.0

            if len(curr_state) >= self.graph.max_depth:
                stop_reason = "max_depth_reached"
                break

            if rem_b <= 0:
                stop_reason = "budget_exhausted"
                break

            # 3. Evaluación de la política
            t_pol_0 = time.perf_counter()
            top_scores_curr = np.abs(df.ravel()) if (df.ndim == 1 or df.shape[1] == 1) else np.sort(df[0])[::-1]
            feat_s = self.graph.encode_state_features(
                state=curr_state,
                margin=margins_curr,
                top_scores=top_scores_curr,
                remaining_budget=float(rem_b),
            )
            action, _ = self.policy.select_action(curr_state, feat_s, remaining_budget=rem_b)
            t_pol_1 = time.perf_counter()
            policy_time_ms += (t_pol_1 - t_pol_0) * 1000.0

            if action == "STOP":
                stop_reason = "policy_decided_stop"
                break

            # 4. Extracción bajo demanda del bloque seleccionado
            t_ext_0 = time.perf_counter()
            fn_cand = self.registry.load_extractor(action)
            v_cand = fn_cand(image_input)
            if self.registry.is_cuda():
                torch.cuda.synchronize()
            t_ext_1 = time.perf_counter()
            extractor_time_ms += (t_ext_1 - t_ext_0) * 1000.0

            acquired_vectors[action] = v_cand
            inc_c = self.cost_model.incremental_cost(action, curr_state.blocks)
            rem_b = max(0.0, rem_b - inc_c)
            curr_state = curr_state.add(action)
            step_num += 1

        # Clasificación final en curr_state
        blocks_final = [acquired_vectors[b] for b in curr_state.blocks]
        X_final = np.concatenate(blocks_final).reshape(1, -1)
        clf_final = self.clfs[curr_state.id]
        final_pred = clf_final.predict(X_final)[0]

        total_measured_ms = extractor_time_ms + policy_time_ms + clf_time_ms

        return {
            "final_prediction": final_pred,
            "final_state": curr_state.id,
            "route": list(curr_state.blocks),
            "stop_reason": stop_reason,
            "total_measured_ms": total_measured_ms,
            "latency_breakdown_ms": {
                "extractor_ms": extractor_time_ms,
                "policy_gate_ms": policy_time_ms,
                "classifier_ms": clf_time_ms,
            },
        }


def benchmark_physical_online_parity(
    policy: SequentialAcquisitionPolicy,
    state_classifiers: Dict[str, Any],
    graph: StateGraph,
    cost_model: HardwareCostModel,
    feature_store: ProtectedFeatureStore,
    extractor_registry: OnlineExtractorRegistry,
    test_idx: np.ndarray,
    image_inputs: List[Any],
    target_budget_ms: float,
) -> Dict[str, Any]:
    """Compara sistemáticamente la inferencia física bajo demanda contra la simulación cacheada."""
    assert len(test_idx) == len(image_inputs), "Número de índices y de imágenes debe coincidir."
    n_samples = len(test_idx)

    # 1. Warmup
    all_needed_blocks = [graph.base_block] + graph.candidate_blocks
    extractor_registry.warmup(all_needed_blocks, n_warmup=2)

    executor = OnlineSequentialPolicyExecutor(
        policy=policy,
        state_classifiers=state_classifiers,
        graph=graph,
        cost_model=cost_model,
        extractor_registry=extractor_registry,
        target_budget_ms=target_budget_ms,
    )

    online_predictions = []
    online_routes = []
    online_latencies = []
    online_breakdowns = []

    cached_predictions = []
    cached_routes = []
    cached_latencies = []

    base_cost_ms = cost_model.cumulative_cost_ms(graph.initial_state.blocks)

    for i, s_idx in enumerate(test_idx):
        img_in = image_inputs[i]

        # A. Ejecución Física Online
        res_online = executor.execute_image(img_in)
        online_predictions.append(res_online["final_prediction"])
        online_routes.append(res_online["final_state"])
        online_latencies.append(res_online["total_measured_ms"])
        online_breakdowns.append(res_online["latency_breakdown_ms"])

        # B. Simulación Cacheada
        curr_s = graph.initial_state
        rem_b = target_budget_ms - base_cost_ms
        while len(curr_s) < graph.max_depth and rem_b > 0:
            clf_c = state_classifiers[curr_s.id]
            X_c = feature_store.get_state_matrix(curr_s)[s_idx : s_idx + 1]
            df_c = clf_c.decision_function(X_c)
            m_c = float(compute_margins(df_c)[0])
            top_s = np.abs(df_c.ravel()) if df_c.ndim == 1 else np.sort(df_c[0])[::-1]

            feat_c = graph.encode_state_features(
                state=curr_s,
                margin=m_c,
                top_scores=top_s,
                remaining_budget=float(rem_b),
            )
            act, _ = policy.select_action(curr_s, feat_c, remaining_budget=rem_b)
            if act == "STOP":
                break
            rem_b = max(0.0, rem_b - cost_model.incremental_cost(act, curr_s.blocks))
            curr_s = curr_s.add(act)

        clf_fin = state_classifiers[curr_s.id]
        X_fin = feature_store.get_state_matrix(curr_s)[s_idx : s_idx + 1]
        p_cached = clf_fin.predict(X_fin)[0]
        cached_predictions.append(p_cached)
        cached_routes.append(curr_s.id)
        cached_latencies.append(cost_model.cumulative_cost_ms(curr_s.blocks))

    # Métricas de Paridad
    route_agreement = float(np.mean([r_on == r_ca for r_on, r_ca in zip(online_routes, cached_routes)]))
    prediction_agreement = float(np.mean([p_on == p_ca for p_on, p_ca in zip(online_predictions, cached_predictions)]))

    mean_online_ms = float(np.mean(online_latencies))
    median_online_ms = float(np.median(online_latencies))
    p95_online_ms = float(np.percentile(online_latencies, 95))

    mean_cached_ms = float(np.mean(cached_latencies))

    # Desglose promedio
    mean_ext_ms = float(np.mean([b["extractor_ms"] for b in online_breakdowns]))
    mean_gate_ms = float(np.mean([b["policy_gate_ms"] for b in online_breakdowns]))
    mean_clf_ms = float(np.mean([b["classifier_ms"] for b in online_breakdowns]))

    return {
        "n_samples": n_samples,
        "device": extractor_registry.device,
        "route_agreement": route_agreement,
        "prediction_agreement": prediction_agreement,
        "online_timing_ms": {
            "mean": mean_online_ms,
            "median": median_online_ms,
            "p95": p95_online_ms,
        },
        "cached_timing_ms": {
            "mean": mean_cached_ms,
        },
        "timing_breakdown_ms": {
            "mean_extractor_ms": mean_ext_ms,
            "mean_policy_gate_ms": mean_gate_ms,
            "mean_classifier_ms": mean_clf_ms,
        },
        "parity_passed": route_agreement >= 0.95 and prediction_agreement >= 0.95,
    }
