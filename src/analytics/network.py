"""Ideological Network Graph, Entity Clustering & Geopolitical Contagion Analytics."""
from __future__ import annotations

from typing import Any
from datetime import date
import numpy as np
import pandas as pd
import networkx as nx

from src.topics.catalog import load_catalog, resolve_topic
from src.topics.synth import global_weekly


COLOR_PALETTE = ["#f59e0b", "#ef4444", "#3b82f6", "#8b5cf6", "#10b981", "#ec4899", "#14b8a6", "#f97316"]


def build_ideological_network(
    min_correlation: float = 0.25,
    max_nodes: int = 35,
    include_topic_id: str | None = None,
) -> dict[str, Any]:
    """Generate force-directed graph nodes and correlation edges for political entities with algorithmic community detection."""
    catalog = load_catalog()

    if include_topic_id:
        seed = resolve_topic(include_topic_id)
        other_topics = [t for t in catalog if t.id != seed.id][:max_nodes - 1]
        topics = [seed] + other_topics
    else:
        topics = catalog[:max_nodes]

    today = date.today()
    series_map: dict[str, pd.Series] = {}
    node_metadata = {}

    for t in topics:
        df = global_weekly(t.label, end=today)
        if df.empty or len(df) < 5:
            continue

        tones = df["avg_tone"].to_numpy()
        latest_tone = round(float(tones[-1]), 2)
        avg_vol = int(df["article_volume"].mean()) if "article_volume" in df else 5000
        node_size = max(16, min(48, int(np.sqrt(avg_vol) * 0.45 + 16)))

        node_metadata[t.id] = {
            "id": t.id,
            "name": t.label,
            "category": t.category,
            "latest_tone": latest_tone,
            "volume": avg_vol,
            "symbolSize": node_size,
        }
        series_map[t.id] = df.set_index("week_start")["avg_tone"]

    # Build NetworkX graph from correlation matrix
    G = nx.Graph()
    if len(series_map) >= 2:
        df_all = pd.DataFrame(series_map).dropna()
        corr_matrix = df_all.corr()

        labels = list(series_map.keys())

        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                la, lb = labels[i], labels[j]
                r_val = float(corr_matrix.loc[la, lb])

                if abs(r_val) >= min_correlation and not np.isnan(r_val):
                    edge_width = round(float(abs(r_val) * 4.5 + 0.5), 1)
                    G.add_edge(la, lb, weight=r_val, abs_weight=abs(r_val), width=edge_width)

    # Compute node-level centrality metrics before community detection
    betweenness: dict[str, float] = {}
    eigenvector: dict[str, float] = {}
    degree_centrality: dict[str, float] = {}

    if len(G.nodes) > 0:
        try:
            betweenness = nx.betweenness_centrality(G, weight="abs_weight", normalized=True)
            betweenness = {k: round(float(v), 4) for k, v in betweenness.items()}
        except Exception:
            betweenness = {n: 0.0 for n in G.nodes}

        try:
            eigenvector = nx.eigenvector_centrality(G, weight="abs_weight", max_iter=500)
            eigenvector = {k: round(float(v), 4) for k, v in eigenvector.items()}
        except Exception:
            eigenvector = {n: 0.0 for n in G.nodes}

        degree_centrality = nx.degree_centrality(G)
        degree_centrality = {k: round(float(v), 4) for k, v in degree_centrality.items()}

    # Algorithmic Community Detection (Greedy Modularity Maximization)
    clusters = []
    node_to_cluster = {}

    if len(G.nodes) > 0:
        try:
            communities = list(nx.community.greedy_modularity_communities(G, weight="abs_weight"))
        except Exception:
            communities = [set(G.nodes)]

        for cluster_id, comm in enumerate(communities):
            color = COLOR_PALETTE[cluster_id % len(COLOR_PALETTE)]
            cluster_name = f"Emergent Cluster {cluster_id + 1}"

            # Name cluster based on most central node in it (highest degree)
            subgraph = G.subgraph(comm)
            if len(subgraph) > 0:
                central_node = max(dict(subgraph.degree(weight="abs_weight")).items(), key=lambda x: x[1])[0]
                central_label = node_metadata[central_node]["name"]
                cluster_name = f"{central_label} Axis"

            clusters.append({
                "id": cluster_id,
                "name": cluster_name,
                "color": color,
            })

            for node in comm:
                node_to_cluster[node] = {
                    "cluster_id": cluster_id,
                    "cluster_name": cluster_name,
                    "color": color
                }

    # Add isolated nodes to a default cluster
    nodes = []
    for nid, data in node_metadata.items():
        if nid not in node_to_cluster:
            node_to_cluster[nid] = {
                "cluster_id": 99,
                "cluster_name": "Isolated Nodes",
                "color": "#94a3b8"
            }
            if not any(c["id"] == 99 for c in clusters):
                clusters.append({"id": 99, "name": "Isolated Nodes", "color": "#94a3b8"})

        c_info = node_to_cluster[nid]
        nodes.append({
            **data,
            "cluster_id": c_info["cluster_id"],
            "cluster_name": c_info["cluster_name"],
            "betweenness_centrality": betweenness.get(nid, 0.0),
            "eigenvector_centrality": eigenvector.get(nid, 0.0),
            "degree_centrality": degree_centrality.get(nid, 0.0),
            "itemStyle": {"color": c_info["color"]},
        })

    links = []
    for u, v, data in G.edges(data=True):
        r_val = data["weight"]
        rel_type = "positive_alignment" if r_val > 0 else "polarized_inverse"
        links.append({
            "source": u,
            "target": v,
            "source_label": node_metadata[u]["name"],
            "target_label": node_metadata[v]["name"],
            "value": round(r_val, 2),
            "weight": data["width"],
            "relationship": rel_type,
            "lineStyle": {
                "width": data["width"],
                "color": "#38bdf8" if r_val > 0 else "#f43f5e",
                "opacity": min(0.85, max(0.25, abs(r_val))),
                "type": "solid" if r_val > 0 else "dashed",
            },
        })

    links.sort(key=lambda x: abs(x["value"]), reverse=True)

    return {
        "nodes": nodes,
        "links": links,
        "clusters": clusters,
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
    """Simulate epidemiological (SIR) narrative shock transmission across network nodes."""
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

    adj: dict[str, list[dict[str, Any]]] = {}
    for l in network["links"]:
        s, t, w = l["source"], l["target"], l["value"]
        adj.setdefault(s, []).append({"neighbor": t, "weight": w})
        adj.setdefault(t, []).append({"neighbor": s, "weight": w})

    steps_data = []

    # State tracking
    infected_nodes: dict[str, float] = {seed_node["id"]: shock_magnitude}
    recovered_nodes: set[str] = set()

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

    recovered_nodes.add(seed_node["id"])
    current_wave = {seed_node["id"]: shock_magnitude}
    # Use a module-local RNG (default_rng) rather than the global np.random state
    # to avoid cross-contaminating other modules that rely on seeded state.
    rng = np.random.default_rng(42)

    for step_num in range(1, max_steps + 1):
        next_wave: dict[str, float] = {}
        wave_details = []

        for curr_id, curr_shock in current_wave.items():
            neighbors = adj.get(curr_id, [])
            for n_info in neighbors:
                n_id = n_info["neighbor"]
                r_weight = n_info["weight"]

                if n_id in infected_nodes or n_id in recovered_nodes:
                    continue

                # Stochastic SIR Infection Probability
                infection_prob = min(0.95, max(0.05, abs(r_weight) * 1.5))
                is_infected = rng.random() < infection_prob

                if is_infected:
                    transmitted_shock = curr_shock * r_weight * attenuation
                    if abs(transmitted_shock) >= 0.10:
                        next_wave[n_id] = transmitted_shock
                        infected_nodes[n_id] = transmitted_shock

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

        # Move current wave to recovered (cannot be re-infected)
        for curr_id in current_wave.keys():
            recovered_nodes.add(curr_id)

        wave_details.sort(key=lambda x: abs(x["delta"]), reverse=True)
        steps_data.append({
            "step": step_num,
            "description": f"Wave {step_num}: Stochastic SIR contagion infected {len(wave_details)} nodes (attenuation {attenuation:.0%}).",
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
