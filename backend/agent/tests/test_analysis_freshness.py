import pytest

from analyses.models import Analysis
from agent.tools.get_analysis_result import (
    _build_model_freshness,
    get_analysis_result,
)


def test_current_model_result_does_not_require_refresh():
    result = _build_model_freshness(
        {
            "model":
                "current-model",
            "feature_set":
                "current-features",
            "graph_id":
                "12",
        },
        current_model=
            "current-model",
        current_feature_set=
            "current-features",
        current_graph_id=12,
        recommended_tool=
            "run_gnn_analysis",
    )

    assert (
        result["status"]
        == "current"
    )

    assert (
        result[
            "refresh_recommended"
        ]
        is False
    )

    assert (
        result[
            "recommended_tool"
        ]
        is None
    )


def test_legacy_result_recommends_refresh():
    result = _build_model_freshness(
        {
            "scores": {
                "user-1": 0.9,
            },
        },
        current_model=
            "random-forest-current",
        current_feature_set=
            "profile-13d",
        current_graph_id=12,
        recommended_tool=
            "run_bot_analysis",
    )

    assert (
        result["status"]
        == "legacy_schema"
    )

    assert (
        result[
            "refresh_recommended"
        ]
        is True
    )

    assert (
        result[
            "recommended_tool"
        ]
        == "run_bot_analysis"
    )


def test_changed_model_is_stale():
    result = _build_model_freshness(
        {
            "model":
                "old-model",
            "feature_set":
                "profile-13d",
            "graph_id":
                "12",
        },
        current_model=
            "new-model",
        current_feature_set=
            "profile-13d",
        current_graph_id=12,
        recommended_tool=
            "run_bot_analysis",
    )

    assert (
        result["status"]
        == "stale"
    )

    assert (
        "model_changed"
        in result["reasons"]
    )

    assert (
        result[
            "refresh_recommended"
        ]
        is True
    )


@pytest.mark.django_db
def test_get_analysis_result_includes_freshness_metadata():
    analysis = Analysis.objects.create(
        claim_text=(
            "Freshness metadata test"
        ),
    )

    result = get_analysis_result(
        analysis.id
    )

    assert (
        result["id"]
        == analysis.id
    )

    assert (
        "model_freshness"
        in result
    )

    metadata = result[
        "model_freshness"
    ]

    assert (
        metadata[
            "per_result_timestamp_available"
        ]
        is False
    )

    assert "gnn" in metadata
    assert "bot" in metadata
