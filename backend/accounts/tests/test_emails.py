import pytest

from django.core import mail
from django.test import override_settings

from accounts.emails import (
    send_registration_otp_email,
)


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends."
        "locmem.EmailBackend"
    ),
)
def test_otp_email_has_plain_and_html():
    send_registration_otp_email(
        recipient="test@example.com",
        code="482173",
        timeout_minutes=10,
    )

    assert len(mail.outbox) == 1

    message = mail.outbox[0]

    assert "482173" in message.body
    assert "VERITAS" in message.body

    assert len(
        message.alternatives
    ) == 1

    alternative = (
        message.alternatives[0]
    )

    html = (
        alternative.content
        if hasattr(
            alternative,
            "content",
        )
        else alternative[0]
    )

    mimetype = (
        alternative.mimetype
        if hasattr(
            alternative,
            "mimetype",
        )
        else alternative[1]
    )

    assert mimetype == "text/html"
    assert "482173" in html
    assert "VERITAS" in html
    assert "E-postanızı doğrulayın" in html
