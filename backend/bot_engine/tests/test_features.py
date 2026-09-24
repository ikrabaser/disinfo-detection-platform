import math
from datetime import (
    datetime,
    timezone,
)

import numpy as np

from bot_engine.features import (
    BOT_FEATURE_NAMES,
    build_bot_feature_vector,
    extract_bot_feature_batch,
)


def test_extract_bot_features_groups_unique_users():
    nodes = [
        {
            "id": "post-1",
            "attrs": {
                "author_id":
                    "user-a",
                "author_username":
                    "user123",
                "author_description":
                    "example profile",
                "author_created_at":
                    "2024-01-01T00:00:00Z",
                "author_followers_count":
                    1000,
                "author_following_count":
                    100,
                "author_post_count":
                    5000,
                "author_listed_count":
                    10,
                "author_name_word_count":
                    2,
                "author_description_word_count":
                    2,
                "author_verified":
                    True,
                "created_at":
                    "2025-01-01T00:00:00Z",
            },
        },
        {
            "id": "post-2",
            "attrs": {
                "author_id":
                    "user-a",
                "author_followers_count":
                    1000,
                "author_following_count":
                    100,
                "author_post_count":
                    5001,
                "created_at":
                    "2025-01-02T00:00:00Z",
            },
        },
        {
            "id": "post-3",
            "attrs": {
                "author_id":
                    "user-b",
                "author_username":
                    "human_user",
                "author_description":
                    "",
                "author_created_at":
                    "2020-01-01T00:00:00Z",
                "author_followers_count":
                    50,
                "author_following_count":
                    200,
                "author_post_count":
                    300,
                "author_listed_count":
                    0,
                "author_name_word_count":
                    2,
                "author_description_word_count":
                    0,
                "author_verified":
                    False,
                "created_at":
                    "2025-01-02T00:00:00Z",
            },
        },
    ]

    batch = (
        extract_bot_feature_batch(
            nodes
        )
    )

    assert batch.user_ids == [
        "user-a",
        "user-b",
    ]

    assert batch.matrix.shape == (
        2,
        len(
            BOT_FEATURE_NAMES
        ),
    )

    assert np.isfinite(
        batch.matrix
    ).all()


def test_feature_vector_uses_account_age_and_posting_rate():
    observed_at = datetime(
        2025,
        1,
        11,
        tzinfo=timezone.utc,
    )

    profile = {
        "author_id":
            "user-a",
        "author_username":
            "bot123",
        "author_description":
            "test profile",
        "author_created_at":
            "2025-01-01T00:00:00Z",
        "author_followers_count":
            100,
        "author_following_count":
            50,
        "author_post_count":
            100,
        "author_listed_count":
            1,
        "author_name_word_count":
            2,
        "author_description_word_count":
            2,
        "author_verified":
            False,
    }

    vector = (
        build_bot_feature_vector(
            profile,
            observed_at,
        )
    )

    index = {
        name: position
        for position, name
        in enumerate(
            BOT_FEATURE_NAMES
        )
    }

    assert math.isclose(
        float(
            vector[
                index[
                    "account_age_days_log"
                ]
            ]
        ),
        math.log1p(10),
        rel_tol=1e-5,
    )

    assert math.isclose(
        float(
            vector[
                index[
                    "posts_per_day_log"
                ]
            ]
        ),
        math.log1p(10),
        rel_tol=1e-5,
    )


def test_empty_graph_returns_empty_feature_matrix():
    batch = (
        extract_bot_feature_batch(
            []
        )
    )

    assert batch.user_ids == []

    assert batch.matrix.shape == (
        0,
        len(
            BOT_FEATURE_NAMES
        ),
    )
