"""
VERITAS authentication endpoints.

JWT access/refresh tokenlari HttpOnly cookie olarak kullanilir.
Password reset akisi 6 haneli OTP + kisa omurlu tek kullanimlik
reset token uzerinden ilerler.
"""

import hashlib
import hmac
import logging
import secrets

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction
from django.contrib.auth.password_validation import (
    validate_password,
)
from django.core.cache import cache
from django.core.exceptions import ValidationError

from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.throttling import (
    ScopedRateThrottle,
)
from rest_framework.views import APIView

from rest_framework_simplejwt.exceptions import (
    TokenError,
)
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import (
    RefreshToken,
)

from accounts.models import User
from accounts.permissions import IsAdminRole
from accounts.emails import (
    send_password_reset_otp_email,
    send_registration_otp_email,
)
from accounts.serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    RegisterSerializer,
    RegisterResendSerializer,
    RegisterVerifySerializer,
    UserSerializer,
    UserRoleUpdateSerializer,
)


logger = logging.getLogger(__name__)


def _set_auth_cookies(
    response: Response,
    access: str,
    refresh: str,
) -> None:
    cookie_kwargs = dict(
        httponly=(
            settings.JWT_AUTH_COOKIE_HTTPONLY
        ),
        secure=(
            settings.JWT_AUTH_COOKIE_SECURE
        ),
        samesite=(
            settings.JWT_AUTH_COOKIE_SAMESITE
        ),
    )

    response.set_cookie(
        settings.JWT_AUTH_COOKIE,
        access,
        **cookie_kwargs,
    )

    response.set_cookie(
        settings.JWT_AUTH_REFRESH_COOKIE,
        refresh,
        **cookie_kwargs,
    )


def _normalise_email(
    email: str,
) -> str:
    return email.strip().lower()


def _email_digest(
    email: str,
) -> str:
    return hashlib.sha256(
        _normalise_email(email).encode(
            "utf-8"
        )
    ).hexdigest()


def _otp_cache_key(
    email: str,
) -> str:
    return (
        "password-reset:otp:"
        f"{_email_digest(email)}"
    )


def _attempts_cache_key(
    email: str,
) -> str:
    return (
        "password-reset:attempts:"
        f"{_email_digest(email)}"
    )


def _cooldown_cache_key(
    email: str,
) -> str:
    return (
        "password-reset:cooldown:"
        f"{_email_digest(email)}"
    )


def _reset_token_cache_key(
    token: str,
) -> str:
    digest = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    return (
        "password-reset:token:"
        f"{digest}"
    )


def _otp_hash(
    user_id: int,
    code: str,
) -> str:
    payload = (
        f"{user_id}:{code}"
    ).encode("utf-8")

    return hmac.new(
        settings.SECRET_KEY.encode(
            "utf-8"
        ),
        payload,
        hashlib.sha256,
    ).hexdigest()



def _registration_pending_key(
    email: str,
) -> str:
    return (
        "registration:pending:"
        f"{_email_digest(email)}"
    )


def _registration_attempts_key(
    email: str,
) -> str:
    return (
        "registration:attempts:"
        f"{_email_digest(email)}"
    )


def _registration_cooldown_key(
    email: str,
) -> str:
    return (
        "registration:cooldown:"
        f"{_email_digest(email)}"
    )


def _registration_code_hash(
    email: str,
    code: str,
) -> str:
    payload = (
        f"{_normalise_email(email)}:{code}"
    ).encode("utf-8")

    return hmac.new(
        settings.SECRET_KEY.encode(
            "utf-8"
        ),
        payload,
        hashlib.sha256,
    ).hexdigest()


def _send_registration_code(
    email: str,
    code: str,
) -> None:
    timeout_minutes = max(
        1,
        settings.REGISTRATION_OTP_TIMEOUT
        // 60,
    )

    send_registration_otp_email(
        recipient=email,
        code=code,
        timeout_minutes=timeout_minutes,
    )


