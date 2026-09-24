from __future__ import annotations

from typing import Any

import torch
from torch_geometric.data import Data
from torch_geometric.utils import to_undirected

from graph_engine.aligned_features import (
    transform_profile_features,
)
from graph_engine.structural_features import (
    build_structural_features,
)


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def propagation_graph_to_aligned_pyg(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> Data:
    if not nodes:
        raise ValueError(
            "GNN donusumu icin graph en az bir node icermeli."
        )

    node_index = {
        str(node["id"]): index
        for index, node in enumerate(nodes)
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

    if edge_pairs:
        directed_edge_index = torch.tensor(
            edge_pairs,
            dtype=torch.long,
        ).t().contiguous()
    else:
        directed_edge_index = torch.empty(
            (2, 0),
            dtype=torch.long,
        )

    profile_rows = []

    for node in nodes:
        attrs = node.get("attrs") or {}

        # UPFD original profile sirasi:
        # 0 verified
        # 1 geo_enabled
        # 2 followers_count
        # 3 friends/following_count
        # 4 statuses/post_count
        # 5 favourites_count
        # 6 listed_count
        # 7 account month
        # 8 name word count
        # 9 description word count

        profile_rows.append(
            [
                1.0
                if attrs.get("author_verified")
                else 0.0,

                0.0,

                _safe_float(
                    attrs.get(
                        "author_followers_count"
                    )
                ),

                _safe_float(
                    attrs.get(
                        "author_following_count"
                    )
                ),

                _safe_float(
                    attrs.get(
                        "author_post_count"
                    )
                ),

                0.0,

                _safe_float(
                    attrs.get(
                        "author_listed_count"
                    )
                ),

                _safe_float(
                    attrs.get(
                        "author_account_month"
                    )
                ),

                _safe_float(
                    attrs.get(
                        "author_name_word_count"
                    )
                ),

                _safe_float(
                    attrs.get(
                        "author_description_word_count"
                    )
                ),
            ]
        )

    raw_profile_x = torch.tensor(
        profile_rows,
        dtype=torch.float32,
    )

    profile_x = transform_profile_features(
        raw_profile_x
    )

    structural_x = build_structural_features(
        edge_index=directed_edge_index,
        num_nodes=len(nodes),
    )

    x = torch.cat(
        [
            profile_x,
            structural_x,
        ],
        dim=1,
    )

    edge_index = to_undirected(
        directed_edge_index,
        num_nodes=len(nodes),
    )

    return Data(
        x=x,
        edge_index=edge_index,
        node_ids=[
            str(node["id"])
            for node in nodes
        ],
    )
