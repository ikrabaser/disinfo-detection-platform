from django.urls import path

from agent.views import AgentPromptView, AgentToolListView

urlpatterns = [
    path("prompt/", AgentPromptView.as_view(), name="agent-prompt"),
    path("tools/", AgentToolListView.as_view(), name="agent-tools"),
]
