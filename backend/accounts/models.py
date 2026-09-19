"""
Kullanici modeli ve rol tabanli erisim kontrolu (RBAC).

Roller: admin, analyst, viewer.
- admin: tam yetki (kullanici yonetimi, tum analizler)
- analyst: analiz olusturma / calistirma / goruntuleme
- viewer: sadece salt-okunur goruntuleme
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    ANALYST = "analyst", "Analyst"
    VIEWER = "viewer", "Viewer"


class User(AbstractUser):
    """Custom user model - RBAC icin `role` alani eklenmis Django auth kullanicisi."""

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        help_text="Kullanicinin platform icindeki rolu (RBAC).",
    )

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"

    @property
    def is_admin_role(self) -> bool:
        return self.role == Role.ADMIN

    @property
    def is_analyst_role(self) -> bool:
        return self.role in (Role.ADMIN, Role.ANALYST)
