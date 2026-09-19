"""
Centrifugo entegrasyonu - analiz ilerlemesini (progress) gercek zamanli
olarak frontend'e yayinlamak icin kullanilir.

Mimari notu:
    Backend (Django) -> Centrifugo HTTP API (publish) -> Centrifugo sunucusu
    -> WebSocket -> Frontend (dashboard, analiz detay sayfasi).

Redis, Centrifugo'nun kendi ic engine'i olarak (cluster/scale senaryolarinda)
veya Django cache/Procrastinate backend'i olarak kullanilir (REDIS_URL).

Bu modul GERCEK bir HTTP cagrisi yapmaz (agirlikli olarak `requests`
kutuphanesi ile yapilmalidir); asagida STUB + TODO olarak birakilmistir.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class CentrifugoClient:
    """Centrifugo API'sine event publish eden istemci (STUB)."""

    def __init__(self, api_url: str | None = None, api_key: str | None = None):
        self.api_url = api_url or settings.CENTRIFUGO_API_URL
        self.api_key = api_key or settings.CENTRIFUGO_API_KEY

    def publish(self, channel: str, data: dict[str, Any]) -> dict[str, Any]:
        """Verilen kanala bir event yayinlar.

        TODO (gercek implementasyon):
            import requests
            response = requests.post(
                f"{self.api_url}/publish",
                headers={"Authorization": f"apikey {self.api_key}"},
                json={"channel": channel, "data": data},
                timeout=5,
            )
            response.raise_for_status()
            return response.json()
        """
        logger.info("[CentrifugoClient STUB] publish -> channel=%s data=%s", channel, json.dumps(data))
        return {"status": "mock-published", "channel": channel}

    def publish_analysis_progress(self, analysis_id: int, stage: str, progress: float) -> dict[str, Any]:
        """Bir analizin ilerleme durumunu `analysis:<id>` kanalina yayinlar.

        Args:
            analysis_id: Analysis model PK.
            stage: "nlp" | "gnn" | "bot_detection" | "source_verification" | "done"
            progress: 0.0 - 1.0 arasi ilerleme yuzdesi.
        """
        channel = f"analysis:{analysis_id}"
        return self.publish(channel, {"stage": stage, "progress": progress})


def get_centrifugo_client() -> CentrifugoClient:
    return CentrifugoClient()
