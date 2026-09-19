"""
HttpOnly cookie tabanli JWT authentication.

rest_framework_simplejwt varsayilan olarak `Authorization: Bearer <token>`
header'i bekler. Bu proje HttpOnly cookie akisi kullandigi icin, access
token'i `settings.JWT_AUTH_COOKIE` adli cookie'den okuyan kucuk bir
authentication sinifi tanimliyoruz. Boylece token JS tarafindan erisilemez
(XSS riskine karsi daha guvenli).
"""
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    """Access token'i Authorization header yerine HttpOnly cookie'den okur."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.JWT_AUTH_COOKIE)
        if raw_token is None:
            # Header fallback (ornegin mobil/API istemciler icin).
            return super().authenticate(request)
        try:
            validated_token = self.get_validated_token(raw_token)
        except InvalidToken:
            return None
        return self.get_user(validated_token), validated_token
