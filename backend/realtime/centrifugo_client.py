from __future__ import annotations

import logging
from typing import Any

import httpx
from django.conf import settings


logger = logging.getLogger(__name__)


class CentrifugoClient:
    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 5.0,
    ):
        self.api_url = (
            api_url
            or settings.CENTRIFUGO_API_URL
        ).rstrip("/")

        self.api_key = (
            api_key
            or settings.CENTRIFUGO_API_KEY
        )

        self.timeout = timeout

    def publish(
        self,
        channel: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        url = f"{self.api_url}/publish"

        try:
            response = httpx.post(
                url,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "channel": channel,
                    "data": data,
                },
                timeout=self.timeout,
            )

            response.raise_for_status()

            result = response.json()

            if result.get("error"):
                error = result["error"]

                logger.warning(
                    "Centrifugo API error: "
                    "channel=%s error=%s",
                    channel,
                    error,
                )

                return {
                    "status": "publish-failed",
                    "channel": channel,
                    "error": error,
                }

            logger.info(
                "Centrifugo publish success: channel=%s",
                channel,
            )

            return {
                "status": "published",
                "channel": channel,
                "response": result,
            }

        except (
            httpx.RequestError,
            httpx.HTTPStatusError,
        ) as exc:
            logger.warning(
                "Centrifugo publish failed: "
                "channel=%s error=%s",
                channel,
                exc,
            )

            # Realtime katmani core analysis'i
            # dusurmemeli.
            return {
                "status": "publish-failed",
                "channel": channel,
                "error": str(exc),
            }

    def publish_analysis_progress(
        self,
        analysis_id: int,
        stage: str,
        progress: float,
    ) -> dict[str, Any]:
        channel = f"analysis:{analysis_id}"

        return self.publish(
            channel,
            {
                "analysis_id": analysis_id,
                "stage": stage,
                "progress": progress,
            },
        )


def get_centrifugo_client() -> CentrifugoClient:
    return CentrifugoClient()
