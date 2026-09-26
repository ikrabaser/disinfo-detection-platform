"""Agent tool: get_analysis_result."""

from typing import Any

from agent.tools.permissions import (
    tool_permission,
)


def _as_result(
    value: Any,
) -> dict:
    if isinstance(
        value,
        dict,
    ):
        return value

    return {}


def _string_id(
    value: Any,
) -> str | None:
    if value is None:
        return None

    return str(value)


def _build_model_freshness(
    stored_result: Any,
    *,
    current_model: str,
    current_feature_set: str,
    current_graph_id: int | None,
    recommended_tool: str,
) -> dict:
    """
    Stored model sonucunun mevcut runtime modeliyle
    uyumunu metadata uzerinden degerlendirir.

    Bu timestamp tabanli kesin freshness degildir;
    model / feature-set / graph provenance kontroludur.
    """

    stored = _as_result(
        stored_result
    )

    stored_present = bool(
        stored
    )

    current_graph = _string_id(
        current_graph_id
    )

    stored_model = stored.get(
        "model"
    )

    stored_feature_set = stored.get(
        "feature_set"
    )

    stored_graph = _string_id(
        stored.get(
            "graph_id"
        )
    )

    model_matches = (
        stored_model
        == current_model
        if stored_model is not None
        else None
    )

    feature_set_matches = (
        stored_feature_set
        == current_feature_set
        if stored_feature_set
        is not None
        else None
    )

    graph_matches = (
        stored_graph
        == current_graph
        if (
            stored_graph is not None
            and current_graph
            is not None
        )
        else None
    )

    reasons: list[str] = []

    refresh_possible = (
        current_graph
        is not None
    )

    if not stored_present:
        status = "missing"

        reasons.append(
            "stored_result_missing"
        )

        refresh_recommended = (
            refresh_possible
        )

    elif current_graph is None:
        status = "unverifiable"

        reasons.append(
            "analysis_has_no_current_"
            "propagation_graph"
        )

        refresh_recommended = False

    else:
        missing_metadata = []

        if stored_model is None:
            missing_metadata.append(
                "model"
            )

        if stored_feature_set is None:
            missing_metadata.append(
                "feature_set"
            )

        if stored_graph is None:
            missing_metadata.append(
                "graph_id"
            )

        mismatches = []

        if model_matches is False:
            mismatches.append(
                "model_changed"
            )

        if (
            feature_set_matches
            is False
        ):
            mismatches.append(
                "feature_set_changed"
            )

        if graph_matches is False:
            mismatches.append(
                "graph_changed"
            )

        if mismatches:
            status = "stale"

            reasons.extend(
                mismatches
            )

            refresh_recommended = True

        elif missing_metadata:
            status = "legacy_schema"

            reasons.extend(
                (
                    "missing_provenance:"
                    + item
                )
                for item
                in missing_metadata
            )

            refresh_recommended = True

        else:
            status = "current"

            reasons.append(
                "stored_provenance_matches_"
                "current_runtime"
            )

            refresh_recommended = False

    return {
        "status":
            status,

        "stored_result_present":
            stored_present,

        "stored_model":
            stored_model,

        "current_model":
            current_model,

        "model_matches":
            model_matches,

        "stored_feature_set":
            stored_feature_set,

        "current_feature_set":
            current_feature_set,

        "feature_set_matches":
            feature_set_matches,

        "stored_graph_id":
            stored_graph,

        "current_graph_id":
            current_graph,

        "graph_matches":
            graph_matches,

        "refresh_possible":
            refresh_possible,

        "refresh_recommended":
            refresh_recommended,

        "recommended_tool": (
            recommended_tool
            if refresh_recommended
            else None
        ),

        "reasons":
            reasons,
    }


@tool_permission(
    roles={
        "admin",
        "analyst",
        "viewer",
    }
)
def get_analysis_result(
    analysis_id: int,
) -> dict:
    """
    Analiz sonucunu model freshness metadata'siyla getirir.

    Args:
        analysis_id:
            analyses.models.Analysis PK degeri.

    Returns:
        Serialize edilmis Analysis kaydi ve
        model_freshness metadata'si.
    """

    # Lazy imports:
    # Django app registry ve agir ML importlarini
    # module import zamaninda tetiklememek icin.
    from analyses.models import Analysis
    from analyses.serializers import (
        AnalysisSerializer,
    )

    from bot_engine.inference import (
        FEATURE_SET as BOT_FEATURE_SET,
        MODEL_NAME as BOT_MODEL_NAME,
    )

    from graph_engine.inference import (
        FEATURE_SET as GNN_FEATURE_SET,
        MODEL_NAME as GNN_MODEL_NAME,
    )

    try:
        analysis = (
            Analysis.objects
            .select_related(
                "propagation_graph"
            )
            .get(
                pk=analysis_id
            )
        )

    except Analysis.DoesNotExist:
        return {
            "error": (
                "Analysis "
                f"id={analysis_id} "
                "bulunamadi."
            )
        }

    payload = dict(
        AnalysisSerializer(
            analysis
        ).data
    )

    gnn_freshness = (
        _build_model_freshness(
            analysis.gnn_result,
            current_model=
                GNN_MODEL_NAME,
            current_feature_set=
                GNN_FEATURE_SET,
            current_graph_id=
                analysis
                .propagation_graph_id,
            recommended_tool=
                "run_gnn_analysis",
        )
    )

    bot_freshness = (
        _build_model_freshness(
            analysis
            .bot_analysis_result,
            current_model=
                BOT_MODEL_NAME,
            current_feature_set=
                BOT_FEATURE_SET,
            current_graph_id=
                analysis
                .propagation_graph_id,
            recommended_tool=
                "run_bot_analysis",
        )
    )

    # Eski GNN kayitlarinda edge_count,
    # original propagation graph edge sayisi
    # yerine undirected PyG model edge sayisini
    # temsil edebiliyordu.
    graph = (
        analysis.propagation_graph
    )

    stored_gnn = _as_result(
        analysis.gnn_result
    )

    if (
        graph is not None
        and stored_gnn
        and "edge_count"
        in stored_gnn
        and "model_edge_count"
        not in stored_gnn
    ):
        original_edge_count = len(
            graph.edges or []
        )

        stored_edge_count = (
            stored_gnn.get(
                "edge_count"
            )
        )

        if (
            stored_edge_count
            != original_edge_count
        ):
            gnn_freshness[
                "schema_status"
            ] = (
                "legacy_edge_count_"
                "semantics"
            )

            gnn_freshness[
                "schema_note"
            ] = (
                "Stored edge_count, "
                "original propagation "
                "graph edge sayisi yerine "
                "modelin undirected PyG "
                "edge sayisini temsil "
                "ediyor olabilir."
            )

            gnn_freshness[
                "original_graph_edge_count"
            ] = original_edge_count

            gnn_freshness[
                "stored_edge_count"
            ] = stored_edge_count

        else:
            gnn_freshness[
                "schema_status"
            ] = "current"

    else:
        gnn_freshness[
            "schema_status"
        ] = "current"

    payload[
        "model_freshness"
    ] = {
        "basis": (
            "stored model, feature-set "
            "and graph provenance"
        ),

        "per_result_timestamp_available":
            False,

        "timestamp_note": (
            "Analysis modelinde GNN ve "
            "bot sonuclari icin ayri "
            "generated_at alanlari "
            "bulunmuyor. Bu nedenle "
            "freshness metadata/provenance "
            "tabanli hesaplanir."
        ),

        "gnn":
            gnn_freshness,

        "bot":
            bot_freshness,
    }

    return payload
