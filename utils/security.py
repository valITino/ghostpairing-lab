"""
Security helpers — input sanitization, token validation, safe formatting.
"""
import hashlib
import hmac
import secrets
from typing import Optional


def safe_truncate(value: str, max_len: int = 50) -> str:
    """Truncate a string safely for display/logging."""
    if len(value) <= max_len:
        return value
    return value[:max_len - 3] + "..."


def redact_phone(phone: str) -> str:
    """Redact a phone number for logging: +1234***"""
    if not phone or len(phone) < 5:
        return "***"
    return phone[:5] + "*" * (len(phone) - 5)


def sanitize_filename(name: str) -> str:
    """Remove path traversal and special chars from a filename."""
    import re
    return re.sub(r"[^\w\-.]", "_", name)


def constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())


def validate_admin_token(token: Optional[str]) -> bool:
    """Validate the admin authorization token."""
    from config import ADMIN_TOKEN
    if not token:
        return False
    # Support "Bearer <token>" or raw token
    if token.startswith("Bearer "):
        token = token[7:]
    return constant_time_compare(token, ADMIN_TOKEN)


def generate_session_id() -> str:
    """Generate a cryptographically random session ID."""
    return secrets.token_hex(16)
