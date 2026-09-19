from django.urls import path

from realtime.views import AnalysisProgressSSEView, CentrifugoConnectTokenView

urlpatterns = [
    path("connect-token/", CentrifugoConnectTokenView.as_view(), name="realtime-connect-token"),
    path("analyses/<int:analysis_id>/stream/", AnalysisProgressSSEView.as_view(), name="realtime-analysis-sse"),
]
