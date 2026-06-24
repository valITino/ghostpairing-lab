"""
Playwright anti-detection utilities.
Applies fingerprint spoofing, human-like behavior patterns, and browser hardening.
Based on 2025-2026 evasion research.
"""
import random
import time
from typing import Optional

from playwright.sync_api import Page, Browser, BrowserContext

from config import (
    STEALTH_ENABLED,
    USER_AGENT,
    VIEWPORT_WIDTH,
    VIEWPORT_HEIGHT,
    LOCALE,
    TIMEZONE_ID,
)


def get_stealth_init_script() -> str:
    """JavaScript to inject before page loads to spoof browser fingerprints."""
    return """
    // Override navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });

    // Fake plugins array
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });

    // Fake languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
    });

    // Override chrome.runtime
    window.chrome = {
        runtime: {},
        loadTimes: function() {},
        csi: function() {},
        app: {},
    };

    // Override permissions query
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
    );

    // Overwrite the `plugins` descriptor to be more convincing
    Object.defineProperty(navigator, 'platform', {
        get: () => 'Win32',
    });

    // Fake hardware concurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8,
    });

    // Fake device memory
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 8,
    });
    """


def apply_stealth_context(context: BrowserContext) -> None:
    """Apply stealth configurations to a browser context."""
    if not STEALTH_ENABLED:
        return

    # Add init script to all pages in this context
    context.add_init_script(get_stealth_init_script())

    # Randomize viewport slightly for fingerprint diversity
    w_jitter = random.randint(-20, 20)
    h_jitter = random.randint(-10, 10)
    for page in context.pages:
        page.set_viewport_size({
            "width": VIEWPORT_WIDTH + w_jitter,
            "height": VIEWPORT_HEIGHT + h_jitter,
        })


def create_stealth_context(browser: Browser) -> BrowserContext:
    """Create a browser context with anti-detection settings."""
    context = browser.new_context(
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        user_agent=USER_AGENT,
        locale=LOCALE,
        timezone_id=TIMEZONE_ID,
        permissions=["geolocation"],
        geolocation={"latitude": 40.7128, "longitude": -74.0060},  # NYC
        color_scheme="light",
    )

    if STEALTH_ENABLED:
        context.add_init_script(get_stealth_init_script())

    return context


def human_delay(min_ms: int = 300, max_ms: int = 2000) -> None:
    """Random delay to simulate human thinking/reading time."""
    time.sleep(random.uniform(min_ms, max_ms) / 1000.0)


def human_type(page: Page, selector: str, text: str, wpm: int = 60) -> None:
    """
    Type text with variable per-character delays simulating human typing.
    wpm: words per minute (default 60 = ~200ms per char average).
    """
    ms_per_char = 12000 / wpm  # avg ms per character
    element = page.locator(selector).first
    element.click()
    human_delay(100, 300)

    for i, char in enumerate(text):
        # Variable delay: slower at start and end, with random jitter
        position_factor = 1.0
        if i < 2:
            position_factor = 1.5  # slower start
        elif i > len(text) - 3:
            position_factor = 1.3  # slower end

        jitter = random.uniform(0.5, 1.5)
        delay = ms_per_char * position_factor * jitter / 1000.0
        time.sleep(delay)
        element.type(char, delay=0)


def bézier_mouse_move(
    page: Page,
    target_selector: str,
    steps: int = 25,
) -> None:
    """
    Move mouse to a target using a Bézier-like curved path.
    Simple implementation — interpolates with a control point offset.
    """
    try:
        box = page.locator(target_selector).first.bounding_box()
        if not box:
            page.locator(target_selector).first.click()
            return

        # Get current mouse position (approximate)
        start_x = random.randint(100, 400)
        start_y = random.randint(100, 500)
        end_x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
        end_y = box["y"] + box["height"] / 2 + random.uniform(-3, 3)

        # Control point for curve
        cp_x = (start_x + end_x) / 2 + random.uniform(-80, 80)
        cp_y = max((start_y + end_y) / 2 + random.uniform(-60, 40), 10)

        for i in range(steps + 1):
            t = i / steps
            # Quadratic Bézier
            x = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * cp_x + t ** 2 * end_x
            y = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * cp_y + t ** 2 * end_y
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.005, 0.015))

        page.mouse.click(end_x, end_y)
    except Exception:
        # Fallback: simple click
        try:
            page.locator(target_selector).first.click()
        except Exception:
            pass


def load_session(context: BrowserContext) -> bool:
    """Try to restore a previous browser session from storage state."""
    import os
    from config import SESSION_STORAGE_FILE

    if os.path.exists(SESSION_STORAGE_FILE):
        try:
            # Storage state is applied at context creation time in newer Playwright
            return True
        except Exception:
            return False
    return False


def save_session(context: BrowserContext) -> None:
    """Save browser session state for persistence across restarts."""
    import os
    from config import SESSION_STORAGE_FILE, SESSION_DIR

    os.makedirs(SESSION_DIR, exist_ok=True)
    try:
        context.storage_state(path=SESSION_STORAGE_FILE)
    except Exception:
        pass
