from django.conf import settings
from django.core.mail import (
    EmailMultiAlternatives,
)
from django.template.loader import (
    render_to_string,
)


def _send_veritas_otp_email(
    *,
    recipient: str,
    code: str,
    subject: str,
    eyebrow: str,
    title: str,
    intro: str,
    timeout_minutes: int,
    security_note: str,
) -> int:
    plain_text = (
        f"VERITAS\n\n"
        f"{title}\n\n"
        f"{intro}\n\n"
        f"Doğrulama kodu: {code}\n\n"
        f"Bu kod {timeout_minutes} dakika "
        f"geçerlidir.\n\n"
        f"{security_note}"
    )

    html_content = render_to_string(
        "emails/otp_email.html",
        {
            "eyebrow": eyebrow,
            "title": title,
            "intro": intro,
            "code": code,
            "timeout_minutes":
                timeout_minutes,
            "security_note":
                security_note,
        },
    )

    message = EmailMultiAlternatives(
        subject=subject,
        body=plain_text,
        from_email=(
            settings.DEFAULT_FROM_EMAIL
        ),
        to=[recipient],
    )

    message.attach_alternative(
        html_content,
        "text/html",
    )

    return message.send(
        fail_silently=False
    )


def send_registration_otp_email(
    *,
    recipient: str,
    code: str,
    timeout_minutes: int,
) -> int:
    return _send_veritas_otp_email(
        recipient=recipient,
        code=code,
        subject=(
            "VERITAS e-posta "
            "doğrulama kodu"
        ),
        eyebrow="Güvenli kayıt",
        title="E-postanızı doğrulayın",
        intro=(
            "VERITAS hesabınızı "
            "oluşturmak için aşağıdaki "
            "6 haneli doğrulama kodunu "
            "kullanın."
        ),
        timeout_minutes=(
            timeout_minutes
        ),
        security_note=(
            "Bu kayıt işlemini siz "
            "başlatmadıysanız bu "
            "e-postayı yok sayabilirsiniz."
        ),
    )


def send_password_reset_otp_email(
    *,
    recipient: str,
    code: str,
    timeout_minutes: int,
) -> int:
    return _send_veritas_otp_email(
        recipient=recipient,
        code=code,
        subject=(
            "VERITAS şifre sıfırlama "
            "doğrulama kodu"
        ),
        eyebrow="Hesap güvenliği",
        title="Şifrenizi sıfırlayın",
        intro=(
            "VERITAS hesabınızın "
            "şifresini sıfırlamak için "
            "aşağıdaki 6 haneli "
            "doğrulama kodunu kullanın."
        ),
        timeout_minutes=(
            timeout_minutes
        ),
        security_note=(
            "Bu şifre sıfırlama "
            "talebini siz yapmadıysanız "
            "bu e-postayı yok "
            "sayabilirsiniz."
        ),
    )
