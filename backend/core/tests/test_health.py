import pytest

from django.urls import reverse


@pytest.mark.django_db
def test_health_endpoint_returns_ok(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        "core.urls.get_system_health",
        lambda: {
            "status": "ok",
            "services": {
                "api": "ok",
                "database": "ok",
                "redis": "ok",
                "queue": "ok",
                "realtime": "ok",
            },
        },
    )

    response = client.get(
        reverse(
            "health-check"
        )
    )

    assert (
        response.status_code
        == 200
    )

    assert (
        response.json()[
            "status"
        ]
        == "ok"
    )


@pytest.mark.django_db
def test_health_endpoint_returns_503_when_degraded(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        "core.urls.get_system_health",
        lambda: {
            "status":
                "degraded",
            "services": {
                "api": "ok",
                "database": "ok",
                "redis": "ok",
                "queue": "ok",
                "realtime":
                    "down",
            },
        },
    )

    response = client.get(
        reverse(
            "health-check"
        )
    )

    assert (
        response.status_code
        == 503
    )

    assert (
        response.json()[
            "services"
        ][
            "realtime"
        ]
        == "down"
    )
