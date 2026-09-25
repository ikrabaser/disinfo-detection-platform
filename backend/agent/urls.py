from django.urls import path

from agent.views import (
    AgentPromptView,
    AgentProviderListView,
    AgentToolListView,
)


urlpatterns = [
    path(
        "prompt/",
        AgentPromptView.as_view(),
        name="agent-prompt",
    ),
    path(
        "providers/",
        AgentProviderListView.as_view(),
        name="agent-providers",
    ),
    path(
        "tools/",
        AgentToolListView.as_view(),
        name="agent-tools",
    ),
]
