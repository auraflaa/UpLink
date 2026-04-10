"""
Test script for Telegram bot integration with the scheduler.
This script helps get your Telegram chat ID and sends a test reminder.
"""

import json
import os
import ssl
import sys
from typing import Optional
from urllib import error, request

# Add the parent directory to sys.path to import scheduler
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from Scheduler.scheduler import _load_dotenv, SchedulerEngine

ENV_PATHS = [
    os.path.join(os.path.dirname(__file__), ".env"),
    os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "Scheduler", ".env")),
]


def get_bot_token():
    """Get the Telegram bot token from environment or .env file."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        return token

    for path in ENV_PATHS:
        env_settings = _load_dotenv(path)
        token = (
            env_settings.get("TELEGRAM_BOT_TOKEN")
            or env_settings.get("BOT_TOKEN")
            or env_settings.get("TELEGRAM_TOKEN")
        )
        if token:
            return token

    return token


def get_env_setting(*keys):
    for key in keys:
        value = os.getenv(key)
        if value:
            return value

    for path in ENV_PATHS:
        env_settings = _load_dotenv(path)
        for key in keys:
            value = env_settings.get(key)
            if value:
                return value

    return None


def build_ssl_context():
    """
    Build an SSL context for Telegram API calls.

    Preferred fix:
    - set TELEGRAM_CA_BUNDLE to a PEM file that contains your trusted root cert

    Temporary fallback:
    - set TELEGRAM_ALLOW_INSECURE_SSL=true to bypass certificate validation
    """
    cafile = get_env_setting("TELEGRAM_CA_BUNDLE", "SSL_CERT_FILE")
    if cafile:
        return ssl.create_default_context(cafile=cafile)

    allow_insecure = str(get_env_setting("TELEGRAM_ALLOW_INSECURE_SSL") or "").strip().lower()
    if allow_insecure in {"1", "true", "yes"}:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    return ssl.create_default_context()


def describe_ssl_mode():
    cafile = get_env_setting("TELEGRAM_CA_BUNDLE", "SSL_CERT_FILE")
    if cafile:
        return "custom_ca_bundle", cafile

    allow_insecure = str(get_env_setting("TELEGRAM_ALLOW_INSECURE_SSL") or "").strip().lower()
    if allow_insecure in {"1", "true", "yes"}:
        return "insecure_bypass", None

    return "default_verification", None


def get_chat_id(token):
    """
    Fetch the latest chat ID from bot updates.
    Note: You must have sent a message to the bot recently for this to work.
    """
    url = "https://api.telegram.org/bot{}/getUpdates".format(token)
    ssl_context = build_ssl_context()
    try:
        with request.urlopen(url, timeout=10, context=ssl_context) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("ok") and data.get("result"):
                # Get the most recent message's chat ID
                latest_update = data["result"][-1]
                chat_id = latest_update.get("message", {}).get("chat", {}).get("id")
                if chat_id:
                    return str(chat_id)
            elif not data.get("ok"):
                print("Telegram API error: {}".format(data.get("description", "unknown error")))
    except error.URLError as e:
        print("Error fetching updates: {}".format(e))
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            print("")
            print("Your Python HTTPS stack does not trust the certificate chain used on this network.")
            print("This usually happens when a proxy, firewall, or antivirus is intercepting HTTPS.")
            print("Recommended fix:")
            print("1. Export the trusted root certificate as a PEM file")
            print("2. Set TELEGRAM_CA_BUNDLE=<path-to-pem> in your .env")
            print("")
            print("Temporary workaround:")
            print("Set TELEGRAM_ALLOW_INSECURE_SSL=true in your .env and run the script again")
    return None


def send_test_reminder(chat_id, token):
    """Send a test reminder message."""
    engine = SchedulerEngine()

    # Schedule a test job
    job_payload = {
        "title": "Telegram bot is working healthily",
        "kind": "task",
        "execute_at": "2026-04-10T12:00:00Z",  # Future date
        "channels": ["telegram"],
        "metadata": {
            "telegram_chat_id": chat_id,
        },
    }

    try:
        result = engine.schedule(job_payload)
        job_id = result["job"]["job_id"]
        print("Scheduled test job: {}".format(job_id))

        # Trigger the reminder immediately
        trigger_result = engine.trigger(job_id, "reminder")
        print("Trigger result: {}".format(trigger_result))

    except Exception as e:
        print("Error scheduling/triggering job: {}".format(e))
    finally:
        engine.shutdown()


def main():
    token = get_bot_token()
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment or .env file.")
        print("Please set TELEGRAM_BOT_TOKEN in your .env file or environment variables.")
        return

    ssl_mode, ssl_value = describe_ssl_mode()
    if ssl_mode == "custom_ca_bundle":
        print("SSL mode: custom CA bundle")
        print("CA bundle: {}".format(ssl_value))
    elif ssl_mode == "insecure_bypass":
        print("SSL mode: insecure bypass enabled")
    else:
        print("SSL mode: default certificate verification")
        print("Tip: set TELEGRAM_ALLOW_INSECURE_SSL=true or TELEGRAM_CA_BUNDLE=<path> in Scheduler/.env")

    print("Fetching your chat ID...")
    print("Make sure you've sent a message to your bot recently!")
    chat_id = get_chat_id(token)

    if not chat_id:
        print("Could not find chat ID. Please:")
        print("1. Start a chat with your bot")
        print("2. Send any message to the bot")
        print("3. Run this script again")
        print("")
        print("Alternatively, you can manually find your chat ID by:")
        print("- Using @userinfobot in Telegram")
        print("- Checking bot logs/updates via API")
        return

    print("Found chat ID: {}".format(chat_id))
    print("Sending test reminder...")

    send_test_reminder(chat_id, token)


if __name__ == "__main__":
    main()
