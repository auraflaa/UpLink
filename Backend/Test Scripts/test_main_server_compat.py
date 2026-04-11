from __future__ import annotations

import requests

from main_server_test_helper import (
    DOCUMENT_PARSER_URL,
    EVENT_HANDLER_URL,
    MAIN_SERVER_URL,
    SCHEDULER_URL,
    ensure_main_server_running,
    print_header,
    stop_process,
)


def _probe(url: str) -> tuple[str, dict]:
    try:
        response = requests.get(url, timeout=5)
        try:
            payload = response.json()
        except Exception:
            payload = {"raw": response.text[:200]}
        return "online" if response.ok else "degraded", payload
    except requests.RequestException as exc:
        return "offline", {"reason": str(exc)}


def main() -> None:
    print_header("UpLink Main Server Compatibility Test")
    started = ensure_main_server_running(auto_start=True)
    try:
        checks = {
            "main_server": f"{MAIN_SERVER_URL}/health",
            "scheduler": f"{SCHEDULER_URL}/health",
            "event_handler": f"{EVENT_HANDLER_URL}/health",
            "document_parser": f"{DOCUMENT_PARSER_URL}/status",
        }

        for service_name, url in checks.items():
            status, payload = _probe(url)
            print(f"- {service_name}: {status}")
            if status != "offline":
                print(payload)

        print_header("Compatibility Test Completed")
        print("Existing services remain independently reachable when they are running.")
    finally:
        stop_process(started)


if __name__ == "__main__":
    main()
