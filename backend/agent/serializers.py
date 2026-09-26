from __future__ import annotations

from rest_framework import serializers

from agent.models import (
    Conversation,
    Message,
)


class MessageSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Message

        fields = [
            "id",
            "role",
            "content",
            "provider",
            "model",
            "input_tokens",
            "output_tokens",
            "metadata",
            "created_at",
        ]

        read_only_fields = fields


class ConversationListSerializer(
    serializers.ModelSerializer
):
    message_count = (
        serializers.IntegerField(
            read_only=True
        )
    )

    class Meta:
        model = Conversation

        fields = [
            "id",
            "title",
            "provider",
            "model",
            "analysis",
            "message_count",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields


class ConversationDetailSerializer(
    serializers.ModelSerializer
):
    messages = MessageSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Conversation

        fields = [
            "id",
            "title",
            "provider",
            "model",
            "analysis",
            "messages",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields


class ConversationCreateSerializer(
    serializers.Serializer
):
    title = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
    )

    provider = serializers.CharField(
        required=False,
        allow_blank=False,
        max_length=32,
    )

    analysis_id = (
        serializers.IntegerField(
            required=False,
            allow_null=True,
        )
    )


class MessageCreateSerializer(
    serializers.Serializer
):
    content = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )



class ConversationUpdateSerializer(
    serializers.Serializer
):
    title = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        max_length=200,
    )
