from __future__ import annotations

from typing import Any

from external.x_client import get_x_api_client
from graph_engine.graph_builder import (
    build_propagation_graph,
    graph_to_dict,
)
from graph_engine.models import PropagationGraph
from nlp_engine.text_classifier import TextClassifier


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


def analyze_social_posts(
    posts: list[dict[str, Any]],
) -> dict[str, Any]:
    classifier = TextClassifier()

    analyzed_posts: list[dict[str, Any]] = []

    label_counts = {
        "gercek": 0,
        "belirsiz": 0,
        "sahte": 0,
    }

    confidences: list[float] = []

    for post in posts:
        text = str(post.get("text", ""))

        result = classifier.classify(text)

        label_counts[result.label] = (
            label_counts.get(result.label, 0) + 1
        )

        confidences.append(result.confidence)

        analyzed_posts.append(
            {
                **post,
                "nlp_label": result.label,
                "nlp_confidence": round(
                    result.confidence,
                    3,
                ),
                "nlp_scores": result.scores,
                "nlp_engine": classifier.engine_name,
            }
        )

    total = len(analyzed_posts)

    suspicious_count = (
        label_counts["sahte"]
        + label_counts["belirsiz"]
    )

    suspicious_ratio = (
        suspicious_count / total
        if total
        else 0.0
    )

    average_confidence = (
        sum(confidences) / len(confidences)
        if confidences
        else 0.0
    )

    summary = {
        "engine": classifier.engine_name,
        "total": total,
        "labels": label_counts,
        "suspicious_count": suspicious_count,
        "suspicious_ratio": round(
            suspicious_ratio,
            3,
        ),
        "average_confidence": round(
            average_confidence,
            3,
        ),
    }

    return {
        "posts": analyzed_posts,
        "summary": summary,
    }


def build_social_graph(
    posts: list[dict[str, Any]],
) -> dict[str, Any]:
    graph = build_propagation_graph(posts)
    raw_graph = graph_to_dict(graph)

    post_lookup = {
        str(post["id"]): post
        for post in posts
    }

    nodes = []

    for node in raw_graph["nodes"]:
        post = post_lookup.get(
            str(node["id"]),
            {},
        )

        attrs = dict(node["attrs"])

        attrs.update(
            {
                "text": post.get("text"),
                "created_at": post.get("created_at"),
                "author_username": post.get(
                    "author_username"
                ),
                "nlp_label": post.get("nlp_label"),
                "nlp_confidence": post.get(
                    "nlp_confidence"
                ),
                "nlp_scores": post.get("nlp_scores"),
                "nlp_engine": post.get("nlp_engine"),
                "like_count": post.get("like_count", 0),
                "retweet_count": post.get("retweet_count", 0),
                "reply_count": post.get("reply_count", 0),
                "quote_count": post.get("quote_count", 0),
                "author_followers_count": post.get(
                    "author_followers_count",
                    0,
                ),
                "author_following_count": post.get(
                    "author_following_count",
                    0,
                ),
                "author_post_count": post.get(
                    "author_post_count",
                    0,
                ),
                "author_verified": post.get(
                    "author_verified",
                    False,
                ),
            }
        )

        nodes.append(
            {
                "id": node["id"],
                "type": attrs.get(
                    "type",
                    "post",
                ),
                "attrs": attrs,
            }
        )

    edges = [
        {
            "source": edge["source"],
            "target": edge["target"],
            "type": edge["attrs"].get(
                "type",
                "share",
            ),
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


def summarize_graph_nlp(
    nodes: list[dict[str, Any]],
) -> dict[str, Any]:
    label_counts = {
        "gercek": 0,
        "belirsiz": 0,
        "sahte": 0,
    }

    confidences = []

    for node in nodes:
        attrs = node.get("attrs") or {}

        label = attrs.get("nlp_label")
        confidence = attrs.get("nlp_confidence")

        if label in label_counts:
            label_counts[label] += 1

        if isinstance(
            confidence,
            (int, float),
        ):
            confidences.append(
                float(confidence)
            )

    total = sum(label_counts.values())

    suspicious_count = (
        label_counts["sahte"]
        + label_counts["belirsiz"]
    )

    engines = {
        (node.get("attrs") or {}).get("nlp_engine")
        for node in nodes
        if (node.get("attrs") or {}).get("nlp_engine")
    }

    engine = (
        next(iter(engines))
        if len(engines) == 1
        else "unknown"
    )

    return {
        "engine": engine,
        "total": total,
        "labels": label_counts,
        "suspicious_count": suspicious_count,
        "suspicious_ratio": round(
            suspicious_count / total,
            3,
        )
        if total
        else 0.0,
        "average_confidence": round(
            sum(confidences) / len(confidences),
            3,
        )
        if confidences
        else 0.0,
    }


def ingest_social_query(
    query: str,
    max_results: int = 10,
) -> dict[str, Any]:
    social_data = fetch_social_posts(
        query=query,
        max_results=max_results,
    )

    nlp_data = analyze_social_posts(
        social_data["posts"],
    )

    graph_data = build_social_graph(
        nlp_data["posts"],
    )

    propagation_graph = (
        PropagationGraph.objects.create(
            source_analysis_query=query,
            node_count=graph_data["node_count"],
            edge_count=graph_data["edge_count"],
            nodes=graph_data["nodes"],
            edges=graph_data["edges"],
        )
    )

    return {
        "source": social_data["source"],
        "query": query,
        "post_count": social_data["count"],
        "graph_id": propagation_graph.id,
        "node_count": propagation_graph.node_count,
        "edge_count": propagation_graph.edge_count,
        "posts": nlp_data["posts"],
        "graph": graph_data,
        "nlp_summary": nlp_data["summary"],
    }
