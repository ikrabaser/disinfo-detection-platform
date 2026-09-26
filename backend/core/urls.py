"""Root URL configuration."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from core.health import (
    get_system_health,
)


def health_check(request):
    health = (
        get_system_health()
    )

    http_status = (
        200
        if health["status"]
        == "ok"
        else 503
    )

    return JsonResponse(
        health,
        status=http_status,
    )


def metrics_stub(request):
    """Prometheus metrics endpoint stub.

    django-prometheus kuruldugunda bu view, `django_prometheus.urls` ile
    degistirilmeli / include edilmelidir. Simdilik boyle bos bir stub
    metin gövdesi donuyor.
    """
    return JsonResponse({"note": "prometheus metrics stub - django-prometheus kurulunca aktif edilecek"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("metrics/", metrics_stub, name="metrics-stub"),
    path("api/auth/", include("accounts.urls")),
    path("api/agent/", include("agent.urls")),
    path("api/analyses/", include("analyses.urls")),
    path("api/realtime/", include("realtime.urls")),
    path("api/social/", include("external.urls")),
]
