from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.throttling import (
    ScopedRateThrottle,
)
from rest_framework.views import APIView

from accounts.models import Role
from agent.client import AgentRunner
from agent.tools import TOOL_REGISTRY
from agent.tools.permissions import (
    can_invoke_tool,
)
from llm import get_provider_catalog


class AgentPromptView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "agent"

    def post(self, request):
        prompt = str(
            request.data.get(
                "prompt",
                "",
            )
        ).strip()

        provider_name = (
            request.data.get(
                "provider"
            )
        )

        if not prompt:
            return Response(
                {
                    "detail":
                        "'prompt' alani zorunludur."
                },
                status=400,
            )

        try:
            runner = AgentRunner(
                user=request.user,
                provider_name=provider_name,
            )

            result = runner.run(
                prompt
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=400,
            )

        return Response(
            {
                "output_text":
                    result.output_text,
                "provider":
                    result.provider,
                "model":
                    result.model,
                "tool_calls":
                    result.tool_calls,
                "structured_output":
                    result.structured_output,
            }
        )


class AgentProviderListView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        return Response(
            {
                "providers":
                    get_provider_catalog()
            }
        )


class AgentToolListView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        tools = []

        for name, fn in (
            TOOL_REGISTRY.items()
        ):
            meta = getattr(
                fn,
                "_tool_meta",
                {},
            )

            doc = meta.get(
                "doc",
                "",
            )

            tools.append(
                {
                    "name": name,
                    "description": (
                        doc.splitlines()[0]
                        if doc
                        else ""
                    ),
                    "allowed_roles":
                        sorted(
                            meta.get(
                                "allowed_roles",
                                [],
                            )
                        ),
                    "can_invoke":
                        can_invoke_tool(
                            request.user,
                            fn,
                        ),
                }
            )

        return Response(
            {
                "tools": tools
            }
        )


# ------------------------------------------------------------
# VERITAS Assistant conversations
# ------------------------------------------------------------

from django.db.models import Count
from rest_framework import status

from agent.models import Conversation
from agent.serializers import (
    ConversationCreateSerializer,
    ConversationDetailSerializer,
    ConversationListSerializer,
    ConversationUpdateSerializer,
    MessageCreateSerializer,
    MessageSerializer,
)
from agent.services import (
    AssistantService,
)
from analyses.models import Analysis
from llm import (
    LLMConfigurationError,
    LLMProviderError,
    get_llm_provider,
)