class RegisterView(APIView):
    """
    Kayıt bilgilerini doğrular ve Gmail'e
    6 haneli doğrulama kodu gönderir.

    Kullanıcı bu aşamada henüz oluşturulmaz.
    """

    permission_classes = [AllowAny]

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        username = (
            serializer.validated_data[
                "username"
            ].strip()
        )

        email = _normalise_email(
            serializer.validated_data[
                "email"
            ]
        )

        password = (
            serializer.validated_data[
                "password"
            ]
        )

        code = (
            f"{secrets.randbelow(1_000_000):06d}"
        )

        pending_key = (
            _registration_pending_key(
                email
            )
        )

        attempts_key = (
            _registration_attempts_key(
                email
            )
        )

        cooldown_key = (
            _registration_cooldown_key(
                email
            )
        )

        cache.set(
            pending_key,
            {
                "username":
                    username,
                "email":
                    email,
                "password_hash":
                    make_password(
                        password
                    ),
                "code_hash":
                    _registration_code_hash(
                        email,
                        code,
                    ),
            },
            timeout=(
                settings
                .REGISTRATION_OTP_TIMEOUT
            ),
        )

        cache.set(
            attempts_key,
            0,
            timeout=(
                settings
                .REGISTRATION_OTP_TIMEOUT
            ),
        )

        cache.set(
            cooldown_key,
            True,
            timeout=(
                settings
                .REGISTRATION_RESEND_COOLDOWN
            ),
        )

        try:
            _send_registration_code(
                email,
                code,
            )
        except Exception:
            cache.delete(
                pending_key
            )
            cache.delete(
                attempts_key
            )
            cache.delete(
                cooldown_key
            )

            logger.exception(
                "Registration OTP "
                "email could not be sent."
            )

            return Response(
                {
                    "detail": (
                        "Doğrulama kodu "
                        "gönderilemedi. "
                        "Lütfen tekrar deneyin."
                    )
                },
                status=503,
            )

        return Response(
            {
                "detail": (
                    "Doğrulama kodu "
                    "e-posta adresinize gönderildi."
                ),
                "email": email,
                "cooldown_seconds": (
                    settings
                    .REGISTRATION_RESEND_COOLDOWN
                ),
            },
            status=200,
        )


