from starlette.testclient import TestClient
from api.main import app
from src.analytics.network import build_ideological_network, CATEGORY_CLUSTERS

client = TestClient(app)


def test_build_ideological_network():
    net = build_ideological_network(min_correlation=0.20, max_nodes=20)
    assert "nodes" in net
    assert "links" in net
    assert "clusters" in net
    assert len(net["nodes"]) > 0
    assert len(net["clusters"]) == 5

    first_node = net["nodes"][0]
    assert "id" in first_node
    assert "name" in first_node
    assert "cluster_name" in first_node
    assert "symbolSize" in first_node


def test_network_api_endpoints():
    resp = client.get("/api/network/graph?min_correlation=0.25&max_nodes=20")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "links" in data

    resp_clusters = client.get("/api/network/clusters")
    assert resp_clusters.status_code == 200
    assert len(resp_clusters.json()) == 5
