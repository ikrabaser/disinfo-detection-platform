from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import numpy as np


BOT_FEATURE_NAMES = [
    "verified",
    "followers_log",
    "following_log",
    "posts_log",
    "listed_log",
    "follower_following_log_ratio",
    "account_age_days_log",
    "posts_per_day_log",
    "name_words_log",
    "description_words_log",
    "has_description",
    "username_length_log",
    "username_digit_ratio",
]


@dataclass(frozen=True)
class BotFeatureBatch:
    user_ids: list[str]
    matrix: np.ndarray
    observed_at: datetime

    @property
    def feature_count(self) -> int:
        return len(BOT_FEATURE_NAMES)

    @property
    def user_count(self) -> int:
        return len(self.user_ids)


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        number = float(value)

        if not math.isfinite(number):
            return default

        return number

    except (
        TypeError,
        ValueError,
    ):
        return default


def _parse_datetime(
    value: Any,
) -> datetime | None:
    if isinstance(
        value,
        datetime,
    ):
        parsed = value

    elif isinstance(
        value,
        str,
    ):
        try:
            parsed = datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )
        except ValueError:
            return None

    else:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.astimezone(
        timezone.utc
    )


def infer_observed_at(
    nodes: list[dict[str, Any]],
) -> datetime:
    timestamps: list[datetime] = []

    for node in nodes:
        attrs = (
            node.get("attrs")
            or {}
        )

        timestamp = _parse_datetime(
            attrs.get(
                "created_at"
            )
        )

        if timestamp:
            timestamps.append(
                timestamp
            )

    if timestamps:
        return max(
            timestamps
        )

    return datetime.now(
        timezone.utc
    )


def aggregate_author_profiles(
    nodes: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    profiles: dict[
        str,
        dict[str, Any],
    ] = {}

    numeric_fields = [
        "author_followers_count",
        "author_following_count",
        "author_post_count",
        "author_listed_count",
        "author_name_word_count",
        "author_description_word_count",
    ]

    text_fields = [
        "author_username",
        "author_description",
    ]

    for node in nodes:
        attrs = (
            node.get("attrs")
            or {}
        )

        raw_user_id = (
            attrs.get(
                "author_id"
            )
        )

        if raw_user_id in (
            None,
            "",
        ):
            continue

        user_id = str(
            raw_user_id
        )

        profile = (
            profiles.setdefault(
                user_id,
                {
                    "author_id":
                        user_id,
                    "author_verified":
                        False,
                },
            )
        )

        profile[
            "author_verified"
        ] = bool(
            profile.get(
                "author_verified",
                False,
            )
            or attrs.get(
                "author_verified",
                False,
            )
        )

        for field in numeric_fields:
            candidate = max(
                0.0,
                _safe_float(
                    attrs.get(
                        field
                    )
                ),
            )

            current = max(
                0.0,
                _safe_float(
                    profile.get(
                        field
                    )
                ),
            )

            profile[field] = max(
                current,
                candidate,
            )

        for field in text_fields:
            current = str(
                profile.get(
                    field
                )
                or ""
            ).strip()

            candidate = str(
                attrs.get(
                    field
                )
                or ""
            ).strip()

            if (
                not current
                and candidate
            ):
                profile[field] = (
                    candidate
                )

        candidate_created_at = (
            attrs.get(
                "author_created_at"
            )
        )

        candidate_date = (
            _parse_datetime(
                candidate_created_at
            )
        )

        current_created_at = (
            profile.get(
                "author_created_at"
            )
        )

        current_date = (
            _parse_datetime(
                current_created_at
            )
        )

        if (
            candidate_date
            and (
                current_date is None
                or candidate_date
                < current_date
            )
        ):
            profile[
                "author_created_at"
            ] = candidate_created_at

    return profiles


def build_bot_feature_vector(
    profile: dict[str, Any],
    observed_at: datetime,
) -> np.ndarray:
    followers = max(
        0.0,
        _safe_float(
            profile.get(
                "author_followers_count"
            )
        ),
    )

    following = max(
        0.0,
        _safe_float(
            profile.get(
                "author_following_count"
            )
        ),
    )

    posts = max(
        0.0,
        _safe_float(
            profile.get(
                "author_post_count"
            )
        ),
    )

    listed = max(
        0.0,
        _safe_float(
            profile.get(
                "author_listed_count"
            )
        ),
    )

    name_words = max(
        0.0,
        _safe_float(
            profile.get(
                "author_name_word_count"
            )
        ),
    )

    description_words = max(
        0.0,
        _safe_float(
            profile.get(
                "author_description_word_count"
            )
        ),
    )

    verified = float(
        bool(
            profile.get(
                "author_verified",
                False,
            )
        )
    )

    username = str(
        profile.get(
            "author_username"
        )
        or ""
    ).strip()

    description = str(
        profile.get(
            "author_description"
        )
        or ""
    ).strip()

    account_created_at = (
        _parse_datetime(
            profile.get(
                "author_created_at"
            )
        )
    )

    if account_created_at:
        account_age_days = max(
            1.0,
            (
                observed_at
                - account_created_at
            ).total_seconds()
            / 86400.0,
        )
    else:
        account_age_days = 0.0

    if account_age_days > 0:
        posts_per_day = (
            posts
            / account_age_days
        )
    else:
        posts_per_day = 0.0

    follower_following_ratio = (
        math.log(
            (followers + 1.0)
            / (following + 1.0)
        )
    )

    username_digit_count = sum(
        char.isdigit()
        for char in username
    )

    username_digit_ratio = (
        username_digit_count
        / len(username)
        if username
        else 0.0
    )

    has_description = float(
        bool(
            description
            or description_words > 0
        )
    )

    return np.asarray(
        [
            verified,
            math.log1p(followers),
            math.log1p(following),
            math.log1p(posts),
            math.log1p(listed),
            follower_following_ratio,
            math.log1p(
                account_age_days
            ),
            math.log1p(
                posts_per_day
            ),
            math.log1p(
                name_words
            ),
            math.log1p(
                description_words
            ),
            has_description,
            math.log1p(
                len(username)
            ),
            username_digit_ratio,
        ],
        dtype=np.float32,
    )


def extract_bot_feature_batch(
    nodes: list[dict[str, Any]],
    observed_at: datetime | None = None,
) -> BotFeatureBatch:
    resolved_observed_at = (
        observed_at
        or infer_observed_at(
            nodes
        )
    )

    profiles = (
        aggregate_author_profiles(
            nodes
        )
    )

    user_ids = sorted(
        profiles.keys()
    )

    if not user_ids:
        matrix = np.zeros(
            (
                0,
                len(
                    BOT_FEATURE_NAMES
                ),
            ),
            dtype=np.float32,
        )

    else:
        matrix = np.stack(
            [
                build_bot_feature_vector(
                    profiles[
                        user_id
                    ],
                    resolved_observed_at,
                )
                for user_id
                in user_ids
            ],
            axis=0,
        )

    return BotFeatureBatch(
        user_ids=user_ids,
        matrix=matrix,
        observed_at=(
            resolved_observed_at
        ),
    )