class AssistantConversationListCreateView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        conversations = (
            Conversation.objects
            .filter(
                user=request.user
            )
            .annotate(
                message_count=Count(
                    "messages"
                )
            )
            .order_by(
                "-updated_at"
            )
        )

        serializer = (
            ConversationListSerializer(
                conversations,
                many=True,
            )
        )

        return Response(
            {
                "conversations":
                    serializer.data
            }
        )

    def post(self, request):
        serializer = (
            ConversationCreateSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        requested_provider = (
            serializer.validated_data
            .get(
                "provider"
            )
        )

        try:
            provider = get_llm_provider(
                requested_provider
            )
        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        analysis = None

        analysis_id = (
            serializer.validated_data
            .get(
                "analysis_id"
            )
        )

        if analysis_id is not None:
            analysis_queryset = (
                Analysis.objects.all()
            )

            if (
                getattr(
                    request.user,
                    "role",
                    None,
                )
                != Role.ADMIN
            ):
                analysis_queryset = (
                    analysis_queryset.filter(
                        created_by=
                            request.user
                    )
                )

            try:
                analysis = (
                    analysis_queryset.get(
                        pk=analysis_id
                    )
                )

            except Analysis.DoesNotExist:
                return Response(
                    {
                        "detail":
                            "Analysis bulunamadi."
                    },
                    status=(
                        status
                        .HTTP_404_NOT_FOUND
                    ),
                )

        title = (
            serializer.validated_data
            .get(
                "title",
                "",
            )
            .strip()
            or "Yeni sohbet"
        )

        conversation = (
            Conversation.objects.create(
                user=request.user,
                analysis=analysis,
                title=title,
                provider=provider.name,
                model=provider.model,
            )
        )

        return Response(
            ConversationDetailSerializer(
                conversation
            ).data,
            status=(
                status
                .HTTP_201_CREATED
            ),
        )


class AssistantConversationDetailView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    def _get_conversation(
        self,
        request,
        conversation_id,
    ):
        try:
            return (
                Conversation.objects
                .prefetch_related(
                    "messages"
                )
                .get(
                    id=conversation_id,
                    user=request.user,
                )
            )
        except Conversation.DoesNotExist:
            return None

    def get(
        self,
        request,
        conversation_id,
    ):
        conversation = (
            self._get_conversation(
                request,
                conversation_id,
            )
        )

        if conversation is None:
            return Response(
                {
                    "detail":
                        "Sohbet bulunamadi."
                },
                status=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
            )

        return Response(
            ConversationDetailSerializer(
                conversation
            ).data
        )

    def patch(
        self,
        request,
        conversation_id,
    ):
        conversation = (
            self._get_conversation(
                request,
                conversation_id,
            )
        )

        if conversation is None:
            return Response(
                {
                    "detail":
                        "Sohbet bulunamadi."
                },
                status=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
            )

        serializer = (
            ConversationUpdateSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        conversation.title = (
            serializer.validated_data[
                "title"
            ]
        )

        conversation.save(
            update_fields=[
                "title",
                "updated_at",
            ]
        )

        return Response(
            ConversationDetailSerializer(
                conversation
            ).data
        )


    def delete(
        self,
        request,
        conversation_id,
    ):
        conversation = (
            self._get_conversation(
                request,
                conversation_id,
            )
        )

        if conversation is None:
            return Response(
                {
                    "detail":
                        "Sohbet bulunamadi."
                },
                status=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
            )

        conversation.delete()

        return Response(
            status=(
                status
                .HTTP_204_NO_CONTENT
            )
        )


class AssistantMessageCreateView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "agent"

    def post(
        self,
        request,
        conversation_id,
    ):
        try:
            conversation = (
                Conversation.objects
                .select_related(
                    "analysis",
                    "user",
                )
                .get(
                    id=conversation_id,
                    user=request.user,
                )
            )

        except Conversation.DoesNotExist:
            return Response(
                {
                    "detail":
                        "Sohbet bulunamadi."
                },
                status=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
            )

        serializer = (
            MessageCreateSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        service = AssistantService(
            user=request.user,
            conversation=conversation,
        )

        try:
            (
                user_message,
                assistant_message,
            ) = service.send(
                serializer.validated_data[
                    "content"
                ]
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        except LLMConfigurationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=(
                    status
                    .HTTP_503_SERVICE_UNAVAILABLE
                ),
            )

        except LLMProviderError:
            return Response(
                {
                    "detail":
                        "LLM provider yaniti "
                        "alinamadi."
                },
                status=(
                    status
                    .HTTP_502_BAD_GATEWAY
                ),
            )

        return Response(
            {
                "user_message":
                    MessageSerializer(
                        user_message
                    ).data,
                "assistant_message":
                    MessageSerializer(
                        assistant_message
                    ).data,
            },
            status=(
                status
                .HTTP_201_CREATED
            ),
        )


class AssistantMessageEditView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "agent"

    def post(
        self,
        request,
        conversation_id,
        message_id,
    ):
        try:
            conversation = (
                Conversation.objects
                .select_related(
                    "analysis",
                    "user",
                )
                .get(
                    id=conversation_id,
                    user=request.user,
                )
            )

        except Conversation.DoesNotExist:
            return Response(
                {
                    "detail":
                        "Sohbet bulunamadi."
                },
                status=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
            )

        serializer = (
            MessageCreateSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        service = AssistantService(
            user=request.user,
            conversation=conversation,
        )

        try:
            (
                edited_message,
                assistant_message,
                deleted_message_ids,
            ) = (
                service
                .edit_user_message_and_regenerate(
                    message_id=
                        message_id,
                    content=
                        serializer
                        .validated_data[
                            "content"
                        ],
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        except LLMConfigurationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=(
                    status
                    .HTTP_503_SERVICE_UNAVAILABLE
                ),
            )

        except LLMProviderError:
            return Response(
                {
                    "detail":
                        "LLM provider yaniti "
                        "alinamadi."
                },
                status=(
                    status
                    .HTTP_502_BAD_GATEWAY
                ),
            )

        return Response(
            {
                "edited_message":
                    MessageSerializer(
                        edited_message
                    ).data,
                "assistant_message":
                    MessageSerializer(
                        assistant_message
                    ).data,
                "deleted_message_ids":
                    deleted_message_ids,
            }
        )


class AssistantRegenerateView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "agent"

    def post(
        self,
        request,
        conversation_id,
    ):
        try:
            conversation = (
                Conversation.objects
                .select_related(
                    "analysis",
                    "user",
                )
                .get(
                    id=conversation_id,
                    user=request.user,
                )
            )

        except Conversation.DoesNotExist:
            return Response(
                {
                    "detail":
                        "Sohbet bulunamadi."
                },
                status=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
            )

        service = AssistantService(
            user=request.user,
            conversation=conversation,
        )

        try:
            (
                replaced_message_id,
                assistant_message,
            ) = service.regenerate_last()

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        except LLMConfigurationError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=(
                    status
                    .HTTP_503_SERVICE_UNAVAILABLE
                ),
            )

        except LLMProviderError:
            return Response(
                {
                    "detail":
                        "LLM provider yaniti "
                        "alinamadi."
                },
                status=(
                    status
                    .HTTP_502_BAD_GATEWAY
                ),
            )

        return Response(
            {
                "replaced_message_id":
                    replaced_message_id,
                "assistant_message":
                    MessageSerializer(
                        assistant_message
                    ).data,
            }
        )


# ------------------------------------------------------------
# VERITAS Assistant SSE streaming
# ------------------------------------------------------------

import json

from django.http import (
    StreamingHttpResponse,
)


def _assistant_sse(
    event_name: str,
    payload: dict,
) -> str:
    return (
        f"event: {event_name}\n"
        "data: "
        + json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
        + "\n\n"
    )


class AssistantMessageStreamView(
    APIView
):
    permission_classes = [
        IsAuthenticated
    ]

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "agent"

    def post(
        self,
        request,
        conversation_id,
    ):
        try:
            conversation = (
                Conversation.objects
                .select_related(
                    "analysis",
                    "user",
                )
                .get(
                    id=conversation_id,
                    user=request.user,
                )
            )

        except Conversation.DoesNotExist:
            return Response(
                {
                    "detail":
                        "Sohbet bulunamadi."
                },
                status=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
            )

        serializer = (
            MessageCreateSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        service = AssistantService(
            user=request.user,
            conversation=conversation,
        )

        if not service.provider.configured:
            return Response(
                {
                    "detail":
                        f"{service.provider.name} "
                        "provider configure edilmemis."
                },
                status=(
                    status
                    .HTTP_503_SERVICE_UNAVAILABLE
                ),
            )

        content = (
            serializer.validated_data[
                "content"
            ]
        )

        def stream():
            try:
                for item in (
                    service.stream_send(
                        content
                    )
                ):
                    event_name = item[
                        "event"
                    ]

                    if (
                        event_name
                        == "start"
                    ):
                        payload = {
                            "user_message":
                                MessageSerializer(
                                    item[
                                        "user_message"
                                    ]
                                ).data
                        }

                    elif (
                        event_name
                        == "delta"
                    ):
                        payload = {
                            "delta":
                                item["delta"]
                        }

                    elif event_name in {
                        "tool_start",
                        "tool_end",
                    }:
                        payload = {
                            "tool_call":
                                item[
                                    "tool_call"
                                ]
                        }

                    elif (
                        event_name
                        == "done"
                    ):
                        payload = {
                            "user_message":
                                MessageSerializer(
                                    item[
                                        "user_message"
                                    ]
                                ).data,
                            "assistant_message":
                                MessageSerializer(
                                    item[
                                        "assistant_message"
                                    ]
                                ).data,
                        }

                    else:
                        continue

                    yield _assistant_sse(
                        event_name,
                        payload,
                    )

            except (
                LLMConfigurationError,
                ValueError,
            ) as exc:
                yield _assistant_sse(
                    "error",
                    {
                        "detail":
                            str(exc)
                    },
                )

            except LLMProviderError:
                yield _assistant_sse(
                    "error",
                    {
                        "detail":
                            "LLM provider yaniti "
                            "alinamadi."
                    },
                )

            except Exception:
                yield _assistant_sse(
                    "error",
                    {
                        "detail":
                            "Assistant streaming "
                            "sirasinda beklenmeyen "
                            "bir hata olustu."
                    },
                )

        response = (
            StreamingHttpResponse(
                stream(),
                content_type=(
                    "text/event-stream"
                ),
            )
        )

        response[
            "Cache-Control"
        ] = "no-cache"

        response[
            "X-Accel-Buffering"
        ] = "no"

        return response
