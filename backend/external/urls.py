from django.urls import path

from external.views import SocialIngestView, SocialSearchView

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
]
