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

