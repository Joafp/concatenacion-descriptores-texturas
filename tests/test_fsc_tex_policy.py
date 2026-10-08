"""Pruebas unitarias para el modelo de costos, grafo de estados y política FSC-Tex."""

import numpy as np
import pytest

from fsc_tex.cost_model import HardwareCostModel
from fsc_tex.policy import BaselineTwoStageCascadePolicy, SequentialAcquisitionPolicy
from fsc_tex.state_graph import State, StateGraph


def test_state_canonical_ordering():
    s1 = State(("resnet50", "siglip_base"))
    s2 = State(("siglip_base", "resnet50"))
    assert s1 == s2
    assert s1.id == "resnet50+siglip_base"
    assert s1.contains("resnet50")
    assert not s1.contains("dinov2")


def test_state_graph_transitions():
    graph = StateGraph(base_block="resnet50", candidate_blocks=["dinov2", "siglip_base"], max_depth=2)
    assert graph.initial_state.id == "resnet50"
    actions = graph.get_actions(graph.initial_state)
    assert "STOP" in actions
    assert "dinov2" in actions
    assert "siglip_base" in actions

    # Estado con profundidad máxima
    s_full = graph.initial_state.add("dinov2")
    actions_full = graph.get_actions(s_full)
    assert actions_full == ["STOP"]


def test_hardware_cost_model():
    model = HardwareCostModel(cost_mode="hardware")
    # Costo incremental de hog debe ser menor que dinov2_large
    c_hog = model.incremental_cost("hog", {"resnet50"})
    c_dino = model.incremental_cost("dinov2_large", {"resnet50"})
    assert c_hog < c_dino
    assert model.incremental_cost("STOP", {"resnet50"}) == 0.0

    # Modo unitario
    model_u = HardwareCostModel(cost_mode="unit")
    assert model_u.incremental_cost("hog", {"resnet50"}) == 1.0
    assert model_u.incremental_cost("dinov2_large", {"resnet50"}) == 1.0


def test_sequential_policy_synthetic_fit():
    graph = StateGraph(base_block="resnet50", candidate_blocks=["block_good", "block_bad"], max_depth=2)
    cost_model = HardwareCostModel(cost_mode="unit")

    # Muestras sintéticas: N=100
    N = 100
    rng = np.random.default_rng(42)

    # Características de la base: margen alto (seguro) vs margen bajo (inseguro)
    margins = rng.uniform(0.1, 2.0, size=N)
    top_scores = rng.uniform(0.5, 3.0, size=(N, 3))
    
    feats_base = np.column_stack([
        np.zeros((N, len(graph.allowlist))),
        margins,
        np.ones(N),
        top_scores,
    ])

    # block_good repara cuando margen < 0.8
    # block_bad aumenta error
    loss_base = (margins < 0.8).astype(np.float32)
    loss_good = np.zeros(N, dtype=np.float32)  # repara todo
    loss_bad = np.ones(N, dtype=np.float32)    # daña todo

    s_good = graph.initial_state.add("block_good")
    s_bad = graph.initial_state.add("block_bad")

    features_by_state = {
        graph.initial_state.id: feats_base,
        s_good.id: feats_base,
        s_bad.id: feats_base,
    }
    losses_by_state = {
        graph.initial_state.id: loss_base,
        s_good.id: loss_good,
        s_bad.id: loss_bad,
    }

    # Probar Horizonte 1
    policy_h1 = SequentialAcquisitionPolicy(
        graph=graph,
        cost_model=cost_model,
        horizon=1,
        cost_lambda=0.1,
    )
    policy_h1.fit_transitions(features_by_state, losses_by_state)

    # Caso seguro (margen muy alto): debe preferir STOP
    feat_safe = graph.encode_state_features(graph.initial_state, margin=3.0, top_scores=np.array([5.0, 1.0, 0.0]))
    action_safe, _ = policy_h1.select_action(graph.initial_state, feat_safe)
    assert action_safe == "STOP"

    # Caso inseguro (margen muy bajo): debe preferir block_good
    feat_unsafe = graph.encode_state_features(graph.initial_state, margin=0.1, top_scores=np.array([1.1, 1.0, 0.5]))
    action_unsafe, _ = policy_h1.select_action(graph.initial_state, feat_unsafe)
    assert action_unsafe == "block_good"


