"""
Jira integration test helper for the UpLink scheduler service.

Test plan:
1. Verify Jira configuration exists in Backend/Scheduler/.env
2. Verify the scheduler service is reachable
3. Fetch Jira projects through the scheduler
4. Search Jira issues through the scheduler
5. Optionally create a Jira issue
6. Optionally schedule reminders from an existing Jira issue due date
7. Optionally analyze a Jira issue/project URL, including public Jira Cloud links

Usage examples:
    python jiraTest.py
    python jiraTest.py --jql "project = UP ORDER BY created DESC"
    python jiraTest.py --create --summary "Jira scheduler smoke test"
    python jiraTest.py --issue-key UP-12
    python jiraTest.py --jira-url "https://example.atlassian.net/browse/ABC-123"
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Any
from urllib import error, parse, request


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from Scheduler.scheduler import _load_dotenv  # noqa: E402


SCHEDULER_ENV_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "Scheduler", ".env")
)
SCHEDULER_SCRIPT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "Scheduler", "scheduler.py")
)
DEFAULT_SCHEDULER_URL = os.getenv("SCHEDULER_URL", "http://127.0.0.1:8002").rstrip("/")


def get_scheduler_env() -> dict[str, str]:
    return _load_dotenv(SCHEDULER_ENV_PATH)


def print_header(title: str) -> None:
    print("")
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_json(label: str, payload: dict[str, Any]) -> None:
    print(f"{label}:")
    print(json.dumps(payload, indent=2))


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = request.Request(
        url=f"{DEFAULT_SCHEDULER_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Unable to reach scheduler at {DEFAULT_SCHEDULER_URL}: {exc.reason}") from exc


def try_scheduler_health() -> tuple[bool, str | None]:
    try:
        request_json("GET", "/health")
        return True, None
    except Exception as exc:
        return False, str(exc)


def start_scheduler() -> subprocess.Popen[str]:
    print("Scheduler is not running. Starting it automatically...")
    process = subprocess.Popen(
        [sys.executable, SCHEDULER_SCRIPT_PATH],
        cwd=os.path.dirname(SCHEDULER_SCRIPT_PATH),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return process


def ensure_scheduler_running(auto_start: bool, startup_wait_seconds: int = 8) -> subprocess.Popen[str] | None:
    healthy, error_message = try_scheduler_health()
    if healthy:
        print("Scheduler is already running.")
        return None

    print(f"Initial scheduler check failed: {error_message}")
    if not auto_start:
        raise RuntimeError(
            "Scheduler is not running on port 8002. Start Backend/Scheduler/scheduler.py first or rerun with --auto-start-scheduler."
        )

    process = start_scheduler()
    for _ in range(startup_wait_seconds):
        time.sleep(1)
        healthy, _ = try_scheduler_health()
        if healthy:
            print("Scheduler started successfully.")
            return process

    process.terminate()
    raise RuntimeError(
        "Scheduler could not be started automatically. Check Backend/Scheduler/scheduler.py for runtime errors."
    )


def verify_env() -> bool:
    print_header("1. Verifying Jira Environment")
    env_settings = get_scheduler_env()
    required_keys = ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"]
    missing = [key for key in required_keys if not env_settings.get(key)]

    print(f"Scheduler env path: {SCHEDULER_ENV_PATH}")
    for key in required_keys:
        status = "present" if env_settings.get(key) else "missing"
        print(f"- {key}: {status}")

    if missing:
        print("")
        print("Missing Jira configuration. Add these keys to Backend/Scheduler/.env:")
        for key in missing:
            print(f"- {key}")
        return False

    return True


def verify_scheduler_health() -> None:
    print_header("2. Verifying Scheduler Health")
    payload = request_json("GET", "/health")
    print_json("Health response", payload)


def test_jira_projects() -> dict[str, Any]:
    print_header("3. Fetching Jira Projects")
    payload = request_json("GET", "/jira/projects")
    print_json("Projects response", payload)
    return payload


def test_jira_search(jql: str | None, max_results: int) -> dict[str, Any]:
    print_header("4. Searching Jira Issues")
    query = parse.urlencode(
        {
            "jql": jql or "",
            "max_results": max_results,
        }
    )
    path = f"/jira/issues?{query}" if query else "/jira/issues"
    payload = request_json("GET", path)
    print_json("Issues response", payload)
    return payload


def test_create_issue(args: argparse.Namespace) -> dict[str, Any]:
    print_header("5. Creating Jira Issue")
    env_settings = get_scheduler_env()
    payload = {
        "project_key": args.project_key or env_settings.get("JIRA_PROJECT_KEY", ""),
        "summary": args.summary,
        "description": args.description,
        "issue_type": args.issue_type,
        "due_date": args.due_date,
        "schedule_due_date": args.schedule_due_date,
        "reminder_offsets_minutes": args.reminder_offsets_minutes,
    }
    created = request_json("POST", "/jira/issues", payload)
    print_json("Create issue response", created)
    return created


def test_schedule_existing_issue(issue_key: str) -> dict[str, Any]:
    print_header("6. Scheduling Existing Jira Issue Due Date")
    payload = request_json(
        "POST",
        "/jira/issues/schedule",
        {
            "issue_key": issue_key,
            "default_reminder_offsets_minutes": [1440, 60, 15],
        },
    )
    print_json("Schedule issue response", payload)
    return payload


def test_analyze_jira_link(jira_url: str) -> dict[str, Any]:
    print_header("7. Analyzing Jira Link")
    payload = request_json(
        "POST",
        "/jira/analyze-link",
        {
            "url": jira_url,
        },
    )
    print_json("Analyze Jira link response", payload)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Jira integration checks against the scheduler service.")
    parser.add_argument("--jql", help="Optional Jira JQL query for the issue search test.")
    parser.add_argument("--max-results", type=int, default=10, help="Max results for Jira issue search.")
    parser.add_argument("--create", action="store_true", help="Create a Jira issue through the scheduler.")
    parser.add_argument("--project-key", help="Jira project key to use when creating an issue.")
    parser.add_argument("--summary", default="UpLink Jira integration smoke test", help="Issue summary for creation test.")
    parser.add_argument(
        "--description",
        default="Created from Backend/Test Scripts/jiraTest.py to verify Jira integration.",
        help="Issue description for creation test.",
    )
    parser.add_argument("--issue-type", default="Task", help="Jira issue type name.")
    parser.add_argument(
        "--due-date",
        default="2026-04-15T18:00:00+05:30",
        help="Due date used for the create-issue flow.",
    )
    parser.add_argument(
        "--schedule-due-date",
        action="store_true",
        help="When creating an issue, also schedule reminders from its due date.",
    )
    parser.add_argument(
        "--reminder-offsets-minutes",
        nargs="*",
        type=int,
        default=[1440, 60, 15],
        help="Reminder offsets used when scheduling a created issue.",
    )
    parser.add_argument(
        "--issue-key",
        help="Existing Jira issue key to schedule through /jira/issues/schedule.",
    )
    parser.add_argument(
        "--jira-url",
        help="Jira issue/project URL to analyze through /jira/analyze-link.",
    )
    parser.add_argument(
        "--auto-start-scheduler",
        action="store_true",
        help="Automatically start the scheduler if it is not already running.",
    )
    parser.add_argument(
        "--keep-scheduler",
        action="store_true",
        help="Keep the auto-started scheduler process running after the test completes.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    print_header("UpLink Jira Integration Test Plan")
    print(f"Scheduler URL: {DEFAULT_SCHEDULER_URL}")
    print("- Verify Scheduler/.env Jira config")
    print("- Call /health")
    print("- Call /jira/projects")
    print("- Call /jira/issues")
    if args.auto_start_scheduler:
        print("- Auto-start scheduler if needed")
    if args.create:
        print("- Call /jira/issues (create)")
    if args.issue_key:
        print("- Call /jira/issues/schedule")
    if args.jira_url:
        print("- Call /jira/analyze-link")

    if not verify_env():
        return

    started_scheduler: subprocess.Popen[str] | None = None
    try:
        started_scheduler = ensure_scheduler_running(args.auto_start_scheduler)
        verify_scheduler_health()
        test_jira_projects()
        test_jira_search(args.jql, args.max_results)

        created_issue_key = ""
        if args.create:
            created = test_create_issue(args)
            created_issue_key = str(created.get("key") or "").strip()

        issue_key_to_schedule = args.issue_key or created_issue_key
        if issue_key_to_schedule:
            test_schedule_existing_issue(issue_key_to_schedule)

        if args.jira_url:
            test_analyze_jira_link(args.jira_url)

        print_header("Jira Test Completed")
        print("The Jira test plan ran successfully.")
    except Exception as exc:
        print_header("Jira Test Failed")
        print(str(exc))
    finally:
        if started_scheduler and not args.keep_scheduler:
            started_scheduler.terminate()
            try:
                started_scheduler.wait(timeout=5)
            except subprocess.TimeoutExpired:
                started_scheduler.kill()
            print("")
            print("Auto-started scheduler process has been stopped.")


if __name__ == "__main__":
    main()
