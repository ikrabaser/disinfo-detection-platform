"""
Auth view'lari - JWT'yi HttpOnly cookie olarak set eden login/refresh/logout
endpoint'leri.
"""
import logging

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from accounts.serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)


logger = logging.getLogger(__name__)


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



class PasswordResetRequestView(APIView):
    """
    Şifre sıfırlama bağlantısı üretir.

    Güvenlik nedeniyle kullanıcı/e-posta bulunup
    bulunmadığına bakılmaksızın aynı cevap döndürülür.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(
            data=request.data
        )
        serializer.is_valid(
            raise_exception=True
        )

        email = serializer.validated_data[
            "email"
        ]

        users = (
            User.objects.filter(
                email__iexact=email,
                is_active=True,
            )
            .exclude(email="")
        )

        for user in users:
            uid = urlsafe_base64_encode(
                force_bytes(user.pk)
            )

            token = (
                default_token_generator
                .make_token(user)
            )

            frontend_url = (
                settings.FRONTEND_URL
                .rstrip("/")
            )

            reset_url = (
                f"{frontend_url}"
                f"/reset-password"
                f"?uid={uid}"
                f"&token={token}"
            )

            message = (
                "VERITAS hesabınız için şifre "
                "sıfırlama talebi alındı.\n\n"
                "Yeni şifrenizi oluşturmak için "
                "aşağıdaki bağlantıyı açın:\n\n"
                f"{reset_url}\n\n"
                "Bu bağlantıyı siz istemediyseniz "
                "bu mesajı yok sayabilirsiniz."
            )

            try:
                send_mail(
                    subject=(
                        "VERITAS şifre sıfırlama"
                    ),
                    message=message,
                    from_email=(
                        settings.DEFAULT_FROM_EMAIL
                    ),
                    recipient_list=[
                        user.email
                    ],
                    fail_silently=False,
                )
            except Exception:
                logger.exception(
                    "Password reset email "
                    "could not be sent."
                )

        return Response(
            {
                "detail": (
                    "Bu e-posta adresiyle "
                    "eşleşen bir hesap varsa, "
                    "şifre sıfırlama bağlantısı "
                    "gönderildi."
                )
            },
            status=200,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = (
            PasswordResetConfirmSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        uid = serializer.validated_data[
            "uid"
        ]

        token = serializer.validated_data[
            "token"
        ]

        new_password = (
            serializer.validated_data[
                "new_password"
            ]
        )

        try:
            user_id = force_str(
                urlsafe_base64_decode(uid)
            )

            user = User.objects.get(
                pk=user_id,
                is_active=True,
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
        ):
            return Response(
                {
                    "detail": (
                        "Şifre sıfırlama "
                        "bağlantısı geçersiz "
                        "veya süresi dolmuş."
                    )
                },
                status=400,
            )

        if not (
            default_token_generator
            .check_token(
                user,
                token,
            )
        ):
            return Response(
                {
                    "detail": (
                        "Şifre sıfırlama "
                        "bağlantısı geçersiz "
                        "veya süresi dolmuş."
                    )
                },
                status=400,
            )

        try:
            validate_password(
                new_password,
                user=user,
            )
        except ValidationError as exc:
            return Response(
                {
                    "new_password":
                        list(exc.messages)
                },
                status=400,
            )

        user.set_password(
            new_password
        )

        user.save(
            update_fields=[
                "password"
            ]
        )

        return Response(
            {
                "detail":
                    "Şifreniz başarıyla güncellendi."
            },
            status=200,
        )