def test_delayed_complementarity_distinguishes_h1_from_h2():
    """Test 7 del protocolo: comprueba que Horizonte 2 descubre complementariedad diferida mientras H1 se detiene."""
    graph = StateGraph(base_block="resnet50", candidate_blocks=["block_A", "block_B"], max_depth=3)
    cost_model = HardwareCostModel(cost_mode="unit")
    cost_lambda = 0.2

    N = 100
    rng = np.random.default_rng(42)

    # Características constantes para que el predictor aprenda la expectativa poblacional
    feats = np.ones((N, len(graph.allowlist) + 5), dtype=np.float32)

    s_A = graph.initial_state.add("block_A")
    s_B = graph.initial_state.add("block_B")
    s_AB = s_A.add("block_B")

    # Base, A y B aislados tienen pérdida 1.0. Solo la combinación A+B tiene pérdida 0.0
    losses_by_state = {
        graph.initial_state.id: np.ones(N, dtype=np.float32),
        s_A.id: np.ones(N, dtype=np.float32),
        s_B.id: np.ones(N, dtype=np.float32),
        s_AB.id: np.zeros(N, dtype=np.float32),
    }
    features_by_state = {
        graph.initial_state.id: feats,
        s_A.id: feats,
        s_B.id: feats,
        s_AB.id: feats,
    }

    # 1. Horizonte 1 (Miope): debe rechazar tanto A como B porque individualmente no aportan
    policy_h1 = SequentialAcquisitionPolicy(
        graph=graph, cost_model=cost_model, horizon=1, cost_lambda=cost_lambda, random_state=42
    )
    policy_h1.fit_transitions(features_by_state, losses_by_state)
    action_h1, _ = policy_h1.select_action(graph.initial_state, feats[0])
    assert action_h1 == "STOP", f"Horizonte 1 debió detenerse por ser miope, pero eligió {action_h1}"

    # 2. Horizonte 2 (Bellman no miope): anticipa que dar 2 pasos repara el error
    policy_h2 = SequentialAcquisitionPolicy(
        graph=graph, cost_model=cost_model, horizon=2, cost_lambda=cost_lambda, random_state=42
    )
    policy_h2.fit_transitions(features_by_state, losses_by_state)
    action_h2_step1, _ = policy_h2.select_action(graph.initial_state, feats[0])
    assert action_h2_step1 in ("block_A", "block_B"), f"Horizonte 2 debió iniciar adquisición, pero eligió {action_h2_step1}"

    # Paso 2 desde el bloque adquirido en paso 1
    state_after_step1 = graph.initial_state.add(action_h2_step1)
    action_h2_step2, _ = policy_h2.select_action(state_after_step1, feats[0])
    expected_second = "block_B" if action_h2_step1 == "block_A" else "block_A"
    assert action_h2_step2 == expected_second, f"Paso 2 debió adquirir el bloque complementario {expected_second}, eligió {action_h2_step2}"


def test_real_case_feasibility_physical_budget():
    """R1 Test 1: Comprueba que BEiTv2 y DINOv2 son factibles bajo presupuesto físico en ms.
    
    Verifica además que cambiar el descriptor base no altera el costo incremental físico del candidato.
    """
    cost_model = HardwareCostModel(cost_mode="hardware")
    candidates = ["siglip_base", "beitv2_base_final", "convnext_v2_t", "eva02_base", "dinov2"]
    graph = StateGraph(base_block="resnet50", candidate_blocks=candidates, max_depth=3)

    spent_base = cost_model.cumulative_cost_ms(graph.initial_state.blocks)  # 11.94 + 0.45 = 12.39 ms
    
    # 1. Presupuesto amplio (100 ms): ambos BEiTv2 y DINOv2 deben ser factibles
    rem_100 = 100.0 - spent_base  # 87.61 ms
    actions_100 = graph.get_actions(graph.initial_state, remaining_budget=rem_100, cost_model=cost_model)
    assert "beitv2_base_final" in actions_100, "BEiTv2 debió ser factible con 87.61 ms remanentes"
    assert "dinov2" in actions_100, "DINOv2 debió ser factible con 87.61 ms remanentes"

    # 2. Presupuesto ajustado (25 ms): sólo SigLIP es factible (12.13 ms <= 12.61 ms)
    # BEiTv2 (12.67 ms > 12.61 ms) y DINOv2 (58.10 ms > 12.61 ms) quedan fuera
    rem_25 = 25.0 - spent_base  # 12.61 ms
    actions_25 = graph.get_actions(graph.initial_state, remaining_budget=rem_25, cost_model=cost_model)
    assert "siglip_base" in actions_25
    assert "beitv2_base_final" not in actions_25
    assert "dinov2" not in actions_25

    # 3. Invarianza de latencia física al cambiar de base
    c_beit_resnet = cost_model.incremental_cost("beitv2_base_final", {"resnet50"})
    c_beit_hog = cost_model.incremental_cost("beitv2_base_final", {"hog"})
    assert c_beit_resnet == pytest.approx(12.67, abs=1e-2)
    assert c_beit_hog == pytest.approx(12.67, abs=1e-2)
    assert c_beit_resnet == c_beit_hog, "Cambiar la base no debe alterar el costo físico del candidato"


