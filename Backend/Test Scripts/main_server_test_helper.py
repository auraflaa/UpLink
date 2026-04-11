from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from typing import Any

import requests


MAIN_SERVER_URL = os.getenv("MAIN_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")
RAG_URL = os.getenv("RAG_URL", "http://127.0.0.1:6399").rstrip("/")
SCHEDULER_URL = os.getenv("SCHEDULER_URL", "http://127.0.0.1:8002").rstrip("/")
EVENT_HANDLER_URL = os.getenv("EVENT_HANDLER_URL", "http://127.0.0.1:8003").rstrip("/")
DOCUMENT_PARSER_URL = os.getenv("DOC_PARSER_URL", "http://127.0.0.1:8004").rstrip("/")

MAIN_SERVER_SCRIPT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "Main Server", "server.py")
)

DEFAULT_GITHUB_URL = "https://github.com/auraflaa/UpLink"
DEFAULT_JIRA_URL = "https://ecosystem.atlassian.net/browse/ACJIRA-2654"


def print_header(title: str) -> None:
    print("")
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_json(label: str, payload: dict[str, Any]) -> None:
    print(f"{label}:")
    print(json.dumps(payload, indent=2))


def build_envelope(
    action: str,
    payload: dict[str, Any] | None = None,
    *,
    user_id: str = "test-user",
    workspace_id: str | None = None,
    ui_surface: str = "test.surface",
    source_kind: str | None = None,
) -> dict[str, Any]:
    return {
        "meta": {
            "action": action,
            "ui_surface": ui_surface,
            "request_id": str(uuid.uuid4()),
            "user_id": user_id,
            "workspace_id": workspace_id,
            "source_kind": source_kind,
        },
        "payload": payload or {},
    }


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.request(
                method=method,
                url=f"{MAIN_SERVER_URL}{path}",
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(1)

    raise RuntimeError(f"{method} {path} failed after retries: {last_error}") from last_error


def is_main_server_running() -> bool:
    try:
        response = requests.get(f"{MAIN_SERVER_URL}/health", timeout=3)
        return response.ok
    except requests.RequestException:
        return False


def start_main_server() -> subprocess.Popen[str]:
    print("Main Server is not running. Starting it automatically...")
    return subprocess.Popen(
        [sys.executable, MAIN_SERVER_SCRIPT_PATH],
        cwd=os.path.dirname(MAIN_SERVER_SCRIPT_PATH),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def ensure_main_server_running(auto_start: bool = True, startup_wait_seconds: int = 10) -> subprocess.Popen[str] | None:
    if is_main_server_running():
        print("Main Server is already running.")
        return None

    if not auto_start:
        raise RuntimeError(
            f"Main Server is not running at {MAIN_SERVER_URL}. Start {MAIN_SERVER_SCRIPT_PATH} first."
        )

    process = start_main_server()
    for _ in range(startup_wait_seconds):
        time.sleep(1)
        if is_main_server_running():
            time.sleep(1)
            print("Main Server started successfully.")
            return process

    process.terminate()
    raise RuntimeError("Main Server could not be started automatically.")


def stop_process(process: subprocess.Popen[str] | None) -> None:
    if not process:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def probe_service(url: str) -> bool:
    try:
        return requests.get(url, timeout=3).ok
    except requests.RequestException:
        return False


def assert_envelope_shape(payload: dict[str, Any]) -> None:
    if "meta" not in payload or "data" not in payload or "errors" not in payload:
        raise AssertionError("Response is missing meta/data/errors envelope keys.")
    meta = payload["meta"]
    if not isinstance(meta, dict):
        raise AssertionError("Response meta must be an object.")
    for key in ("action", "status", "request_id"):
        if key not in meta:
            raise AssertionError(f"Response meta is missing '{key}'.")
