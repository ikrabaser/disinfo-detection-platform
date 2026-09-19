"""
Ham paylasim (post/share) verisinden propagation graph (yayilim grafigi)
insa eden yardimci fonksiyonlar. NetworkX kullanir (agir degildir, ama yine
de lazy-import edilir ki kurulu olmadan da modul import edilebilsin).
"""
from __future__ import annotations

from typing import Any


def build_propagation_graph(posts: list[dict[str, Any]]):
    """Paylasim listesinden bir NetworkX DiGraph insa eder.

    Args:
        posts: Her biri en az {"id", "author_id", "shared_from_id"(opsiyonel)}
            iceren sozlukler listesi (bkz. agent.tools.get_social_posts mock
            verisi).

    Returns:
        networkx.DiGraph - Dugumler kullanicilar/paylasimlar, kenarlar
        paylasim/retweet iliskilerini temsil eder.

    TODO: Gercek implementasyonda, kullanicilar arasi takip iliskileri,
    zaman damgali yayilim hizi ve retweet/quote/reply ayrimi da modellenmeli.
    """
    try:
        import networkx as nx
    except ImportError as exc:
        raise ImportError(
            "networkx kurulu degil. `pip install networkx` ile kurun."
        ) from exc

    graph = nx.DiGraph()
    for post in posts:
        graph.add_node(post["id"], type="post", author_id=post.get("author_id"))
        shared_from = post.get("shared_from_id")
        if shared_from:
            graph.add_edge(shared_from, post["id"], type="share")
    return graph


def graph_to_dict(graph) -> dict[str, Any]:
    """NetworkX grafigini `PropagationGraph.nodes`/`edges` JSONField formatina cevirir."""
    nodes = [{"id": n, "attrs": dict(attrs)} for n, attrs in graph.nodes(data=True)]
    edges = [
        {"source": u, "target": v, "attrs": dict(attrs)}
        for u, v, attrs in graph.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}


def mock_propagation_graph_dict(topic: str = "ornek-konu") -> dict[str, Any]:
    """Gercek veri cekmeden, kucuk bir mock yayilim grafigi doner (test/demo icin)."""
    posts = [
        {"id": "post-1", "author_id": "user-a"},
        {"id": "post-2", "author_id": "user-b", "shared_from_id": "post-1"},
        {"id": "post-3", "author_id": "user-c", "shared_from_id": "post-1"},
        {"id": "post-4", "author_id": "user-d", "shared_from_id": "post-2"},
    ]
    graph = build_propagation_graph(posts)
    result = graph_to_dict(graph)
    result["topic"] = topic
    return result
