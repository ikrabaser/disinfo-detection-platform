import re

import pytest

from django.core import mail
from django.core.cache import cache
from django.test import override_settings

from rest_framework.test import APIClient

from accounts.models import Role, User


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
                "register-otp-tests",
        }
    },
    "REGISTRATION_OTP_TIMEOUT":
        600,
    "REGISTRATION_RESEND_COOLDOWN":
        0,
    "REGISTRATION_MAX_ATTEMPTS":
        5,
}


@pytest.fixture(autouse=True)
def register_test_environment():
    with override_settings(
        **TEST_SETTINGS
    ):
        cache.clear()

        if hasattr(
            mail,
            "outbox"
        ):
            mail.outbox.clear()

        yield

        cache.clear()


@pytest.mark.django_db
def test_registration_requires_otp():
    client = APIClient()

    response = client.post(
        "/api/auth/register/",
        {
            "username":
                "verified-user",
            "email":
                "verified@example.com",
            "password":
                "StrongPass!987",
            "confirm_password":
                "StrongPass!987",
            "role":
                "admin",
        },
        format="json",
    )

    assert response.status_code == 200

    assert not User.objects.filter(
        username="verified-user"
    ).exists()

    assert len(mail.outbox) == 1

    match = re.search(
        r"\b(\d{6})\b",
        mail.outbox[0].body,
    )

    assert match is not None

    code = match.group(1)

    verify = client.post(
        "/api/auth/register/verify/",
        {
            "email":
                "verified@example.com",
            "code":
                code,
        },
        format="json",
    )

    assert verify.status_code == 201

    user = User.objects.get(
        username="verified-user"
    )

    assert user.email == (
        "verified@example.com"
    )

    assert user.role == Role.VIEWER

    assert user.is_active is True

    assert user.check_password(
        "StrongPass!987"
    )


@pytest.mark.django_db
def test_duplicate_email_is_rejected():
    User.objects.create_user(
        username="existing",
        email="existing@example.com",
        password="StrongPass!987",
    )

    client = APIClient()

    response = client.post(
        "/api/auth/register/",
        {
            "username":
                "new-user",
            "email":
                "EXISTING@example.com",
            "password":
                "StrongPass!987",
            "confirm_password":
                "StrongPass!987",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_registration_code_is_single_use():
    client = APIClient()

    response = client.post(
        "/api/auth/register/",
        {
            "username":
                "single-use",
            "email":
                "single@example.com",
            "password":
                "StrongPass!987",
            "confirm_password":
                "StrongPass!987",
        },
        format="json",
    )

    assert response.status_code == 200

    code = re.search(
        r"\b(\d{6})\b",
        mail.outbox[0].body,
    ).group(1)

    first = client.post(
        "/api/auth/register/verify/",
        {
            "email":
                "single@example.com",
            "code":
                code,
        },
        format="json",
    )

    assert first.status_code == 201

    second = client.post(
        "/api/auth/register/verify/",
        {
            "email":
                "single@example.com",
            "code":
                code,
        },
        format="json",
    )

    assert second.status_code == 400


@pytest.mark.django_db
def test_registration_locks_after_bad_codes():
    client = APIClient()

    response = client.post(
        "/api/auth/register/",
        {
            "username":
                "locked-register",
            "email":
                "locked-register@example.com",
            "password":
                "StrongPass!987",
            "confirm_password":
                "StrongPass!987",
        },
        format="json",
    )

    assert response.status_code == 200

    real_code = re.search(
        r"\b(\d{6})\b",
        mail.outbox[0].body,
    ).group(1)

    wrong_code = (
        "000000"
        if real_code != "000000"
        else "111111"
    )

    for _ in range(5):
        result = client.post(
            "/api/auth/register/verify/",
            {
                "email":
                    "locked-register@example.com",
                "code":
                    wrong_code,
            },
            format="json",
        )

        assert result.status_code == 400

    final = client.post(
        "/api/auth/register/verify/",
        {
            "email":
                "locked-register@example.com",
            "code":
                real_code,
        },
        format="json",
    )

    assert final.status_code == 400

    assert not User.objects.filter(
        username="locked-register"
    ).exists()
