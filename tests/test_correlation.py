import pandas as pd
import numpy as np
from src.analytics.correlation import (
    compute_pairwise_correlation,
    compute_lead_lag,
    analyze_topic_correlations,
)
from src.topics.analyze import analyze_topic


def test_pairwise_correlation():
    dates = pd.date_range("2024-01-01", periods=10, freq="W-MON")
    df = pd.DataFrame({
        "Inflation": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        "Economy": [1.1, 2.2, 3.1, 3.9, 5.2, 5.9, 7.1, 8.2, 8.9, 10.1],
        "Approval": [-1.0, -2.0, -3.0, -4.0, -5.0, -6.0, -7.0, -8.0, -9.0, -10.0],
    }, index=dates)

    res = compute_pairwise_correlation(df)
    assert len(res["columns"]) == 3
    assert len(res["matrix"]) == 9  # 3x3 cells
    assert len(res["pairs"]) == 3   # 3 choose 2

    # Inflation & Economy should be strongly positive
    inf_econ = next(p for p in res["pairs"] if "Inflation" in (p["topic_a"], p["topic_b"]) and "Economy" in (p["topic_a"], p["topic_b"]))
    assert inf_econ["correlation"] > 0.95
    assert inf_econ["relationship"] == "strong_positive"

    # Inflation & Approval should be strongly inverse
    inf_app = next(p for p in res["pairs"] if "Inflation" in (p["topic_a"], p["topic_b"]) and "Approval" in (p["topic_a"], p["topic_b"]))
    assert inf_app["correlation"] < -0.95
    assert inf_app["relationship"] == "strong_inverse"


def test_compute_lead_lag():
    dates = pd.date_range("2024-01-01", periods=20, freq="W-MON")
    base = np.sin(np.linspace(0, 4 * np.pi, 20))
    # s_b is s_a shifted by 2 periods
    s_a = pd.Series(base, index=dates)
    s_b = pd.Series(np.roll(base, 2), index=dates)

    res = compute_lead_lag(s_a, s_b, label_a="Leading", label_b="Lagging", max_lag=3)
    assert "optimal_lag" in res
    assert "max_correlation" in res
    assert "summary" in res
    assert len(res["lags"]) == 7  # -3 to +3


def test_analyze_topic_correlations():
    t1 = analyze_topic("inflation")
    t2 = analyze_topic("donald_trump")

    res = analyze_topic_correlations([t1, t2], metric="media")
    assert res["n_topics"] == 2
    assert len(res["columns"]) == 2
    assert len(res["matrix"]) == 4
    assert len(res["pairs"]) == 1
    assert len(res["lead_lag"]) == 1
