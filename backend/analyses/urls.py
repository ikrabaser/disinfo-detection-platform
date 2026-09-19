from rest_framework.routers import DefaultRouter

from analyses.views import AnalysisViewSet

router = DefaultRouter()
router.register("", AnalysisViewSet, basename="analysis")

urlpatterns = router.urls
