"""
MITMProxy addon for intercepting WhatsApp traffic.
Extracted from run.sh — now a proper importable Python module.
"""
import re
from mitmproxy import http
import logging

logger = logging.getLogger("mitmproxy.whatsapp")


def request(flow: http.HTTPFlow) -> None:
    """Intercept WhatsApp verification requests."""
    if not flow.request.host:
        return

    if "whatsapp" in flow.request.host or "wa.me" in flow.request.host:
        logger.info(f"WhatsApp request: {flow.request.method} {flow.request.url}")

        if flow.request.content:
            try:
                content = flow.request.content.decode("utf-8", errors="ignore")
                if "phone" in content.lower() or "number" in content.lower():
                    logger.info("Possible phone number in WhatsApp request")

                    phone_match = re.search(
                        r"phone[^0-9]*([0-9+]{10,})", content, re.IGNORECASE
                    )
                    if phone_match:
                        phone = phone_match.group(1)
                        logger.info(f"Extracted phone number: {phone}")

                        try:
                            import requests
                            requests.post(
                                "http://localhost:8000/api/mitm-phone",
                                json={"phone": phone, "source": "mitmproxy"},
                                timeout=1,
                            )
                        except Exception:
                            pass
            except Exception as e:
                logger.debug(f"Error decoding request: {e}")


def response(flow: http.HTTPFlow) -> None:
    """Intercept WhatsApp verification responses."""
    if not flow.response or not flow.response.content:
        return

    try:
        content = flow.response.content.decode("utf-8", errors="ignore")

        if "code" in content.lower() and (
            "whatsapp" in flow.request.host or "verify" in content.lower()
        ):
            codes = re.findall(r"\b\d{6}\b", content)
            for code in codes:
                logger.warning(f"INTERCEPTED VERIFICATION CODE: {code}")

                try:
                    import requests
                    requests.post(
                        "http://localhost:8000/api/intercept",
                        json={
                            "code": code,
                            "source": "mitmproxy",
                            "host": flow.request.host,
                        },
                        timeout=1,
                    )
                except Exception:
                    pass
    except Exception as e:
        logger.debug(f"Error in response handler: {e}")
