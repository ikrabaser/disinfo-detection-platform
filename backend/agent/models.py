from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assistant_conversations",
    )

    analysis = models.ForeignKey(
        "analyses.Analysis",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assistant_conversations",
    )

    title = models.CharField(
        max_length=200,
        default="Yeni sohbet",
    )

    provider = models.CharField(
        max_length=32,
    )

    model = models.CharField(
        max_length=120,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "-updated_at",
        ]

    def __str__(self) -> str:
        return (
            f"{self.user_id}: "
            f"{self.title}"
        )


class MessageRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(
        max_length=16,
        choices=MessageRole.choices,
    )

    content = models.TextField()

    provider = models.CharField(
        max_length=32,
        blank=True,
    )

    model = models.CharField(
        max_length=120,
        blank=True,
    )

    input_tokens = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    output_tokens = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "created_at",
            "id",
        ]

    def __str__(self) -> str:
        return (
            f"{self.conversation_id} "
            f"[{self.role}]"
        )
