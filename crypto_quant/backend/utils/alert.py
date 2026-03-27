"""
Advanced Telegram Alert System (Quant-Grade)

Adds:
- Retry logic
- Rate limit handling
- Async sending
- Deduplication
- Priority tagging
"""

import os
import json
import time
import hashlib
import threading
import urllib.request
import urllib.error
from typing import Optional


class TelegramConfigError(Exception):
    pass


class TelegramAPIError(Exception):
    pass


# =========================
# Config
# =========================

def _get_config():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise TelegramConfigError("Telegram config missing")

    return token, chat_id


# =========================
# Deduplication Cache
# =========================

_sent_cache = {}
CACHE_TTL = 60  # seconds


def _is_duplicate(message: str) -> bool:
    key = hashlib.md5(message.encode()).hexdigest()
    now = time.time()

    # Cleanup old entries
    for k in list(_sent_cache.keys()):
        if now - _sent_cache[k] > CACHE_TTL:
            del _sent_cache[k]

    if key in _sent_cache:
        return True

    _sent_cache[key] = now
    return False


# =========================
# Core Send
# =========================

def _send_request(payload: dict, retries: int = 3) -> dict:
    token, _ = _get_config()
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = json.dumps(payload).encode()

    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=10) as res:
                result = json.loads(res.read().decode())

                if not result.get("ok"):
                    raise TelegramAPIError(result.get("description"))

                return result

        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = 2 ** attempt
                time.sleep(retry_after)
                continue
            raise

        except Exception:
            time.sleep(1 + attempt)

    raise TelegramAPIError("Max retries exceeded")


# =========================
# Public Send
# =========================

def send(
    message: str,
    parse_mode: Optional[str] = "HTML",
    priority: str = "normal",
    deduplicate: bool = True
) -> dict:

    if not message.strip():
        raise ValueError("Empty message")

    if deduplicate and _is_duplicate(message):
        return {"status": "skipped_duplicate"}

    _, chat_id = _get_config()

    # Priority tagging
    prefix = {
        "high": "🚨 ",
        "medium": "⚠️ ",
        "low": "ℹ️ ",
        "normal": ""
    }.get(priority, "")

    payload = {
        "chat_id": chat_id,
        "text": prefix + message,
        "disable_web_page_preview": True
    }

    if parse_mode:
        payload["parse_mode"] = parse_mode

    return _send_request(payload)


# =========================
# Async Send (Non-blocking)
# =========================

def send_async(
    message: str,
    parse_mode: Optional[str] = "HTML",
    priority: str = "normal"
):
    def _run():
        try:
            send(message, parse_mode, priority)
        except Exception as e:
            import logging
            logging.error(f"Telegram send failed: {e}")

    threading.Thread(target=_run, daemon=True).start()


# =========================
# Safe Wrapper
# =========================

def send_safe(message: str, **kwargs) -> bool:
    try:
        send(message, **kwargs)
        return True
    except Exception as e:
        import logging
        logging.error(f"Telegram error: {e}")
        return False


# =========================
# Global Manager
# =========================

class AlertManager:
    def __init__(self):
        pass

    def trigger_alert(self, title: str, message: str):
        print(f"ALERT: {title} - {message}")
        # In production, this would send to Telegram/email/etc.

    def send_safe(self, message: str, **kwargs):
        return send_safe(message, **kwargs)


# Global alert manager instance
_default_alert_manager = None

def get_alert_manager() -> AlertManager:
    """
    Get or create the global alert manager instance.

    Returns:
        AlertManager instance
    """
    global _default_alert_manager
    if _default_alert_manager is None:
        _default_alert_manager = AlertManager()
    return _default_alert_manager