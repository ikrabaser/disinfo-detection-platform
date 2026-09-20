from __future__ import annotations

import torch
from torch_geometric.utils import to_undirected

from graph_engine.structural_features import (
    STRUCTURAL_FEATURE_NAMES,
    build_structural_features,
)


ALIGNED_PROFILE_FEATURE_NAMES = [
    "verified",
    "followers_log",
    "following_log",
    "posts_log",
    "listed_log",
    "account_month_log",
    "name_words_log",
    "description_words_log",
]

ALIGNED_FEATURE_NAMES = (
    ALIGNED_PROFILE_FEATURE_NAMES
    + STRUCTURAL_FEATURE_NAMES
)

# UPFD profile feature sırası:
# 0 verified
# 1 geo_enabled
# 2 followers_count
# 3 friends_count
# 4 statuses_count
# 5 favourites_count
# 6 listed_count
# 7 account month
# 8 name word count
# 9 description word count
PROFILE_INDICES = [
    0,
    2,
    3,
    4,
    6,
    7,
    8,
    9,
]


def transform_profile_features(x):
    selected = x[:, PROFILE_INDICES].float()

    verified = selected[:, 0:1]

    numeric = torch.clamp(
        selected[:, 1:],
        min=0.0,
    )

    numeric = torch.log1p(
        numeric
    )

    return torch.cat(
        [
            verified,
            numeric,
        ],
        dim=1,
    )


class AlignedProfileStructuralTransform:
    def __call__(self, data):
        directed_edge_index = (
            data.edge_index.clone()
        )

        profile_x = (
            transform_profile_features(
                data.x
            )
        )

        structural_x = (
            build_structural_features(
                edge_index=directed_edge_index,
                num_nodes=data.num_nodes,
            )
        )

        data.x = torch.cat(
            [
                profile_x,
                structural_x,
            ],
            dim=1,
        )

        data.edge_index = to_undirected(
            directed_edge_index,
            num_nodes=data.num_nodes,
        )

        return data
