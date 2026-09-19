import pytest

from accounts.models import Role, User


@pytest.mark.django_db
def test_user_default_role_is_viewer():
    user = User.objects.create_user(username="tester", password="testpass123")
    assert user.role == Role.VIEWER
    assert user.is_admin_role is False
    assert user.is_analyst_role is False


@pytest.mark.django_db
def test_admin_role_flags():
    admin = User.objects.create_user(username="boss", password="testpass123", role=Role.ADMIN)
    assert admin.is_admin_role is True
    assert admin.is_analyst_role is True


@pytest.mark.django_db
def test_user_str_includes_role():
    user = User.objects.create_user(username="analyst1", password="testpass123", role=Role.ANALYST)
    assert "analyst1" in str(user)
    assert "analyst" in str(user)
