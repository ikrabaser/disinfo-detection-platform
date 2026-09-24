from __future__ import annotations

import time

import jwt
from django.conf import settings


ALGORITHM = "HS256"


def _expiration() -> int:
    return (
        int(time.time())
        + settings.CENTRIFUGO_TOKEN_TTL_SECONDS
    )


def create_connection_token(
    user_id: int | str,
) -> str:
    claims = {
        "sub": str(user_id),
        "exp": _expiration(),
    }

    return jwt.encode(
        claims,
        settings.CENTRIFUGO_HMAC_SECRET,
        algorithm=ALGORITHM,
    )


def create_subscription_token(
    user_id: int | str,
    channel: str,
) -> str:
    claims = {
        "sub": str(user_id),
        "channel": channel,
        "exp": _expiration(),
    }

    return jwt.encode(
        claims,
        settings.CENTRIFUGO_HMAC_SECRET,
        algorithm=ALGORITHM,
    )
