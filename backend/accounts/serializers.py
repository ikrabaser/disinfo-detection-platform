from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "date_joined",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False,
    )

    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "confirm_password",
        ]

    def validate_username(self, value):
        value = value.strip()

        if User.objects.filter(
            username__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "Bu kullanıcı adı zaten kullanılıyor."
            )

        return value

    def validate_email(self, value):
        value = value.strip().lower()

        if User.objects.filter(
            email__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "Bu e-posta adresi zaten kullanılıyor."
            )

        return value

    def validate_password(self, value):
        try:
            django_validate_password(
                value
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                list(exc.messages)
            ) from exc

        return value

    def validate(self, attrs):
        if (
            attrs["password"]
            != attrs["confirm_password"]
        ):
            raise serializers.ValidationError(
                {
                    "confirm_password":
                        "Şifreler eşleşmiyor."
                }
            )

        return attrs


class RegisterVerifySerializer(
    serializers.Serializer
):
    email = serializers.EmailField()

    code = serializers.RegexField(
        regex=r"^\d{6}$",
        error_messages={
            "invalid":
                "Doğrulama kodu 6 haneli olmalıdır."
        },
    )


class RegisterResendSerializer(
    serializers.Serializer
):
    email = serializers.EmailField()


class PasswordResetRequestSerializer(
    serializers.Serializer
):
    email = serializers.EmailField()


class PasswordResetVerifySerializer(
    serializers.Serializer
):
    email = serializers.EmailField()

    code = serializers.RegexField(
        regex=r"^\d{6}$",
        error_messages={
            "invalid":
                "Doğrulama kodu 6 haneli olmalıdır."
        },
    )


class PasswordResetConfirmSerializer(
    serializers.Serializer
):
    reset_token = serializers.CharField(
        min_length=20
    )

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False,
    )

    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        if (
            attrs["new_password"]
            != attrs["confirm_password"]
        ):
            raise serializers.ValidationError(
                {
                    "confirm_password":
                        "Şifreler eşleşmiyor."
                }
            )

        return attrs
