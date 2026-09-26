from __future__ import annotations

from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import transaction

from analyses.models import (
    Analysis,
    AnalysisModelRun,
    AnalysisModelRunKind,
    AnalysisModelRunSource,
)
from bot_engine import inference as bot_inference
from graph_engine.inference import (
    DEFAULT_CHECKPOINT as
        GNN_DEFAULT_CHECKPOINT,
)
from graph_engine.inference import (
    predict_propagation_graph,
)


SNAPSHOT_FIELDS = {
    AnalysisModelRunKind.GNN:
        "gnn_result",
    AnalysisModelRunKind.BOT:
        "bot_analysis_result",
}


def _as_dict(
    value: Any,
) -> dict:
    if isinstance(
        value,
        dict,
    ):
        return dict(value)

    return {}


def _graph_id(
    value: Any,
) -> int | None:
    if value in {
        None,
        "",
    }:
        return None

    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def _artifact_ref(
    path: Any,
) -> str:
    if not path:
        return ""

    candidate = Path(path)

    try:
        return str(
            candidate.resolve().relative_to(
                Path(
                    settings.BASE_DIR
                ).resolve()
            )
        )

    except (
        ValueError,
        OSError,
    ):
        return str(candidate)


def _create_history_run(
    *,
    analysis: Analysis,
    kind: str,
    source: str,
    result: dict,
    artifact_ref: str = "",
) -> AnalysisModelRun:
    return (
        AnalysisModelRun.objects.create(
            analysis=analysis,
            kind=kind,
            source=source,
            model_name=str(
                result.get(
                    "model"
                )
                or ""
            ),
            feature_set=str(
                result.get(
                    "feature_set"
                )
                or ""
            ),
            graph_id_snapshot=(
                _graph_id(
                    result.get(
                        "graph_id"
                    )
                )
                or analysis
                .propagation_graph_id
            ),
            artifact_ref=(
                artifact_ref
            ),
            result=result,
            cross_domain=bool(
                result.get(
                    "cross_domain",
                    False,
                )
            ),
        )
    )


@transaction.atomic
def persist_model_result(
    *,
    analysis: Analysis,
    kind: str,
    source: str,
    result: dict,
    artifact_ref: str = "",
) -> AnalysisModelRun:
    """
    Model sonucunu current snapshot'a
    yazar ve immutable history kaydi
    olusturur.

    History sistemi eklenmeden onceki
    snapshot ilk overwrite oncesinde
    legacy_import olarak korunur.
    """

    if analysis.pk is None:
        raise ValueError(
            "Analysis kaydedilmis "
            "olmali."
        )

    snapshot_field = (
        SNAPSHOT_FIELDS.get(
            kind
        )
    )

    if snapshot_field is None:
        raise ValueError(
            "Desteklenmeyen model "
            f"run kind: {kind}"
        )

    payload = _as_dict(
        result
    )

    existing_snapshot = (
        _as_dict(
            getattr(
                analysis,
                snapshot_field,
                None,
            )
        )
    )

    has_history = (
        AnalysisModelRun.objects
        .filter(
            analysis=analysis,
            kind=kind,
        )
        .exists()
    )

    if (
        existing_snapshot
        and not has_history
    ):
        _create_history_run(
            analysis=analysis,
            kind=kind,
            source=(
                AnalysisModelRunSource
                .LEGACY_IMPORT
            ),
            result=
                existing_snapshot,
        )

    setattr(
        analysis,
        snapshot_field,
        payload,
    )

    analysis.save(
        update_fields=[
            snapshot_field,
            "updated_at",
        ]
    )

    return _create_history_run(
        analysis=analysis,
        kind=kind,
        source=source,
        result=payload,
        artifact_ref=artifact_ref,
    )


def run_and_record_gnn_analysis(
    *,
    analysis: Analysis,
    source: str,
) -> dict:
    graph = (
        analysis.propagation_graph
    )

    if graph is None:
        raise ValueError(
            "Bu Analysis kaydina "
            "bagli propagation graph "
            "bulunmuyor."
        )

    raw_result = (
        predict_propagation_graph(
            graph
        )
    )

    model_edge_count = (
        raw_result.get(
            "edge_count"
        )
    )

    result = {
        "analysis_id":
            analysis.pk,
        **raw_result,
        "edge_count":
            len(
                graph.edges
                or []
            ),
        "model_edge_count":
            model_edge_count,
    }

    persist_model_result(
        analysis=analysis,
        kind=(
            AnalysisModelRunKind.GNN
        ),
        source=source,
        result=result,
        artifact_ref=_artifact_ref(
            GNN_DEFAULT_CHECKPOINT
        ),
    )

    return result


def run_and_record_bot_analysis(
    *,
    analysis: Analysis,
    source: str,
) -> dict:
    graph = (
        analysis.propagation_graph
    )

    if graph is None:
        raise ValueError(
            "Bu Analysis kaydina "
            "bagli propagation graph "
            "bulunmuyor."
        )

    raw_result = (
        bot_inference
        .predict_graph_users(
            graph.nodes
        )
    )

    result = {
        "analysis_id":
            analysis.pk,
        "graph_id":
            str(graph.pk),
        **raw_result,
    }

    persist_model_result(
        analysis=analysis,
        kind=(
            AnalysisModelRunKind.BOT
        ),
        source=source,
        result=result,
        artifact_ref=_artifact_ref(
            bot_inference
            .DEFAULT_CHECKPOINT
        ),
    )

    return result
