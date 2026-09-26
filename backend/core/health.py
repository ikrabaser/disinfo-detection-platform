from __future__ import annotations

from typing import Callable

import httpx
import redis

from django.conf import settings
from django.db import connection


def _safe_check(
    check: Callable[[], bool],
) -> str:
    try:
        return (
            "ok"
            if check()
            else "down"
        )
    except Exception:
        return "down"


def check_database() -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1"
        )

        row = cursor.fetchone()

    return (
        row is not None
        and row[0] == 1
    )


def check_redis() -> bool:
    client = redis.Redis.from_url(
        settings.REDIS_URL,
        socket_connect_timeout=1.5,
        socket_timeout=1.5,
    )

    return bool(
        client.ping()
    )


def check_procrastinate_queue() -> bool:
    """
    Worker heartbeat degil.

    Procrastinate'in PostgreSQL queue
    storage'inin erisilebilir oldugunu
    dogrular.
    """

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM procrastinate_jobs
            LIMIT 1
            """
        )

    return True


def centrifugo_health_url() -> str:
    api_url = (
        settings
        .CENTRIFUGO_API_URL
        .rstrip("/")
    )

    if api_url.endswith(
        "/api"
    ):
        return (
            api_url[:-4]
            + "/health"
        )

    return (
        api_url
        + "/health"
    )


def check_realtime() -> bool:
    response = httpx.get(
        centrifugo_health_url(),
        timeout=1.5,
    )

    return (
        response.status_code
        == 200
    )


def get_system_health() -> dict:
    services = {
        "api": "ok",
        "database":
            _safe_check(
                check_database
            ),
        "redis":
            _safe_check(
                check_redis
            ),
        "queue":
            _safe_check(
                check_procrastinate_queue
            ),
        "realtime":
            _safe_check(
                check_realtime
            ),
    }

    healthy = all(
        value == "ok"
        for value
        in services.values()
    )

    return {
        "status":
            "ok"
            if healthy
            else "degraded",
        "services":
            services,
    }
