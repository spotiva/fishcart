import hashlib
import hmac
import secrets
import base64
from datetime import timedelta
from pathlib import Path

import resend
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.template.loader import render_to_string

from .models import LoginOTP


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def digest_otp(email: str, code: str) -> str:
    material = f"{email}:{code}".encode()
    return hmac.new(settings.OTP_PEPPER.encode(), material, hashlib.sha256).hexdigest()


def create_login_otp(email: str) -> str:
    code = generate_otp()
    now = timezone.now()
    LoginOTP.objects.filter(email=email, consumed_at__isnull=True).update(consumed_at=now)
    LoginOTP.objects.create(email=email, code_digest=digest_otp(email, code), expires_at=now + timedelta(seconds=settings.OTP_TTL_SECONDS))
    return code


@transaction.atomic
def verify_login_otp(email: str, code: str) -> bool:
    now = timezone.now()
    otp = LoginOTP.objects.select_for_update().filter(email=email, consumed_at__isnull=True, expires_at__gt=now).order_by("-created_at").first()
    if otp is None or otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        return False
    otp.attempts += 1
    valid = hmac.compare_digest(otp.code_digest, digest_otp(email, code))
    if valid:
        otp.consumed_at = now
    otp.save(update_fields=["attempts", "consumed_at"])
    return valid


def send_login_otp_email(email: str, code: str) -> None:
    """Send the branded OTP using Resend's HTTPS API, without logging secrets."""
    if not settings.RESEND_API_KEY:
        raise ImproperlyConfigured("RESEND_API_KEY is not configured")

    expiry_minutes = max(1, (settings.OTP_TTL_SECONDS + 59) // 60)
    logo_path = Path(__file__).parent / "email_assets" / "machli-logo.jpeg"
    context = {"code": code, "expiry_minutes": expiry_minutes, "brand_name": "machli", "has_logo": logo_path.is_file()}
    params = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": [email],
        "subject": "Your machli sign-in code",
        "text": render_to_string("users/emails/otp.txt", context),
        "html": render_to_string("users/emails/otp.html", context),
    }
    if logo_path.is_file():
        params["attachments"] = [{
            "filename": logo_path.name,
            "content": base64.b64encode(logo_path.read_bytes()).decode("ascii"),
            "content_type": "image/jpeg",
            "content_id": "machli-logo",
        }]

    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send(params)
