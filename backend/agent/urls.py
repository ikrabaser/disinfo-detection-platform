from django.urls import path

from agent.views import (
    AgentPromptView,
    AgentProviderListView,
    AgentToolListView,
    AssistantConversationDetailView,
    AssistantConversationListCreateView,
    AssistantMessageCreateView,
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
    path(
        "conversations/",
        AssistantConversationListCreateView.as_view(),
        name="assistant-conversations",
    ),
    path(
        "conversations/<uuid:conversation_id>/",
        AssistantConversationDetailView.as_view(),
        name="assistant-conversation-detail",
    ),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        AssistantMessageCreateView.as_view(),
        name="assistant-message-create",
    ),
]
