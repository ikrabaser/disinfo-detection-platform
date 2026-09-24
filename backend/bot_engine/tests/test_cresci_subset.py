from pathlib import Path

import pandas as pd

from bot_engine.datasets.cresci_subset import (
    BOT_LABEL,
    HUMAN_LABEL,
    load_cresci_subset,
)
from bot_engine.features import (
    BOT_FEATURE_NAMES,
)


def _write_dataset(
    path: Path,
    rows: list[dict],
) -> None:
    pd.DataFrame(
        rows
    ).to_csv(
        path,
        index=False,
    )


def test_load_cresci_subset(
    tmp_path,
):
    common = {
        "name": "Example User",
        "statuses_count": 1000,
        "followers_count": 100,
        "friends_count": 50,
        "listed_count": 2,
        "verified": False,
        "description": "example description",
        "created_at":
            "Tue Mar 17 08:51:12 +0000 2009",
        "crawled_at":
            "2016-03-15 14:12:22",
    }

    _write_dataset(
        tmp_path
        / "genuine_users.csv",
        [
            {
                **common,
                "id": "human-1",
                "screen_name":
                    "human_user",
            }
        ],
    )

    _write_dataset(
        tmp_path
        / "spam_users.csv",
        [
            {
                **common,
                "id": "bot-1",
                "screen_name":
                    "bot123456",
                "statuses_count":
                    50000,
            }
        ],
    )

    dataset = (
        load_cresci_subset(
            tmp_path
        )
    )

    assert dataset.X.shape == (
        2,
        len(
            BOT_FEATURE_NAMES
        ),
    )

    assert set(
        dataset.y.tolist()
    ) == {
        HUMAN_LABEL,
        BOT_LABEL,
    }

    assert dataset.user_ids == [
        "human-1",
        "bot-1",
    ]
