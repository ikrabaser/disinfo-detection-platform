"""Agent tool: verify_sources."""
from agent.tools.permissions import tool_permission
from external.news_fetcher import fetch_news_articles


@tool_permission(roles={"admin", "analyst"})
def verify_sources(claim: str) -> dict:
    """Verilen iddiayi (claim) bilinen/guvenilir haber kaynaklariyla karsilastirarak dogrular (mock).

    Args:
        claim: Dogrulanacak iddia/haber metni.

    Returns:
        {
            "claim": str,
            "supporting_sources": list[dict],
            "contradicting_sources": list[dict],
            "verification_status": "dogrulandi"|"celiskili"|"yetersiz-kaynak",
        }

    TODO: Gercek implementasyonda guvenilir haber kaynaklari veritabani /
    fact-checking API'leri (ör. Teyit.org benzeri servisler) ile
    karsilastirma yapilmalidir. Su an MOCK - fetch_news_articles sonuclarini
    "destekleyen kaynak" olarak isaretler.
    """
    related_articles = fetch_news_articles(query=claim, limit=3)

    return {
        "claim": claim,
        "supporting_sources": related_articles,
        "contradicting_sources": [],
        "verification_status": "yetersiz-kaynak",
    }
