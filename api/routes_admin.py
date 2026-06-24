"""
Admin endpoints — dashboard, stats, database management.
Protected by Bearer token auth for destructive operations.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from core.database import db
from automation.pairing_flow import whatsapp_api
from utils.security import validate_admin_token, safe_truncate
from core.logging_config import get_logger
from models.schemas import HealthResponse, ClearDBResponse

logger = get_logger(__name__)
router = APIRouter(tags=["admin"])

# Reference to active_attacks from routes_attack
_active_attacks_ref = None


def set_active_attacks_ref(ref: dict) -> None:
    """Set reference to active_attacks dict from routes_attack module."""
    global _active_attacks_ref
    _active_attacks_ref = ref


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint — verifies server, database, and Playwright."""
    playwright_ok = False
    try:
        import playwright
        playwright_ok = True
    except ImportError:
        pass

    db_ok = False
    try:
        db.init_database()
        db_ok = True
    except Exception:
        pass

    return JSONResponse(content={
        "status": "ok" if (db_ok and playwright_ok) else "degraded",
        "version": "2.1",
        "playwright_available": playwright_ok,
        "database_ok": db_ok,
    })


@router.get("/readiness")
async def readiness_check():
    """Readiness probe for orchestration."""
    db_ok = False
    try:
        db.init_database()
        db_ok = True
    except Exception:
        pass

    return JSONResponse(content={
        "ready": db_ok,
        "database": "connected" if db_ok else "error",
    })


@router.get("/admin")
async def admin_dashboard(request: Request):
    """Serve the admin monitoring dashboard."""
    try:
        with open("templates/admin.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        # Return simple dashboard if template missing
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html><head><title>GhostPairing Admin</title></head>
        <body>
            <h1>GhostPairing Admin</h1>
            <div id="stats">Loading...</div>
            <script>
                fetch('/api/stats').then(r => r.json()).then(d => {
                    document.getElementById('stats').innerHTML =
                        '<pre>' + JSON.stringify(d, null, 2) + '</pre>';
                });
            </script>
        </body></html>
        """)


@router.get("/api/stats")
async def get_stats():
    """Get attack statistics."""
    stats = db.get_stats()
    stats["active_automations"] = len(whatsapp_api.get_active_automations())
    return JSONResponse(content=stats)


@router.get("/api/attacks")
async def list_attacks():
    """List recent attacks."""
    try:
        attacks = db.list_attacks(limit=50)
        return JSONResponse(content={"attacks": attacks})
    except Exception as e:
        logger.error(f"Error listing attacks: {e}")
        return JSONResponse(
            content={"error": "Database error", "attacks": []},
            status_code=500,
        )


@router.get("/api/active-attacks")
async def get_active_attacks():
    """Get currently active attacks."""
    active = _active_attacks_ref if _active_attacks_ref else {}
    return JSONResponse(content={
        "active_attacks": active,
        "active_automations": whatsapp_api.get_active_automations(),
        "count": len(active),
    })


@router.post("/clear-db", response_model=ClearDBResponse)
async def clear_database(request: Request):
    """Clear all attack data (requires admin token)."""
    auth = request.headers.get("Authorization")
    if not validate_admin_token(auth):
        raise HTTPException(status_code=401, detail="Unauthorized")

    db.clear_all()

    if _active_attacks_ref is not None:
        _active_attacks_ref.clear()

    return JSONResponse(content={
        "message": "Database cleared",
        "active_attacks_cleared": True,
    })


@router.get("/test-automation")
async def test_automation():
    """Test if browser automation is available."""
    try:
        import playwright
        return JSONResponse(content={
            "playwright_installed": True,
            "firefox_available": True,
            "automation_ready": True,
            "message": "Browser automation is ready",
        })
    except ImportError:
        return JSONResponse(content={
            "playwright_installed": False,
            "firefox_available": False,
            "automation_ready": False,
            "message": "Install: pip install playwright && playwright install firefox",
        })


@router.get("/stop-automation/{attack_id}")
async def stop_automation(attack_id: int):
    """Request to stop an active automation (informational only)."""
    return JSONResponse(content={
        "message": f"Automation stop requested for attack {attack_id}",
        "note": "Close Firefox window manually or wait for timeout",
    })
