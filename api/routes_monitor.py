"""
WebSocket monitoring endpoint for real-time attack tracking.
"""
import asyncio
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.websocket_manager import ws_manager
from core.database import db
from automation.pairing_flow import whatsapp_api
from core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """WebSocket for real-time attack monitoring dashboard."""
    client_id = f"monitor_{uuid.uuid4().hex[:8]}"

    try:
        cid = await ws_manager.connect(websocket, client_id)
        logger.info(f"Monitor connected: {cid}")

        # Send initial stats
        stats = db.get_stats()
        await websocket.send_json({
            "type": "init",
            "client_id": cid,
            "stats": stats,
            "message": "Connected to GhostPairing Automation Monitor",
            "active_automations": len(whatsapp_api.get_active_automations()),
        })

        # Keep connection alive with ping/pong
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0,
                )

                msg_type = data.get("type")
                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "get_stats":
                    stats = db.get_stats()
                    await websocket.send_json({
                        "type": "stats_update",
                        "stats": stats,
                        "active_automations": len(
                            whatsapp_api.get_active_automations()
                        ),
                    })

            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        logger.info(f"Monitor disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket, client_id)
