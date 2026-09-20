from __future__ import annotations

import math
from typing import Any


FEATURE_NAMES = [
    "nlp_gercek",
    "nlp_sahte",
    "nlp_belirsiz",
    "nlp_confidence",
    "like_count_log",
    "retweet_count_log",
    "reply_count_log",
    "quote_count_log",
    "followers_log",
    "following_log",
    "author_post_count_log",
    "author_verified",
    "in_degree",
    "out_degree",
]


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _log_feature(value: Any) -> float:
    value = max(
        0.0,
        _safe_float(value),
    )

    return math.log1p(value)


def propagation_graph_to_pyg(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
):
    try:
        import torch
        from torch_geometric.data import Data
    except ImportError as exc:
        raise ImportError(
            "PyTorch ve torch-geometric gerekli."
        ) from exc

    if not nodes:
        raise ValueError(
            "GNN dönüşümü için graph en az bir node içermeli."
        )

    node_index = {
        str(node["id"]): index
        for index, node in enumerate(nodes)
    }

    in_degree = {
        node_id: 0
        for node_id in node_index
    }

    out_degree = {
        node_id: 0
        for node_id in node_index
    }

    edge_pairs: list[list[int]] = []

    for edge in edges:
        source = str(edge["source"])
        target = str(edge["target"])

        if (
            source not in node_index
            or target not in node_index
        ):
            continue

        edge_pairs.append(
            [
                node_index[source],
                node_index[target],
            ]
        )

        out_degree[source] += 1
        in_degree[target] += 1

    feature_rows: list[list[float]] = []

    for node in nodes:
        node_id = str(node["id"])
        attrs = node.get("attrs") or {}

        nlp_scores = (
            attrs.get("nlp_scores")
            or {}
        )

        feature_rows.append(
            [
                _safe_float(
                    nlp_scores.get("gercek")
                ),
                _safe_float(
                    nlp_scores.get("sahte")
                ),
                _safe_float(
                    nlp_scores.get("belirsiz")
                ),
                _safe_float(
                    attrs.get(
                        "nlp_confidence"
                    )
                ),
                _log_feature(
                    attrs.get("like_count")
                ),
                _log_feature(
                    attrs.get(
                        "retweet_count"
                    )
                ),
                _log_feature(
                    attrs.get(
                        "reply_count"
                    )
                ),
                _log_feature(
                    attrs.get(
                        "quote_count"
                    )
                ),
                _log_feature(
                    attrs.get(
                        "author_followers_count"
                    )
                ),
                _log_feature(
                    attrs.get(
                        "author_following_count"
                    )
                ),
                _log_feature(
                    attrs.get(
                        "author_post_count"
                    )
                ),
                1.0
                if attrs.get(
                    "author_verified"
                )
                else 0.0,
                float(
                    in_degree[node_id]
                ),
                float(
                    out_degree[node_id]
                ),
            ]
        )

    x = torch.tensor(
        feature_rows,
        dtype=torch.float32,
    )

    if edge_pairs:
        edge_index = torch.tensor(
            edge_pairs,
            dtype=torch.long,
        ).t().contiguous()
    else:
        edge_index = torch.empty(
            (2, 0),
            dtype=torch.long,
        )

    return Data(
        x=x,
        edge_index=edge_index,
        node_ids=[
            str(node["id"])
            for node in nodes
        ],
    )
