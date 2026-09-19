"""
Procrastinate task tanimlari (STUB).

Gercek implementasyonda bu tasklar, `AgentRunner` veya dogrudan
nlp_engine/graph_engine servislerini cagirarak uzun suren analiz
islemlerini arka planda (asenkron) calistirir ve Centrifugo uzerinden
ilerleme yayinlar.
"""
from __future__ import annotations

from typing import Any


def run_analysis_task_stub(analysis_id: int) -> dict[str, Any]:
    """Bir Analysis kaydini uctan uca isleyen (mock) is parcacigi.

    TODO: Gercek implementasyonda `@app.task` decorator'i ile Procrastinate'e
    kaydedilmeli:

        from procrastinate_app.app import get_procrastinate_app
        app = get_procrastinate_app()

        @app.task(queue="analysis")
        def run_analysis_task(analysis_id: int):
            ...gercek analiz akisi (nlp + gnn + bot + skor birlestirme)...
            ...realtime.centrifugo_client ile ilerleme yayinla...

    Bu fonksiyon, PROCRASTINATE_ENABLED=false oldugunda dogrudan senkron
    olarak cagirilabilecek basit bir mock/sync fallback saglar.
    """
    from agent.tools.run_bot_analysis import run_bot_analysis
    from agent.tools.run_gnn_analysis import run_gnn_analysis
    from agent.tools.run_nlp_analysis import run_nlp_analysis
    from analyses.models import Analysis, AnalysisStatus
    from realtime.centrifugo_client import get_centrifugo_client

    centrifugo = get_centrifugo_client()

    try:
        analysis = Analysis.objects.get(pk=analysis_id)
    except Analysis.DoesNotExist:
        return {"error": f"Analysis id={analysis_id} bulunamadi."}

    centrifugo.publish_analysis_progress(analysis_id, stage="nlp", progress=0.2)
    nlp_result = run_nlp_analysis(analysis.claim_text)

    centrifugo.publish_analysis_progress(analysis_id, stage="gnn", progress=0.5)
    gnn_result = run_gnn_analysis(graph_id=str(analysis.propagation_graph_id or "mock"))

    centrifugo.publish_analysis_progress(analysis_id, stage="bot_detection", progress=0.8)
    bot_result = run_bot_analysis(user_ids=["user-a", "user-b"])

    # Basit bir birlestirme formulu (TODO: gercek/agirlikli bir formulle degistirin).
    truth_score = round(
        (nlp_result["confidence"] * 0.4)
        + ((1 - gnn_result["organized_campaign_score"]) * 0.3)
        + ((1 - max(bot_result["scores"].values(), default=0)) * 0.3),
        3,
    )

    analysis.nlp_result = nlp_result
    analysis.gnn_result = gnn_result
    analysis.bot_analysis_result = bot_result
    analysis.truth_score = truth_score
    analysis.status = AnalysisStatus.COMPLETED
    analysis.save()

    centrifugo.publish_analysis_progress(analysis_id, stage="done", progress=1.0)
    return {"analysis_id": analysis_id, "truth_score": truth_score}
