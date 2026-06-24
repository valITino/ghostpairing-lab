"""
WhatsApp Web DOM selectors — centralized with fallback chains.
Update this file when WhatsApp changes its UI. Nothing else needs to change.
"""
import re
from typing import List, Pattern

from config import (
    LINK_PHONE_BUTTONS,
    PHONE_INPUTS,
    NEXT_BUTTONS,
    CODE_INPUTS,
    DIGIT_INPUTS,
    VERIFY_BUTTONS,
    SUCCESS_INDICATORS,
    CODE_DISPLAY_PATTERN,
    WHATSAPP_URL,
)


class WhatsAppSelectors:
    """All selectors and patterns for WhatsApp Web interaction."""

    # URL
    BASE_URL = WHATSAPP_URL

    # Multi-step selectors with fallback chains
    LINK_PHONE_BUTTONS: List[str] = LINK_PHONE_BUTTONS
    PHONE_INPUTS: List[str] = PHONE_INPUTS
    NEXT_BUTTONS: List[str] = NEXT_BUTTONS
    CODE_INPUTS: List[str] = CODE_INPUTS
    DIGIT_INPUTS: List[str] = DIGIT_INPUTS
    VERIFY_BUTTONS: List[str] = VERIFY_BUTTONS
    SUCCESS_INDICATORS: List[str] = SUCCESS_INDICATORS

    # Pattern for displayed code: XXXX-XXXX
    CODE_DISPLAY_PATTERN: Pattern = CODE_DISPLAY_PATTERN

    # Code extraction JavaScript strategies
    CODE_EXTRACTION_STRATEGIES = {
        "structured_dom": """
            () => {
                const headings = Array.from(document.querySelectorAll('*'));
                const heading = headings.find(el =>
                    el.textContent.includes('Enter code on phone')
                );
                if (!heading) return null;
                let parent = heading.parentElement;
                while (parent && parent !== document.body) {
                    const children = Array.from(parent.querySelectorAll('*'));
                    const singleChars = children.filter(el => {
                        const text = el.textContent.trim();
                        return text.length === 1 &&
                               text.match(/[A-Z0-9-]/i) &&
                               el.children.length === 0;
                    });
                    if (singleChars.length >= 8) {
                        return singleChars.slice(0, 9)
                            .map(el => el.textContent.trim().toUpperCase())
                            .join('');
                    }
                    parent = parent.parentElement;
                }
                return null;
            }
        """,
        "leaf_nodes": """
            () => {
                const allElements = Array.from(document.querySelectorAll('*'));
                const leafChars = allElements
                    .filter(el => {
                        const text = el.textContent.trim();
                        return text.length === 1 &&
                               text.match(/[A-Z0-9-]/i) &&
                               el.children.length === 0 &&
                               el.offsetParent !== null;
                    })
                    .map(el => el.textContent.trim().toUpperCase());
                return leafChars.slice(0, 20).join('');
            }
        """,
    }
