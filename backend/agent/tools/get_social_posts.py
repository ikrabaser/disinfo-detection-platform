"""Agent tool: get_social_posts."""

from agent.tools.permissions import tool_permission
from external.x_client import get_x_api_client


@tool_permission(roles={"admin", "analyst", "viewer"})
def get_social_posts(
    query: str,
    max_results: int = 10,
) -> list[dict]:
    """
    Verilen sorguyla ilişkili X paylaşımlarını getirir.

    Gerçek X API Bearer Token tanımlıysa canlı veri kullanılır.
    Token yoksa geliştirme ortamında mock client devreye girer.
    """

    client = get_x_api_client()

    return client.search_recent_posts(
        query=query,
        max_results=max_results,
    )