def test_decreasing_budget_tracking_and_multistep_acquisitions():
    """R1 Test 2: Comprueba que el presupuesto se descuenta en cada paso y permite >= 2 adquisiciones reales."""
    cost_model = HardwareCostModel(cost_mode="hardware")
    candidates = ["dinov2", "beitv2_base_final"]
    graph = StateGraph(base_block="resnet50", candidate_blocks=candidates, max_depth=3)

    N = 100
    # Base: 12.39 ms
    # dinov2: 58.10 ms
    # beitv2: 12.67 ms
    # Secuencia completa: 12.39 + 58.10 + 12.67 = 83.16 ms <= 100.0 ms
    s_dino = graph.initial_state.add("dinov2")
    s_full = s_dino.add("beitv2_base_final")
    s_beit = graph.initial_state.add("beitv2_base_final")

    # Pérdidas sintéticas
    losses_by_state = {
        graph.initial_state.id: np.ones(N, dtype=np.float32),
        s_dino.id: np.full(N, 0.5, dtype=np.float32),
        s_full.id: np.zeros(N, dtype=np.float32),
        s_beit.id: np.full(N, 0.8, dtype=np.float32),
    }

    # Features:
    d_feat = len(graph.allowlist) + 5
    features_by_state = {sid: np.ones((N, d_feat), dtype=np.float32) for sid in losses_by_state}

    policy = SequentialAcquisitionPolicy(
        graph=graph, cost_model=cost_model, horizon=2, cost_lambda=0.001, random_state=42
    )
    policy.fit_transitions(features_by_state, losses_by_state)

    def dummy_feat_fn(st, rem_b):
        return np.ones(d_feat, dtype=np.float32)

    # 1. Con presupuesto de 100 ms: debe ejecutar exactamente 2 adquisiciones reales
    final_st, actions_taken, total_cost = policy.rollout_trajectory(
        initial_state=graph.initial_state, get_features_fn=dummy_feat_fn, budget=100.0
    )
    assert len(actions_taken) == 2, f"Debió ejecutar 2 adquisiciones, ejecutó {actions_taken}"
    assert actions_taken == ["dinov2", "beitv2_base_final"]
    assert total_cost == pytest.approx(83.16, abs=0.1)
    assert total_cost <= 100.0

    # 2. Con presupuesto restrictivo de 60 ms:
    # Base cuesta 12.39 ms. Remanente = 47.61 ms.
    # dinov2 (58.10 ms > 47.61 ms) no es factible. Sólo beitv2 (12.67 ms) es factible.
    final_st_tight, actions_tight, cost_tight = policy.rollout_trajectory(
        initial_state=graph.initial_state, get_features_fn=dummy_feat_fn, budget=60.0
    )
    assert "dinov2" not in actions_tight, "DINOv2 no debió ser seleccionado bajo presupuesto restrictivo de 60 ms"
    assert cost_tight <= 60.0