class RegisterResendView(APIView):
    permission_classes = [AllowAny]

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "register_resend"

    def post(self, request):
        serializer = (
            RegisterResendSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        email = _normalise_email(
            serializer.validated_data[
                "email"
            ]
        )

        pending_key = (
            _registration_pending_key(
                email
            )
        )

        attempts_key = (
            _registration_attempts_key(
                email
            )
        )

        cooldown_key = (
            _registration_cooldown_key(
                email
            )
        )

        pending = cache.get(
            pending_key
        )

        if not pending:
            return Response(
                {
                    "detail": (
                        "Kayıt doğrulama "
                        "oturumunun süresi dolmuş. "
                        "Lütfen kayıt formunu "
                        "yeniden doldurun."
                    )
                },
                status=400,
            )

        if cache.get(
            cooldown_key
        ):
            return Response(
                {
                    "detail": (
                        "Yeni kod göndermek "
                        "için biraz bekleyin."
                    ),
                    "retry_after": (
                        settings
                        .REGISTRATION_RESEND_COOLDOWN
                    ),
                },
                status=429,
            )

        code = (
            f"{secrets.randbelow(1_000_000):06d}"
        )

        pending[
            "code_hash"
        ] = (
            _registration_code_hash(
                email,
                code,
            )
        )

        cache.set(
            pending_key,
            pending,
            timeout=(
                settings
                .REGISTRATION_OTP_TIMEOUT
            ),
        )

        cache.set(
            attempts_key,
            0,
            timeout=(
                settings
                .REGISTRATION_OTP_TIMEOUT
            ),
        )

        try:
            _send_registration_code(
                email,
                code,
            )
        except Exception:
            logger.exception(
                "Registration OTP resend "
                "email could not be sent."
            )

            return Response(
                {
                    "detail": (
                        "Doğrulama kodu "
                        "gönderilemedi."
                    )
                },
                status=503,
            )

        cache.set(
            cooldown_key,
            True,
            timeout=(
                settings
                .REGISTRATION_RESEND_COOLDOWN
            ),
        )

        return Response(
            {
                "detail":
                    "Yeni doğrulama kodu gönderildi.",
                "cooldown_seconds": (
                    settings
                    .REGISTRATION_RESEND_COOLDOWN
                ),
            },
            status=200,
        )


class RegisterVerifyView(APIView):
    """
    OTP doğruysa gerçek User kaydı burada oluşturulur.
    """

    permission_classes = [AllowAny]

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "register_verify"

    def post(self, request):
        serializer = (
            RegisterVerifySerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        email = _normalise_email(
            serializer.validated_data[
                "email"
            ]
        )

        code = (
            serializer.validated_data[
                "code"
            ]
        )

        pending_key = (
            _registration_pending_key(
                email
            )
        )

        attempts_key = (
            _registration_attempts_key(
                email
            )
        )

        cooldown_key = (
            _registration_cooldown_key(
                email
            )
        )

        pending = cache.get(
            pending_key
        )

        invalid_response = {
            "detail": (
                "Doğrulama kodu "
                "geçersiz veya süresi dolmuş."
            )
        }

        if not pending:
            return Response(
                invalid_response,
                status=400,
            )

        attempts = int(
            cache.get(
                attempts_key
            )
            or 0
        )

        if (
            attempts
            >= settings
            .REGISTRATION_MAX_ATTEMPTS
        ):
            cache.delete(
                pending_key
            )
            cache.delete(
                attempts_key
            )

            return Response(
                invalid_response,
                status=400,
            )

        expected_hash = (
            _registration_code_hash(
                email,
                code,
            )
        )

        if not hmac.compare_digest(
            expected_hash,
            pending["code_hash"],
        ):
            attempts += 1

            if (
                attempts
                >= settings
                .REGISTRATION_MAX_ATTEMPTS
            ):
                cache.delete(
                    pending_key
                )
                cache.delete(
                    attempts_key
                )
            else:
                cache.set(
                    attempts_key,
                    attempts,
                    timeout=(
                        settings
                        .REGISTRATION_OTP_TIMEOUT
                    ),
                )

            return Response(
                invalid_response,
                status=400,
            )

        username = pending[
            "username"
        ]

        if User.objects.filter(
            username__iexact=username
        ).exists():
            cache.delete(
                pending_key
            )

            return Response(
                {
                    "detail": (
                        "Bu kullanıcı adı "
                        "artık kullanılıyor. "
                        "Lütfen tekrar kayıt olun."
                    )
                },
                status=400,
            )

        if User.objects.filter(
            email__iexact=email
        ).exists():
            cache.delete(
                pending_key
            )

            return Response(
                {
                    "detail": (
                        "Bu e-posta adresi "
                        "zaten kullanılıyor."
                    )
                },
                status=400,
            )

        try:
            with transaction.atomic():
                user = User(
                    username=username,
                    email=email,
                )

                # Redis'te yalnızca Django password hash'i
                # tutuldu. Ham şifre saklanmıyor.
                user.password = (
                    pending[
                        "password_hash"
                    ]
                )

                # Model default'u viewer'dır.
                user.save()

        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "Kullanıcı hesabı "
                        "oluşturulamadı. "
                        "Lütfen tekrar deneyin."
                    )
                },
                status=400,
            )

        cache.delete(
            pending_key
        )
        cache.delete(
            attempts_key
        )
        cache.delete(
            cooldown_key
        )

        return Response(
            UserSerializer(
                user
            ).data,
            status=201,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get(
            "username"
        )

        password = request.data.get(
            "password"
        )

        user = User.objects.filter(
            username=username
        ).first()

        if (
            user is None
            or not user.check_password(
                password
            )
        ):
            return Response(
                {
                    "detail":
                        "Gecersiz kimlik bilgileri."
                },
                status=401,
            )

        refresh = RefreshToken.for_user(
            user
        )

        response = Response(
            UserSerializer(user).data,
            status=200,
        )

        _set_auth_cookies(
            response,
            str(refresh.access_token),
            str(refresh),
        )

        return response


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        raw_refresh = request.COOKIES.get(
            settings.JWT_AUTH_REFRESH_COOKIE
        )

        if not raw_refresh:
            return Response(
                {
                    "detail":
                        "Refresh token bulunamadi."
                },
                status=401,
            )

        try:
            serializer = (
                TokenRefreshSerializer(
                    data={
                        "refresh":
                            raw_refresh
                    }
                )
            )

            serializer.is_valid(
                raise_exception=True
            )
        except TokenError:
            return Response(
                {
                    "detail":
                        "Gecersiz refresh token."
                },
                status=401,
            )

        access = (
            serializer.validated_data[
                "access"
            ]
        )

        new_refresh = (
            serializer.validated_data.get(
                "refresh",
                raw_refresh,
            )
        )

        response = Response(
            {
                "detail":
                    "Token yenilendi."
            },
            status=200,
        )

        _set_auth_cookies(
            response,
            access,
            new_refresh,
        )

        return response


class LogoutView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):
        response = Response(
            {
                "detail":
                    "Cikis yapildi."
            },
            status=200,
        )

        response.delete_cookie(
            settings.JWT_AUTH_COOKIE
        )

        response.delete_cookie(
            settings.JWT_AUTH_REFRESH_COOKIE
        )

        return response


