from django.urls import path

from external.views import (
    LatestPropagationGraphView,
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
]