def test_no_oracle_optimism_in_bellman_continuation():
    """R1 Test 3: Comprueba la eliminación del optimismo del oráculo.
    
    Con acciones futuras indistinguibles y pérdidas opuestas ([0, 1] vs [1, 0]),
    la inducción desplegable aprende la expectativa poblacional (0.5), no el error cero del oráculo (0.0).
    """
    candidates = ["step1_cand", "opt_A", "opt_B"]
    graph = StateGraph(base_block="resnet50", candidate_blocks=candidates, max_depth=3)
    cost_model = HardwareCostModel(cost_mode="unit")

    N = 200
    # Features indistinguibles (todos unos)
    d_feat = len(graph.allowlist) + 5
    feats = np.ones((N, d_feat), dtype=np.float32)

    s1 = graph.initial_state.add("step1_cand")
    s1_A = s1.add("opt_A")
    s1_B = s1.add("opt_B")

    # Pérdidas futuras opuestas:
    loss_A = np.tile([0.0, 1.0], N // 2).astype(np.float32)
    loss_B = np.tile([1.0, 0.0], N // 2).astype(np.float32)

    losses_by_state = {
        graph.initial_state.id: np.ones(N, dtype=np.float32),
        s1.id: np.ones(N, dtype=np.float32),
        s1_A.id: loss_A,
        s1_B.id: loss_B,
    }
    features_by_state = {sid: feats for sid in losses_by_state}

    policy = SequentialAcquisitionPolicy(
        graph=graph, cost_model=cost_model, horizon=2, cost_lambda=0.0, random_state=42
    )
    policy.fit_transitions(features_by_state, losses_by_state)

    # El modelo Q2 para el paso 1 evalúa la continuación hacia opt_A y opt_B
    m_q2 = policy.models[(2, graph.initial_state.id, "step1_cand")]
    pred_val = float(m_q2.predict(feats[:1])[0])

    # El oráculo previo aprendía min(loss_A, loss_B) = 0.0.
    # El modelo desplegable debe predecir la expectativa poblacional E[Loss] = 0.5.
    assert pred_val > 0.35, f"Optimismo del oráculo detectado: pred_val={pred_val:.4f} <= 0.35"
    assert pred_val == pytest.approx(0.5, abs=0.15)


def test_feasibility_parity_between_training_and_inference():
    """R1 Test 4: Comprueba paridad de factibilidad entre fit_transitions y select_action."""
    cost_model = HardwareCostModel(cost_mode="hardware")
    candidates = ["beitv2_base_final", "dinov2"]
    graph = StateGraph(base_block="resnet50", candidate_blocks=candidates, max_depth=3)

    # Base: 12.39 ms. Con max_budget = 30 ms, beitv2 (12.67 ms) es factible (25.06 <= 30),
    # pero dinov2 (58.10 ms) es infactible (70.49 > 30).
    N = 50
    d_feat = len(graph.allowlist) + 5
    feats = np.ones((N, d_feat), dtype=np.float32)

    s_beit = graph.initial_state.add("beitv2_base_final")
    s_dino = graph.initial_state.add("dinov2")

    losses_by_state = {
        graph.initial_state.id: np.ones(N, dtype=np.float32),
        s_beit.id: np.zeros(N, dtype=np.float32),
        s_dino.id: np.zeros(N, dtype=np.float32),
    }
    features_by_state = {sid: feats for sid in losses_by_state}

    policy = SequentialAcquisitionPolicy(
        graph=graph, cost_model=cost_model, horizon=1, cost_lambda=0.01, random_state=42
    )
    # Ajuste con max_budget = 30 ms
    policy.fit_transitions(features_by_state, losses_by_state, max_budget=30.0)

    # 1. En entrenamiento: la acción dinov2 no debió ser ajustada desde initial_state
    assert (1, graph.initial_state.id, "dinov2") not in policy.models
    assert (1, graph.initial_state.id, "beitv2_base_final") in policy.models

    # 2. En inferencia: con el mismo presupuesto remanente (30 - 12.39 = 17.61 ms),
    # dinov2 no está en las acciones factibles
    rem_b = 30.0 - cost_model.cumulative_cost_ms(graph.initial_state.blocks)
    actions = graph.get_actions(graph.initial_state, remaining_budget=rem_b, cost_model=cost_model)
    assert "dinov2" not in actions
    assert "beitv2_base_final" in actions

    act, _ = policy.select_action(graph.initial_state, feats[0], remaining_budget=rem_b)
    assert act == "beitv2_base_final"


def test_unknown_extractor_raises_key_error():
    """R1 Test 5: Comprueba que extractores desconocidos lanzan KeyError sin fallback silencioso."""
    cost_model = HardwareCostModel(cost_mode="hardware")

    with pytest.raises(KeyError):
        cost_model.incremental_cost("unknown_extractor", {"resnet50"})

    with pytest.raises(KeyError):
        cost_model.incremental_cost_ms("unknown_extractor")

    with pytest.raises(KeyError):
        cost_model.cumulative_cost({"resnet50", "unknown_extractor"})

    with pytest.raises(KeyError):
        cost_model.cumulative_cost_ms({"resnet50", "unknown_extractor"})

    with pytest.raises(KeyError):
        HardwareCostModel(normalize_by="invalid_block").incremental_cost("resnet50")


def test_canonical_22_descriptors_in_cost_model():
    """R1 Test 6: Comprueba que los 22 descriptores canónicos del registro existen en HardwareCostModel."""
    import json
    from pathlib import Path
    registry_path = Path("configs/fsc_tex/descriptor_registry_v1.json")
    assert registry_path.exists(), "El registro de descriptores debe existir"

    with open(registry_path, "r", encoding="utf-8") as f:
        reg = json.load(f)

    cost_model = HardwareCostModel(cost_mode="hardware")
    descriptors = reg["descriptors"]
    assert len(descriptors) == 22

    for desc in descriptors:
        name = desc["name"]
        cost = cost_model.incremental_cost(name, set())
        cost_ms = cost_model.incremental_cost_ms(name)
        assert cost > 0.0, f"Costo de {name} debe ser positivo"
        assert cost_ms > 0.0, f"Latencia en ms de {name} debe ser positiva"
        assert np.isfinite(cost), f"Costo de {name} debe ser finito"


