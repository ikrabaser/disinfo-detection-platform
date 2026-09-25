import re

import pytest

from django.core import mail
from django.core.cache import cache
from django.test import override_settings

from rest_framework.test import APIClient

from accounts.models import User


TEST_SETTINGS = {
    "EMAIL_BACKEND": (
        "django.core.mail.backends."
        "locmem.EmailBackend"
    ),
    "CACHES": {
        "default": {
            "BACKEND": (
                "django.core.cache.backends."
                "locmem.LocMemCache"
            ),
            "LOCATION":
                "password-reset-tests",
        }
    },
    "PASSWORD_RESET_OTP_TIMEOUT": 600,
    "PASSWORD_RESET_TOKEN_TIMEOUT": 600,
    "PASSWORD_RESET_RESEND_COOLDOWN": 60,
    "PASSWORD_RESET_MAX_ATTEMPTS": 5,
}


@pytest.fixture(autouse=True)
def password_reset_test_settings():
    with override_settings(
        **TEST_SETTINGS
    ):
        cache.clear()

        yield

        cache.clear()


@pytest.mark.django_db
def test_password_reset_otp_flow():
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

    code_match = re.search(
        r"\b(\d{6})\b",
        mail.outbox[0].body,
    )

    assert code_match is not None

    code = code_match.group(1)

    verify = client.post(
        "/api/auth/password-reset/verify/",
        {
            "email":
                "reset@example.com",
            "code":
                code,
        },
        format="json",
    )

    assert verify.status_code == 200

    reset_token = (
        verify.data["reset_token"]
    )

    second_verify = client.post(
        "/api/auth/password-reset/verify/",
        {
            "email":
                "reset@example.com",
            "code":
                code,
        },
        format="json",
    )

    assert second_verify.status_code == 400

    confirm = client.post(
        "/api/auth/password-reset/confirm/",
        {
            "reset_token":
                reset_token,
            "new_password":
                "NewPass!987654",
            "confirm_password":
                "NewPass!987654",
        },
        format="json",
    )

    assert confirm.status_code == 200

    user.refresh_from_db()

    assert user.check_password(
        "NewPass!987654"
    )

    reused_token = client.post(
        "/api/auth/password-reset/confirm/",
        {
            "reset_token":
                reset_token,
            "new_password":
                "AnotherPass!987",
            "confirm_password":
                "AnotherPass!987",
        },
        format="json",
    )

    assert reused_token.status_code == 400


@pytest.mark.django_db
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

    verify = client.post(
        "/api/auth/password-reset/verify/",
        {
            "email":
                "missing@example.com",
            "code":
                "123456",
        },
        format="json",
    )

    assert verify.status_code == 400


@pytest.mark.django_db
def test_otp_locks_after_max_attempts():
    User.objects.create_user(
        username="locked-user",
        email="locked@example.com",
        password="OldPass!234",
    )

    client = APIClient()

    response = client.post(
        "/api/auth/password-reset/",
        {
            "email":
                "locked@example.com"
        },
        format="json",
    )

    assert response.status_code == 200

    code_match = re.search(
        r"\b(\d{6})\b",
        mail.outbox[0].body,
    )

    assert code_match is not None

    code = code_match.group(1)

    wrong_code = (
        "000000"
        if code != "000000"
        else "111111"
    )

    for _ in range(5):
        result = client.post(
            "/api/auth/password-reset/verify/",
            {
                "email":
                    "locked@example.com",
                "code":
                    wrong_code,
            },
            format="json",
        )

        assert result.status_code == 400

    correct_after_lock = client.post(
        "/api/auth/password-reset/verify/",
        {
            "email":
                "locked@example.com",
            "code":
                code,
        },
        format="json",
    )

    assert (
        correct_after_lock.status_code
        == 400
    )
