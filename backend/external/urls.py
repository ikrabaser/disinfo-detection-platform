from django.urls import path

from external.views import (
    LatestPropagationGraphView,
    PropagationGraphDetailView,
    SocialIngestView,
    SocialSearchView,
)

urlpatterns = [
    path(
        "search/",
        SocialSearchView.as_view(),
        name="social-search",
    ),
    path(
        "ingest/",
        SocialIngestView.as_view(),
        name="social-ingest",
    ),
    path(
        "graphs/latest/",
        LatestPropagationGraphView.as_view(),
        name="latest-propagation-graph",
    ),
    path(
        "graphs/<int:graph_id>/",
        PropagationGraphDetailView.as_view(),
        name="propagation-graph-detail",
    ),
]
