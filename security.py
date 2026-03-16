from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from config import get_settings
from schemas import TokenPayload


class TokenValidationError(ValueError):
    pass


def _urlsafe_b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _urlsafe_b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}".encode("ascii"))


def _sign(value: str) -> str:
    settings = get_settings()
    digest = hmac.new(
        settings.auth_secret.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _urlsafe_b64encode(digest)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    encoded_payload = _urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = _sign(encoded_payload)
    return f"{encoded_payload}.{signature}"


def decode_access_token(token: str) -> TokenPayload:
    try:
        encoded_payload, provided_signature = token.split(".", maxsplit=1)
    except ValueError as exc:
        raise TokenValidationError("Malformed access token.") from exc

    expected_signature = _sign(encoded_payload)
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise TokenValidationError("Invalid access token signature.")

    try:
        payload = json.loads(_urlsafe_b64decode(encoded_payload))
    except (ValueError, json.JSONDecodeError) as exc:
        raise TokenValidationError("Invalid access token payload.") from exc

    subject = payload.get("sub")
    expires_at = payload.get("exp")
    if not isinstance(subject, str) or not subject:
        raise TokenValidationError("Access token subject is missing.")
    if not isinstance(expires_at, int):
        raise TokenValidationError("Access token expiration is missing.")
    if expires_at <= int(datetime.now(timezone.utc).timestamp()):
        raise TokenValidationError("Access token has expired.")

    return TokenPayload(subject=subject, expires_at=expires_at)
