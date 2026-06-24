"""
Playwright browser lifecycle manager.
Singleton browser instance with session persistence and graceful cleanup.
"""
import threading
from typing import Optional

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Playwright

from config import (
    BROWSER_HEADLESS,
    BROWSER_SLOW_MO,
    BROWSER_PROFILE_DIR,
    SESSION_STORAGE_FILE,
)
from automation.stealth import create_stealth_context, save_session
from core.logging_config import get_logger

logger = get_logger(__name__)


class BrowserManager:
    """Singleton manager for Playwright browser lifecycle."""

    _instance: Optional["BrowserManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    def start(self) -> BrowserContext:
        """Launch browser and return a fresh context. Reuses existing browser if alive."""
        if self._browser and self._browser.is_connected():
            logger.info("Reusing existing browser instance")
            context = self._create_context()
            self._context = context
            return context

        logger.info("Launching Firefox via Playwright")
        try:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.firefox.launch(
                headless=BROWSER_HEADLESS,
                slow_mo=BROWSER_SLOW_MO,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    f"--window-size=1280,720",
                ],
            )
            context = self._create_context()
            self._context = context
            logger.info("Browser launched successfully")
            return context
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise

    def _create_context(self) -> BrowserContext:
        """Create a new browser context with anti-detection."""
        import os

        # Try to restore session if storage state exists
        if os.path.exists(SESSION_STORAGE_FILE):
            try:
                context = self._browser.new_context(
                    storage_state=SESSION_STORAGE_FILE,
                )
                logger.info("Restored previous browser session")
                return context
            except Exception as e:
                logger.warning(f"Failed to restore session: {e}")

        return create_stealth_context(self._browser)

    def save_session_state(self) -> None:
        """Persist current browser session for next launch."""
        if self._context:
            save_session(self._context)
            logger.info("Browser session saved")

    @property
    def browser(self) -> Optional[Browser]:
        return self._browser

    @property
    def is_running(self) -> bool:
        return self._browser is not None and self._browser.is_connected()

    def cleanup(self) -> None:
        """Gracefully shut down browser and playwright."""
        logger.info("Cleaning up browser resources")
        try:
            if self._context:
                self._context.close()
                self._context = None
        except Exception as e:
            logger.debug(f"Error closing context: {e}")

        try:
            if self._browser:
                self._browser.close()
                self._browser = None
        except Exception as e:
            logger.debug(f"Error closing browser: {e}")

        try:
            if self._playwright:
                self._playwright.stop()
                self._playwright = None
        except Exception as e:
            logger.debug(f"Error stopping playwright: {e}")

        logger.info("Browser cleanup complete")


# Singleton accessor
def get_browser_manager() -> BrowserManager:
    return BrowserManager()
