"""Ideological Network Graph, Entity Clustering & Geopolitical Contagion Analytics."""
from __future__ import annotations

from typing import Any
from datetime import date
import numpy as np
import pandas as pd

from src.topics.catalog import load_catalog, resolve_topic
from src.topics.synth import global_weekly


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
    if category == "economy" or any(k in t_id for k in ["inflation", "tax", "housing", "interest", "debt", "cost_of_living"]):
        return CATEGORY_CLUSTERS["macroeconomics"]
    elif any(k in t_id for k in ["trump", "sunak", "republican", "conservative", "afd", "reform", "meloni", "milei", "bjp", "netanyahu"]):
        return CATEGORY_CLUSTERS["conservative_right"]
    elif any(k in t_id for k in ["biden", "harris", "starmer", "democrat", "labour", "scholz", "macron", "congress"]):
        return CATEGORY_CLUSTERS["progressive_centre"]
    elif category == "geopolitics" or any(k in t_id for k in ["ukraine", "russia", "china", "taiwan", "gaza", "israel", "defense", "sanctions", "nato"]):
        return CATEGORY_CLUSTERS["geopolitics_security"]
    else:
        return CATEGORY_CLUSTERS["technology_governance"]


def build_ideological_network(
    min_correlation: float = 0.25,
    max_nodes: int = 35,
    include_topic_id: str | None = None,
) -> dict[str, Any]:
    """Generate force-directed graph nodes and correlation edges for political entities."""
    catalog = load_catalog()
    
    if include_topic_id:
        seed = resolve_topic(include_topic_id)
        other_topics = [t for t in catalog if t.id != seed.id][:max_nodes - 1]
        topics = [seed] + other_topics
    else:
        topics = catalog[:max_nodes]

    today = date.today()
    nodes = []
    series_map: dict[str, pd.Series] = {}

    for t in topics:
        df = global_weekly(t.label, end=today)
        if df.empty or len(df) < 5:
            continue

        tones = df["avg_tone"].to_numpy()
        latest_tone = round(float(tones[-1]), 2)
        avg_vol = int(df["article_volume"].mean()) if "article_volume" in df else 5000
        
        cluster = _assign_cluster(t.id, t.category)
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

        series_map[t.label] = df.set_index("week_start")["avg_tone"]

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


def simulate_contagion_spread(
    seed_topic_id: str = "inflation",
    shock_magnitude: float = -3.0,
    attenuation: float = 0.65,
    max_steps: int = 3,
) -> dict[str, Any]:
    """Simulate geopolitical and sentiment narrative shock transmission across connected network nodes."""
    seed_topic = resolve_topic(seed_topic_id)
    network = build_ideological_network(min_correlation=0.15, max_nodes=40, include_topic_id=seed_topic.id)
    
    node_map = {n["id"]: n for n in network["nodes"]}
    seed_node = node_map.get(seed_topic.id)
    
    if not seed_node:
        seed_node = {
            "id": seed_topic.id,
            "name": seed_topic.label,
            "latest_tone": 0.0,
            "cluster_name": "General",
        }

    # Build adjacency mapping with correlation weights
    adj: dict[str, list[dict[str, Any]]] = {}
    for l in network["links"]:
        s, t, w = l["source"], l["target"], l["value"]
        adj.setdefault(s, []).append({"neighbor": t, "weight": w})
        adj.setdefault(t, []).append({"neighbor": s, "weight": w})

    steps_data = []
    affected_nodes_global: dict[str, float] = {seed_node["id"]: shock_magnitude}

    # Step 0: Epicenter shock
    steps_data.append({
        "step": 0,
        "description": f"Initial shock origin at epicenter '{seed_node['name']}' with magnitude {shock_magnitude:+.2f} tone.",
        "affected_nodes": [
            {
                "id": seed_node["id"],
                "label": seed_node["name"],
                "cluster_name": seed_node.get("cluster_name", "General"),
                "pre_shock_tone": seed_node["latest_tone"],
                "post_shock_tone": round(seed_node["latest_tone"] + shock_magnitude, 2),
                "delta": round(shock_magnitude, 2),
                "correlation_weight": 1.0,
            }
        ],
    })

    # Step 1 to N: Propagation waves
    current_wave = {seed_node["id"]: shock_magnitude}
    for step_num in range(1, max_steps + 1):
        next_wave: dict[str, float] = {}
        wave_details = []

        for curr_id, curr_shock in current_wave.items():
            neighbors = adj.get(curr_id, [])
            for n_info in neighbors:
                n_id = n_info["neighbor"]
                r_weight = n_info["weight"]

                if n_id in affected_nodes_global:
                    continue

                transmitted_shock = curr_shock * r_weight * (attenuation ** step_num)
                if abs(transmitted_shock) >= 0.15:
                    next_wave[n_id] = transmitted_shock
                    affected_nodes_global[n_id] = transmitted_shock
                    
                    target_n = node_map.get(n_id, {"name": n_id, "latest_tone": 0.0, "cluster_name": "General"})
                    wave_details.append({
                        "id": n_id,
                        "label": target_n["name"],
                        "cluster_name": target_n.get("cluster_name", "General"),
                        "pre_shock_tone": target_n["latest_tone"],
                        "post_shock_tone": round(target_n["latest_tone"] + transmitted_shock, 2),
                        "delta": round(transmitted_shock, 2),
                        "correlation_weight": round(r_weight, 2),
                    })

        if not wave_details:
            break

        wave_details.sort(key=lambda x: abs(x["delta"]), reverse=True)
        steps_data.append({
            "step": step_num,
            "description": f"Wave {step_num}: Contagion transmitted to {len(wave_details)} adjacent nodes (attenuation rate {attenuation:.0%}).",
            "affected_nodes": wave_details,
        })
        current_wave = next_wave

    return {
        "seed_topic": seed_node["id"],
        "seed_label": seed_node["name"],
        "shock_magnitude": shock_magnitude,
        "attenuation_rate": attenuation,
        "steps": steps_data,
    }
