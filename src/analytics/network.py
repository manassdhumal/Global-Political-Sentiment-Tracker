"""Ideological Network Graph & Entity Clustering Analytics."""
from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

from src.topics.catalog import load_catalog
from src.topics.synth import topic_weekly
from src.analytics.correlation import compute_pairwise_correlation


CATEGORY_CLUSTERS: dict[str, dict[str, Any]] = {
    "macroeconomics": {"id": 0, "name": "Macroeconomics & Cost of Living", "color": "#f59e0b"},
    "conservative_right": {"id": 1, "name": "Conservative & Nationalist Movements", "color": "#ef4444"},
    "progressive_centre": {"id": 2, "name": "Centre-Left & Democratic Institutions", "color": "#3b82f6"},
    "geopolitics_security": {"id": 3, "name": "Geopolitical Conflicts & Defense", "color": "#8b5cf6"},
    "technology_governance": {"id": 4, "name": "Emerging Tech & Global Governance", "color": "#10b981"},
}


def _assign_cluster(topic_id: str, category: str) -> dict[str, Any]:
    """Map a topic entity to an ideological / topical community cluster."""
    t_id = topic_id.lower()
    if category == "economy" or any(k in t_id for k in ["inflation", "tax", "housing", "interest", "debt"]):
        return CATEGORY_CLUSTERS["macroeconomics"]
    elif any(k in t_id for k in ["trump", "sunak", "republican", "conservative", "afd", "reform", "meloni", "milei", "bjp", "netanyahu"]):
        return CATEGORY_CLUSTERS["conservative_right"]
    elif any(k in t_id for k in ["biden", "harris", "starmer", "democrat", "labour", "scholz", "macron", "congress"]):
        return CATEGORY_CLUSTERS["progressive_centre"]
    elif category == "geopolitics" or any(k in t_id for k in ["ukraine", "russia", "china", "taiwan", "gaza", "israel", "defense", "sanctions", "nato"]):
        return CATEGORY_CLUSTERS["geopolitics_security"]
    else:
        return CATEGORY_CLUSTERS["technology_governance"]


def build_ideological_network(min_correlation: float = 0.25, max_nodes: int = 30) -> dict[str, Any]:
    """Generate force-directed graph nodes and correlation edges for political entities."""
    catalog = load_catalog()
    topics = catalog.all_topics()[:max_nodes]

    # 1. Build nodes and collect time series
    nodes = []
    series_map: dict[str, pd.Series] = {}

    for t in topics:
        df = topic_weekly(t.id)
        if df.empty or len(df) < 5:
            continue

        tones = df["avg_tone"].to_numpy()
        latest_tone = round(float(tones[-1]), 2)
        avg_vol = int(df["article_volume"].mean()) if "article_volume" in df else 5000
        
        cluster = _assign_cluster(t.id, t.category)

        # Scale node size for graph visualization (15 to 45px)
        node_size = max(16, min(48, int(np.sqrt(avg_vol) * 0.45 + 16)))

        nodes.append({
            "id": t.id,
            "name": t.label,
            "category": t.category,
            "latest_tone": latest_tone,
            "volume": avg_vol,
            "symbolSize": node_size,
            "cluster_id": cluster["id"],
            "cluster_name": cluster["name"],
            "itemStyle": {"color": cluster["color"]},
        })

        series_map[t.label] = df.set_index("date")["avg_tone"]

    # 2. Build aligned dataframe & compute pairwise correlations
    links = []
    if len(series_map) >= 2:
        df_all = pd.DataFrame(series_map).dropna()
        corr_matrix = df_all.corr()

        labels = list(series_map.keys())
        id_lookup = {t.label: t.id for t in topics}

        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                la, lb = labels[i], labels[j]
                r_val = float(corr_matrix.loc[la, lb])
                
                if abs(r_val) >= min_correlation and not np.isnan(r_val):
                    # Positive alignment or polarized inverse
                    rel_type = "positive_alignment" if r_val > 0 else "polarized_inverse"
                    edge_width = round(float(abs(r_val) * 4.5 + 0.5), 1)

                    links.append({
                        "source": id_lookup.get(la, la),
                        "target": id_lookup.get(lb, lb),
                        "source_label": la,
                        "target_label": lb,
                        "value": round(r_val, 2),
                        "weight": edge_width,
                        "relationship": rel_type,
                        "lineStyle": {
                            "width": edge_width,
                            "color": "#38bdf8" if r_val > 0 else "#f43f5e",
                            "opacity": min(0.85, max(0.25, abs(r_val))),
                            "type": "solid" if r_val > 0 else "dashed",
                        },
                    })

    # Sort links by absolute strength
    links.sort(key=lambda x: abs(x["value"]), reverse=True)

    return {
        "nodes": nodes,
        "links": links,
        "clusters": list(CATEGORY_CLUSTERS.values()),
        "summary": {
            "node_count": len(nodes),
            "link_count": len(links),
            "min_correlation_threshold": min_correlation,
        },
    }
