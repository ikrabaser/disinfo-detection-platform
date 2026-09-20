from __future__ import annotations

from typing import Any

from external.x_client import get_x_api_client
from graph_engine.graph_builder import build_propagation_graph, graph_to_dict
from graph_engine.models import PropagationGraph


def fetch_social_posts(
    query: str,
    max_results: int = 10,
) -> dict[str, Any]:
    query = query.strip()

    if not query:
        raise ValueError("Arama sorgusu boş olamaz.")

    max_results = max(1, min(int(max_results), 100))

    client = get_x_api_client()

    posts = client.search_recent_posts(
        query=query,
        max_results=max_results,
    )

    source = (
        "mock"
        if client.__class__.__name__.lower().startswith("mock")
        else "x"
    )

    return {
        "source": source,
        "query": query,
        "count": len(posts),
        "posts": posts,
    }


def build_social_graph(
    posts: list[dict[str, Any]],
) -> dict[str, Any]:
    graph = build_propagation_graph(posts)
    raw_graph = graph_to_dict(graph)

    nodes = [
        {
            "id": node["id"],
            "type": node["attrs"].get("type", "post"),
            "attrs": node["attrs"],
        }
        for node in raw_graph["nodes"]
    ]

    edges = [
        {
            "source": edge["source"],
            "target": edge["target"],
            "type": edge["attrs"].get("type", "share"),
            "attrs": edge["attrs"],
        }
        for edge in raw_graph["edges"]
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def ingest_social_query(
    query: str,
    max_results: int = 10,
) -> dict[str, Any]:
    social_data = fetch_social_posts(
        query=query,
        max_results=max_results,
    )

    graph_data = build_social_graph(
        social_data["posts"],
    )

    propagation_graph = PropagationGraph.objects.create(
        source_analysis_query=query,
        node_count=graph_data["node_count"],
        edge_count=graph_data["edge_count"],
        nodes=graph_data["nodes"],
        edges=graph_data["edges"],
    )

    return {
        "source": social_data["source"],
        "query": query,
        "post_count": social_data["count"],
        "graph_id": propagation_graph.id,
        "node_count": propagation_graph.node_count,
        "edge_count": propagation_graph.edge_count,
        "posts": social_data["posts"],
        "graph": graph_data,
    }
