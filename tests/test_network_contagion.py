"""Tests for ideological network and contagion shock propagation."""
import pytest
from src.analytics.network import build_ideological_network, simulate_contagion_spread


def test_build_ideological_network():
    net = build_ideological_network(min_correlation=0.20, max_nodes=20)
    assert "nodes" in net
    assert "links" in net
    assert len(net["nodes"]) > 0


def test_simulate_contagion_spread():
    res = simulate_contagion_spread("inflation", shock_magnitude=-3.0, max_steps=3)
    assert res["seed_topic"] == "inflation"
    assert res["shock_magnitude"] == -3.0
    assert len(res["steps"]) >= 1
    assert res["steps"][0]["step"] == 0
    assert len(res["steps"][0]["affected_nodes"]) == 1
