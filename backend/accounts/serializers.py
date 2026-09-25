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
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "role",
        ]

    def create(self, validated_data):
        password = validated_data.pop(
            "password"
        )

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


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
