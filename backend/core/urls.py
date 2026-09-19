"""Root URL configuration."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    return JsonResponse({"status": "ok", "service": "dezenformasyon-tespit-platformu"})


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
]
