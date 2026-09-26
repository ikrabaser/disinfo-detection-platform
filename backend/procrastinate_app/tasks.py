from __future__ import annotations

import logging

from django.db import close_old_connections
from procrastinate.contrib.django import app

from agent.tools.run_bot_analysis import (
    run_bot_analysis,
)
from agent.tools.run_gnn_analysis import (
    run_gnn_analysis,
)
from agent.tools.run_nlp_analysis import (
    run_nlp_analysis,
)
from analyses.models import (
    Analysis,
    AnalysisStatus,
)
from ai_analysis.service import (
    run_ai_evidence_analysis,
)
from external.services import (
    ingest_social_query,
)
from graph_engine.models import (
    PropagationGraph,
)
from realtime.centrifugo_client import (
    get_centrifugo_client,
)


logger = logging.getLogger(__name__)


@app.task(queue="analysis")
def run_analysis_task(
    analysis_id: int,
) -> dict:
    """
    Bir Analysis kaydini arka planda isler.

    Akis:
        Analysis
        -> NLP
        -> propagation graph
        -> GNN
        -> bot analizi
        -> DB save
        -> realtime progress
    """

    centrifugo = get_centrifugo_client()

    try:
        analysis = Analysis.objects.get(
            pk=analysis_id
        )
    except Analysis.DoesNotExist as exc:
        raise ValueError(
            f"Analysis bulunamadi: {analysis_id}"
        ) from exc

    try:
        analysis.status = AnalysisStatus.RUNNING

        analysis.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        centrifugo.publish_analysis_progress(
            analysis_id,
            stage="started",
            progress=0.05,
        )

        # --------------------------------------------------
        # NLP
        # --------------------------------------------------
        centrifugo.publish_analysis_progress(
            analysis_id,
            stage="nlp",
            progress=0.15,
        )

        nlp_result = run_nlp_analysis(
            analysis.claim_text
        )

        analysis.nlp_result = nlp_result

        analysis.save(
            update_fields=[
                "nlp_result",
                "updated_at",
            ]
        )

        # Uzun ML islemleri oncesinde eski DB
        # connection'i serbest birak.
        close_old_connections()

        # --------------------------------------------------
        # PROPAGATION GRAPH
        # --------------------------------------------------
        centrifugo.publish_analysis_progress(
            analysis_id,
            stage="graph",
            progress=0.35,
        )

        if analysis.propagation_graph_id:
            graph = PropagationGraph.objects.get(
                pk=analysis.propagation_graph_id
            )

        else:
            query = (
                analysis.query.strip()
                if analysis.query
                else analysis.claim_text[:255]
            )

            ingest_result = ingest_social_query(
                query=query,
                max_results=10,
            )

            graph = PropagationGraph.objects.get(
                pk=ingest_result["graph_id"]
            )

            analysis.propagation_graph = graph

            analysis.save(
                update_fields=[
                    "propagation_graph",
                    "updated_at",
                ]
            )

        # --------------------------------------------------
        # GNN
        # --------------------------------------------------
        centrifugo.publish_analysis_progress(
            analysis_id,
            stage="gnn",
            progress=0.60,
        )

        gnn_result = run_gnn_analysis(
            analysis_id=analysis.id
        )

        analysis.gnn_result = gnn_result

        analysis.save(
            update_fields=[
                "gnn_result",
                "updated_at",
            ]
        )

        # --------------------------------------------------
        # BOT ANALYSIS
        # --------------------------------------------------
        centrifugo.publish_analysis_progress(
            analysis_id,
            stage="bot_detection",
            progress=0.80,
        )

        bot_result = run_bot_analysis(
            analysis_id=analysis.id
        )

        analysis.bot_analysis_result = (
            bot_result
        )

        analysis.save(
            update_fields=[
                "bot_analysis_result",
                "updated_at",
            ]
        )

        close_old_connections()

        # --------------------------------------------------
        # AI EVIDENCE / RAG ANALYSIS
        # --------------------------------------------------
        centrifugo.publish_analysis_progress(
            analysis_id,
            stage="ai_evidence",
            progress=0.90,
        )

        try:
            ai_result = (
                run_ai_evidence_analysis(
                    analysis.claim_text
                )
            )

        except Exception as exc:
            logger.exception(
                "AI evidence analysis failed: "
                "analysis_id=%s",
                analysis_id,
            )

            ai_result = {
                "status": "failed",
                "reason":
                    "ai_evidence_analysis_failed",
                "error_type":
                    type(exc).__name__,
                "report": None,
            }

        analysis.ai_analysis_result = (
            ai_result
        )

        # Bilerek truth_score hesaplamiyoruz.
        #
        # GNN UPFD/Politifact cross-domain.
        # Bot modeli de tarihsel Cresci-derived
        # Twitter profil verisinden guncel X alanina
        # cross-domain uygulanmaktadir ve skorlari
        # kalibre edilmis olasilik degildir.
        #
        # Bu sinyalleri "gerceklik skoru" diye
        # birlestirmek metodolojik olarak henuz
        # dogru olmaz.
        analysis.truth_score = None

        analysis.status = (
            AnalysisStatus.COMPLETED
        )

        analysis.save(
            update_fields=[
                "ai_analysis_result",
                "truth_score",
                "status",
                "updated_at",
            ]
        )

        centrifugo.publish_analysis_progress(
            analysis_id,
            stage="completed",
            progress=1.0,
        )

        return {
            "analysis_id": analysis.id,
            "status": analysis.status,
            "graph_id": graph.id,
            "gnn_prediction": (
                gnn_result[
                    "predicted_label"
                ]
            ),
            "gnn_confidence": (
                gnn_result[
                    "confidence"
                ]
            ),
            "ai_analysis_status": (
                ai_result.get(
                    "status"
                )
            ),
        }

    except Exception:
        logger.exception(
            "Analysis task failed: analysis_id=%s",
            analysis_id,
        )

        analysis.status = (
            AnalysisStatus.FAILED
        )

        analysis.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        centrifugo.publish_analysis_progress(
            analysis_id,
            stage="failed",
            progress=1.0,
        )

        raise
