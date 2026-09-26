import pytest

from django.core.cache import cache
from django.test import override_settings

from rest_framework.test import APIClient

from accounts.models import Role, User


TEST_CACHE = {
    "default": {
        "BACKEND": (
            "django.core.cache.backends."
            "locmem.LocMemCache"
        ),
        "LOCATION":
            "user-management-tests",
    }
}


@pytest.fixture(autouse=True)
def isolated_cache():
    with override_settings(
        CACHES=TEST_CACHE
    ):
        cache.clear()
        yield
        cache.clear()


@pytest.fixture
def users(db):
    admin = User.objects.create_user(
        username="admin-user",
        email="admin@example.com",
        password="StrongPass!987",
        role=Role.ADMIN,
    )

    analyst = User.objects.create_user(
        username="analyst-user",
        email="analyst@example.com",
        password="StrongPass!987",
        role=Role.ANALYST,
    )

    viewer = User.objects.create_user(
        username="viewer-user",
        email="viewer@example.com",
        password="StrongPass!987",
        role=Role.VIEWER,
    )

    return admin, analyst, viewer


@pytest.mark.django_db
def test_admin_can_list_users(
    users
):
    admin, _, _ = users

    client = APIClient()
    client.force_authenticate(
        user=admin
    )

    response = client.get(
        "/api/auth/users/"
    )

    assert response.status_code == 200
    assert len(response.data) == 3


@pytest.mark.django_db
def test_non_admin_cannot_list_users(
    users
):
    _, analyst, viewer = users

    for user in (
        analyst,
        viewer,
    ):
        client = APIClient()

        client.force_authenticate(
            user=user
        )

        response = client.get(
            "/api/auth/users/"
        )

        assert (
            response.status_code
            == 403
        )


@pytest.mark.django_db
def test_admin_can_change_other_user_role(
    users
):
    admin, _, viewer = users

    client = APIClient()

    client.force_authenticate(
        user=admin
    )

    response = client.patch(
        (
            f"/api/auth/users/"
            f"{viewer.id}/role/"
        ),
        {
            "role":
                Role.ANALYST
        },
        format="json",
    )

    assert response.status_code == 200

    viewer.refresh_from_db()

    assert (
        viewer.role
        == Role.ANALYST
    )


@pytest.mark.django_db
def test_admin_cannot_change_own_role(
    users
):
    admin, _, _ = users

    client = APIClient()

    client.force_authenticate(
        user=admin
    )

    response = client.patch(
        (
            f"/api/auth/users/"
            f"{admin.id}/role/"
        ),
        {
            "role":
                Role.VIEWER
        },
        format="json",
    )

    assert response.status_code == 400

    admin.refresh_from_db()

    assert (
        admin.role
        == Role.ADMIN
    )


@pytest.mark.django_db
def test_invalid_role_is_rejected(
    users
):
    admin, _, viewer = users

    client = APIClient()

    client.force_authenticate(
        user=admin
    )

    response = client.patch(
        (
            f"/api/auth/users/"
            f"{viewer.id}/role/"
        ),
        {
            "role":
                "super-admin"
        },
        format="json",
    )

    assert response.status_code == 400
