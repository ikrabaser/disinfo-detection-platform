import re

import pytest

from django.core import mail
from django.test import override_settings

from rest_framework.test import APIClient

from accounts.models import User


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends."
        "locmem.EmailBackend"
    ),
    FRONTEND_URL="http://localhost:5174",
)
def test_password_reset_flow():
    user = User.objects.create_user(
        username="reset-user",
        email="reset@example.com",
        password="OldPass!234",
    )

    client = APIClient()

    response = client.post(
        "/api/auth/password-reset/",
        {
            "email":
                "reset@example.com"
        },
        format="json",
    )

    assert response.status_code == 200
    assert len(mail.outbox) == 1

    body = mail.outbox[0].body

    match = re.search(
        r"uid=([^&\s]+)&token=([^\s]+)",
        body,
    )

    assert match is not None

    uid, token = match.groups()

    confirm_response = client.post(
        "/api/auth/password-reset/confirm/",
        {
            "uid": uid,
            "token": token,
            "new_password":
                "NewPass!987654",
            "confirm_password":
                "NewPass!987654",
        },
        format="json",
    )

    assert (
        confirm_response.status_code
        == 200
    )

    user.refresh_from_db()

    assert user.check_password(
        "NewPass!987654"
    )


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends."
        "locmem.EmailBackend"
    )
)
def test_unknown_email_does_not_leak_account():
    client = APIClient()

    response = client.post(
        "/api/auth/password-reset/",
        {
            "email":
                "missing@example.com"
        },
        format="json",
    )

    assert response.status_code == 200
    assert len(mail.outbox) == 0