class MeView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        return Response(
            UserSerializer(
                request.user
            ).data
        )


class PasswordResetRequestView(
    APIView
):
    permission_classes = [AllowAny]

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = (
        "password_reset_request"
    )

    def post(self, request):
        serializer = (
            PasswordResetRequestSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        email = _normalise_email(
            serializer.validated_data[
                "email"
            ]
        )

        generic_detail = (
            "Bu e-posta adresiyle "
            "eşleşen bir hesap varsa, "
            "6 haneli doğrulama kodu "
            "gönderildi."
        )

        cooldown_key = (
            _cooldown_cache_key(
                email
            )
        )

        if cache.get(cooldown_key):
            return Response(
                {
                    "detail":
                        generic_detail,
                    "cooldown_seconds":
                        settings
                        .PASSWORD_RESET_RESEND_COOLDOWN,
                },
                status=200,
            )

        cache.set(
            cooldown_key,
            True,
            timeout=(
                settings
                .PASSWORD_RESET_RESEND_COOLDOWN
            ),
        )

        user = (
            User.objects.filter(
                email__iexact=email,
                is_active=True,
            )
            .exclude(email="")
            .order_by("id")
            .first()
        )

        if user is not None:
            code = (
                f"{secrets.randbelow(1_000_000):06d}"
            )

            otp_key = (
                _otp_cache_key(
                    email
                )
            )

            attempts_key = (
                _attempts_cache_key(
                    email
                )
            )

            cache.set(
                otp_key,
                {
                    "user_id":
                        user.pk,
                    "code_hash":
                        _otp_hash(
                            user.pk,
                            code,
                        ),
                },
                timeout=(
                    settings
                    .PASSWORD_RESET_OTP_TIMEOUT
                ),
            )

            cache.set(
                attempts_key,
                0,
                timeout=(
                    settings
                    .PASSWORD_RESET_OTP_TIMEOUT
                ),
            )

            try:
                send_password_reset_otp_email(
                    recipient=user.email,
                    code=code,
                    timeout_minutes=max(
                        1,
                        settings
                        .PASSWORD_RESET_OTP_TIMEOUT
                        // 60,
                    ),
                )
            except Exception:
                cache.delete(
                    otp_key
                )

                cache.delete(
                    attempts_key
                )

                logger.exception(
                    "Password reset OTP "
                    "email could not be sent."
                )

        return Response(
            {
                "detail":
                    generic_detail,
                "cooldown_seconds":
                    settings
                    .PASSWORD_RESET_RESEND_COOLDOWN,
            },
            status=200,
        )


class PasswordResetVerifyView(
    APIView
):
    permission_classes = [AllowAny]

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = (
        "password_reset_verify"
    )

    def post(self, request):
        serializer = (
            PasswordResetVerifySerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        email = _normalise_email(
            serializer.validated_data[
                "email"
            ]
        )

        code = (
            serializer.validated_data[
                "code"
            ]
        )

        otp_key = (
            _otp_cache_key(email)
        )

        attempts_key = (
            _attempts_cache_key(
                email
            )
        )

        record = cache.get(
            otp_key
        )

        invalid_response = {
            "detail": (
                "Doğrulama kodu "
                "geçersiz veya süresi dolmuş."
            )
        }

        if not record:
            return Response(
                invalid_response,
                status=400,
            )

        attempts = int(
            cache.get(
                attempts_key
            )
            or 0
        )

        if (
            attempts
            >= settings
            .PASSWORD_RESET_MAX_ATTEMPTS
        ):
            cache.delete(
                otp_key
            )

            cache.delete(
                attempts_key
            )

            return Response(
                invalid_response,
                status=400,
            )

        expected_hash = _otp_hash(
            record["user_id"],
            code,
        )

        if not hmac.compare_digest(
            expected_hash,
            record["code_hash"],
        ):
            attempts += 1

            if (
                attempts
                >= settings
                .PASSWORD_RESET_MAX_ATTEMPTS
            ):
                cache.delete(
                    otp_key
                )

                cache.delete(
                    attempts_key
                )
            else:
                cache.set(
                    attempts_key,
                    attempts,
                    timeout=(
                        settings
                        .PASSWORD_RESET_OTP_TIMEOUT
                    ),
                )

            return Response(
                invalid_response,
                status=400,
            )

        try:
            user = User.objects.get(
                pk=record["user_id"],
                is_active=True,
            )
        except User.DoesNotExist:
            cache.delete(
                otp_key
            )

            cache.delete(
                attempts_key
            )

            return Response(
                invalid_response,
                status=400,
            )

        cache.delete(
            otp_key
        )

        cache.delete(
            attempts_key
        )

        reset_token = (
            secrets.token_urlsafe(32)
        )

        cache.set(
            _reset_token_cache_key(
                reset_token
            ),
            user.pk,
            timeout=(
                settings
                .PASSWORD_RESET_TOKEN_TIMEOUT
            ),
        )

        return Response(
            {
                "detail":
                    "E-posta doğrulandı.",
                "reset_token":
                    reset_token,
            },
            status=200,
        )


class PasswordResetConfirmView(
    APIView
):
    permission_classes = [AllowAny]

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = (
        "password_reset_confirm"
    )

    def post(self, request):
        serializer = (
            PasswordResetConfirmSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        reset_token = (
            serializer.validated_data[
                "reset_token"
            ]
        )

        new_password = (
            serializer.validated_data[
                "new_password"
            ]
        )

        token_key = (
            _reset_token_cache_key(
                reset_token
            )
        )

        user_id = cache.get(
            token_key
        )

        if not user_id:
            return Response(
                {
                    "detail": (
                        "Şifre sıfırlama "
                        "oturumu geçersiz "
                        "veya süresi dolmuş."
                    )
                },
                status=400,
            )

        try:
            user = User.objects.get(
                pk=user_id,
                is_active=True,
            )
        except User.DoesNotExist:
            cache.delete(
                token_key
            )

            return Response(
                {
                    "detail": (
                        "Şifre sıfırlama "
                        "oturumu geçersiz "
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
                        list(
                            exc.messages
                        )
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

        cache.delete(
            token_key
        )

        return Response(
            {
                "detail":
                    "Şifreniz başarıyla güncellendi."
            },
            status=200,
        )


class UserListView(APIView):
    """
    Admin kullanıcı listesi.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminRole,
    ]

    def get(self, request):
        users = (
            User.objects
            .all()
            .order_by(
                "-date_joined"
            )
        )

        return Response(
            UserSerializer(
                users,
                many=True,
            ).data
        )


class UserRoleUpdateView(APIView):
    """
    Başka bir kullanıcının VERITAS rolünü
    admin tarafından değiştirir.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminRole,
    ]

    def patch(
        self,
        request,
        user_id: int,
    ):
        target = (
            User.objects
            .filter(
                id=user_id
            )
            .first()
        )

        if target is None:
            return Response(
                {
                    "detail":
                        "Kullanıcı bulunamadı."
                },
                status=404,
            )

        if (
            target.id
            == request.user.id
        ):
            return Response(
                {
                    "detail": (
                        "Kendi rolünüzü "
                        "değiştiremezsiniz."
                    )
                },
                status=400,
            )

        serializer = (
            UserRoleUpdateSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        target.role = (
            serializer.validated_data[
                "role"
            ]
        )

        target.save(
            update_fields=[
                "role",
            ]
        )

        return Response(
            UserSerializer(
                target
            ).data
        )
