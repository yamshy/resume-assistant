"""Security helpers for token generation and hashing."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from app.config import get_settings


def generate_token(subject: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expires_delta = expires_delta or timedelta(
        minutes=settings.access_token_expire_minutes
    )
    expiry = int((datetime.now(timezone.utc) + expires_delta).timestamp())
    payload = f"{subject}:{expiry}".encode()
    signature = hmac.new(settings.secret_key.encode(), payload, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(payload + b"." + signature).decode()
    return token


def verify_token(token: str) -> bool:
    settings = get_settings()
    try:
        decoded = base64.urlsafe_b64decode(token.encode())
    except Exception:
        return False
    try:
        payload, signature = decoded.split(b".")
    except ValueError:
        return False
    expected = hmac.new(settings.secret_key.encode(), payload, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        return False
    try:
        subject, expiry = payload.decode().split(":")
    except ValueError:
        return False
    return int(expiry) >= int(datetime.now(timezone.utc).timestamp()) and bool(subject)


def hash_content(content: str) -> str:
    salt = os.environ.get("RESUME_HASH_SALT", "resume")
    digest = hashlib.sha256(f"{salt}:{content}".encode()).hexdigest()
    return digest


def fingerprint_job_posting(text: str) -> str:
    normalized = " ".join(text.lower().split())
    return hash_content(normalized)


__all__ = [
    "generate_token",
    "verify_token",
    "hash_content",
    "fingerprint_job_posting",
]
