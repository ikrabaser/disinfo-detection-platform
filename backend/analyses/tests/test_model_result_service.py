import pytest

from analyses.model_result_service import (
    persist_model_result,
)
from analyses.models import (
    Analysis,
    AnalysisModelRun,
    AnalysisModelRunKind,
    AnalysisModelRunSource,
)


@pytest.mark.django_db
def test_model_result_updates_snapshot_and_creates_history():
    analysis = Analysis.objects.create(
        claim_text="History test",
    )

    result = {
        "model":
            "test-gnn",
        "feature_set":
            "test-features",
        "graph_id":
            "12",
        "cross_domain":
            True,
        "predicted_label":
            "real",
    }

    run = persist_model_result(
        analysis=analysis,
        kind=
            AnalysisModelRunKind.GNN,
        source=
            AnalysisModelRunSource
            .AGENT_TOOL,
        result=result,
        artifact_ref=
            "models/test.pt",
    )

    analysis.refresh_from_db()

    assert (
        analysis.gnn_result
        == result
    )

    assert (
        run.analysis_id
        == analysis.id
    )

    assert (
        run.model_name
        == "test-gnn"
    )

    assert (
        run.feature_set
        == "test-features"
    )

    assert (
        run.graph_id_snapshot
        == 12
    )

    assert (
        run.cross_domain
        is True
    )

    assert (
        run.source
        == AnalysisModelRunSource
        .AGENT_TOOL
    )


@pytest.mark.django_db
def test_first_overwrite_preserves_legacy_snapshot():
    analysis = Analysis.objects.create(
        claim_text="Legacy bot test",
        bot_analysis_result={
            "flagged_users": [
                "legacy-user",
            ],
            "scores": {
                "legacy-user":
                    0.97,
            },
        },
    )

    current_result = {
        "model":
            "random-forest-current",
        "feature_set":
            "profile-13d",
        "graph_id":
            "12",
        "flagged_count":
            0,
        "scores": {
            "legacy-user":
                0.0,
        },
    }

    persist_model_result(
        analysis=analysis,
        kind=
            AnalysisModelRunKind.BOT,
        source=
            AnalysisModelRunSource
            .AGENT_TOOL,
        result=current_result,
    )

    analysis.refresh_from_db()

    runs = list(
        AnalysisModelRun.objects
        .filter(
            analysis=analysis,
            kind=
                AnalysisModelRunKind.BOT,
        )
        .order_by("id")
    )

    assert len(runs) == 2

    assert (
        runs[0].source
        == AnalysisModelRunSource
        .LEGACY_IMPORT
    )

    assert (
        runs[0].result[
            "scores"
        ][
            "legacy-user"
        ]
        == 0.97
    )

    assert (
        runs[1].source
        == AnalysisModelRunSource
        .AGENT_TOOL
    )

    assert (
        analysis
        .bot_analysis_result
        == current_result
    )


@pytest.mark.django_db
def test_later_runs_append_without_duplicate_legacy_import():
    analysis = Analysis.objects.create(
        claim_text="Multiple runs",
    )

    for score in (
        0.2,
        0.8,
    ):
        persist_model_result(
            analysis=analysis,
            kind=
                AnalysisModelRunKind.BOT,
            source=
                AnalysisModelRunSource
                .PIPELINE,
            result={
                "model":
                    "bot-model",
                "feature_set":
                    "profile-13d",
                "graph_id":
                    "5",
                "average_bot_score":
                    score,
            },
        )

    runs = (
        AnalysisModelRun.objects
        .filter(
            analysis=analysis,
            kind=
                AnalysisModelRunKind.BOT,
        )
    )

    assert runs.count() == 2

    assert (
        runs.filter(
            source=
                AnalysisModelRunSource
                .LEGACY_IMPORT
        ).count()
        == 0
    )

    analysis.refresh_from_db()

    assert (
        analysis
        .bot_analysis_result[
            "average_bot_score"
        ]
        == 0.8
    )
