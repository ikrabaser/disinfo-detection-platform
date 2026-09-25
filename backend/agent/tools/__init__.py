"""
Agent tool'lari - AI ajaninin cagirabilecegi fonksiyonlar.

Her tool:
  - Tip belirtilmis (typed) bir imzaya sahiptir.
  - Acik bir docstring icerir (OpenAI'a "structured outputs"/function-calling
    semasi uretmek icin kullanilabilir).
  - `@tool_permission(roles=...)` decorator'i ile hangi rollerin bu tool'u
    cagirabilecegini beyan eder (bkz. agent/tools/permissions.py).

Tum tool fonksiyonlari `TOOL_REGISTRY` icinde toplanir; agent/client.py bu
registry'i kullanarak OpenAI'a gonderilecek tool semalarini insa eder.
"""
from agent.tools.get_analysis_result import get_analysis_result
from agent.tools.get_news import get_news
from agent.tools.get_social_posts import get_social_posts
from agent.tools.run_bot_analysis import run_bot_analysis
from agent.tools.run_gnn_analysis import run_gnn_analysis
from agent.tools.run_nlp_analysis import run_nlp_analysis
from agent.tools.search_evidence import search_evidence
from agent.tools.verify_sources import verify_sources

TOOL_REGISTRY = {
    "get_news": get_news,
    "get_social_posts": get_social_posts,
    "run_nlp_analysis": run_nlp_analysis,
    "run_gnn_analysis": run_gnn_analysis,
    "run_bot_analysis": run_bot_analysis,
    "search_evidence": search_evidence,
    "verify_sources": verify_sources,
    "get_analysis_result": get_analysis_result,
}

__all__ = ["TOOL_REGISTRY"] + list(TOOL_REGISTRY.keys())
