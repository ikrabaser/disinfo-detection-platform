"""
Auth view'lari - JWT'yi HttpOnly cookie olarak set eden login/refresh/logout
endpoint'leri.
"""
from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from accounts.serializers import RegisterSerializer, UserSerializer


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    cookie_kwargs = dict(
        httponly=settings.JWT_AUTH_COOKIE_HTTPONLY,
        secure=settings.JWT_AUTH_COOKIE_SECURE,
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
    )
    response.set_cookie(settings.JWT_AUTH_COOKIE, access, **cookie_kwargs)
    response.set_cookie(settings.JWT_AUTH_REFRESH_COOKIE, refresh, **cookie_kwargs)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=201)


class LoginView(APIView):
    """Kullanici adi/sifre ile giris yapar, JWT'leri HttpOnly cookie olarak doner."""

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = User.objects.filter(username=username).first()
        if user is None or not user.check_password(password):
            return Response({"detail": "Gecersiz kimlik bilgileri."}, status=401)

        refresh = RefreshToken.for_user(user)
        response = Response(UserSerializer(user).data, status=200)
        _set_auth_cookies(response, str(refresh.access_token), str(refresh))
        return response


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        raw_refresh = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if not raw_refresh:
            return Response({"detail": "Refresh token bulunamadi."}, status=401)
        try:
            serializer = TokenRefreshSerializer(data={"refresh": raw_refresh})
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response({"detail": "Gecersiz refresh token."}, status=401)

        access = serializer.validated_data["access"]
        new_refresh = serializer.validated_data.get("refresh", raw_refresh)
        response = Response({"detail": "Token yenilendi."}, status=200)
        _set_auth_cookies(response, access, new_refresh)
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"detail": "Cikis yapildi."}, status=200)
        response.delete_cookie(settings.JWT_AUTH_COOKIE)
        response.delete_cookie(settings.JWT_AUTH_REFRESH_COOKIE)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
