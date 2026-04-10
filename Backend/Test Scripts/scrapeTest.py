"""
Scraper integration and contract test helper for UpLink.

This script validates the expected scraper interface and the normalized
event output format that should feed the event handler and scheduler.

Usage examples:
    python scrapeTest.py
    python scrapeTest.py --platforms unstop devfolio
    python scrapeTest.py --show-sample-format
    python scrapeTest.py --json
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import os
import sys
from typing import Any


SCRAPER_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "Scraping", "scrape.py")
)

EXPECTED_OUTPUT_SCHEMA: dict[str, Any] = {
    "title": "Example Hackathon 2026",
    "description": "Build an AI solution for real-world impact.",
    "platform": "unstop",
    "source_id": "unstop:example-hackathon-2026",
    "event_url": "https://unstop.com/example-hackathon-2026",
    "registration_url": "https://unstop.com/example-hackathon-2026/register",
    "start_at": "2026-05-10T09:00:00+05:30",
    "end_at": "2026-05-12T18:00:00+05:30",
    "deadline": "2026-05-05T23:59:00+05:30",
    "location": "Bengaluru, India",
    "mode": "hybrid",
    "tags": ["hackathon", "ai", "student"],
    "organizer": "Example Org",
    "prize": "INR 1,00,000",
    "timezone": "Asia/Calcutta",
}

RECOMMENDED_KEYS = [
    "title",
    "description",
    "platform",
    "source_id",
    "event_url",
    "registration_url",
    "start_at",
    "end_at",
    "deadline",
    "location",
    "mode",
    "tags",
    "organizer",
    "prize",
    "timezone",
]


def print_header(title: str) -> None:
    print("")
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_json(label: str, payload: Any) -> None:
    print(f"{label}:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def load_scraper_module() -> Any:
    if not os.path.exists(SCRAPER_PATH):
        raise RuntimeError(f"Scraper file not found at: {SCRAPER_PATH}")

    spec = importlib.util.spec_from_file_location("uplink_scrape", SCRAPER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load scraper module from: {SCRAPER_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run contract checks against Backend/Scraping/scrape.py.")
    parser.add_argument(
        "--platforms",
        nargs="*",
        help="Optional list of platforms to pass into run_scrapers(platforms=...).",
    )
    parser.add_argument(
        "--show-sample-format",
        action="store_true",
        help="Print the expected normalized event output format.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print returned scraper results as JSON.",
    )
    return parser


def validate_event(event: dict[str, Any], index: int) -> list[str]:
    problems: list[str] = []
    title = str(event.get("title") or "").strip()
    if not title:
        problems.append(f"event[{index}] is missing 'title'")

    if not str(event.get("source_id") or "").strip() and not str(event.get("event_url") or "").strip():
        problems.append(f"event[{index}] needs either 'source_id' or 'event_url' for dedupe/update logic")

    if not any(
        str(event.get(key) or "").strip()
        for key in ["deadline", "deadline_at", "registration_deadline", "start_at", "execute_at"]
    ):
        problems.append(
            f"event[{index}] needs one scheduling field: deadline, deadline_at, registration_deadline, start_at, or execute_at"
        )

    tags = event.get("tags")
    if tags is not None and not isinstance(tags, list):
        problems.append(f"event[{index}] field 'tags' should be a list")

    mode = str(event.get("mode") or "").strip().lower()
    if mode and mode not in {"online", "offline", "hybrid"}:
        problems.append(f"event[{index}] field 'mode' should be online, offline, or hybrid")

    return problems


def call_run_scrapers(module: Any, platforms: list[str] | None) -> Any:
    run_scrapers = getattr(module, "run_scrapers", None)
    if run_scrapers is None or not callable(run_scrapers):
        raise RuntimeError(
            "scrape.py does not expose a callable run_scrapers() function yet. "
            "Add run_scrapers(platforms=None) so the scraper can be tested."
        )

    signature = inspect.signature(run_scrapers)
    if "platforms" in signature.parameters:
        return run_scrapers(platforms=platforms)
    if platforms:
        raise RuntimeError("run_scrapers() exists but does not accept a 'platforms' argument.")
    return run_scrapers()


def normalize_result_shape(raw_result: Any) -> list[dict[str, Any]]:
    if isinstance(raw_result, list):
        events = raw_result
    elif isinstance(raw_result, dict):
        if isinstance(raw_result.get("events"), list):
            events = raw_result["events"]
        else:
            raise RuntimeError("Scraper returned a dict, but it does not contain an 'events' list.")
    else:
        raise RuntimeError("Scraper output must be either a list[dict] or a dict with an 'events' list.")

    if not all(isinstance(item, dict) for item in events):
        raise RuntimeError("Every scraped event must be a dictionary.")

    return events


def print_contract() -> None:
    print_header("Expected Scraper Output Format")
    print("The scraper should return either:")
    print("- a list of normalized event dictionaries")
    print("- or a dict with an 'events' key containing that list")
    print("")
    print("Recommended normalized keys:")
    for key in RECOMMENDED_KEYS:
        print(f"- {key}")
    print("")
    print_json("Sample normalized event", EXPECTED_OUTPUT_SCHEMA)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    print_header("UpLink Scraper Test Plan")
    print(f"Scraper path: {SCRAPER_PATH}")
    print("- Load scrape.py dynamically")
    print("- Verify a callable run_scrapers() exists")
    print("- Execute scraper")
    print("- Validate normalized output contract")
    print("- Print sample output format")

    if args.show_sample_format:
        print_contract()

    print_header("1. Loading Scraper Module")
    module = load_scraper_module()
    print("Scraper module loaded successfully.")

    print_header("2. Verifying Scraper Entrypoint")
    run_scrapers = getattr(module, "run_scrapers", None)
    if run_scrapers is None or not callable(run_scrapers):
        raise RuntimeError(
            "scrape.py is currently empty or incomplete. "
            "Expected a callable run_scrapers(platforms=None) entrypoint."
        )
    print("Found callable run_scrapers() entrypoint.")

    print_header("3. Running Scraper")
    result = call_run_scrapers(module, args.platforms)
    events = normalize_result_shape(result)
    print(f"Scraper returned {len(events)} event(s).")

    print_header("4. Validating Output Contract")
    all_problems: list[str] = []
    for index, event in enumerate(events):
        all_problems.extend(validate_event(event, index))

    if all_problems:
        print("Contract validation found issues:")
        for problem in all_problems:
            print(f"- {problem}")
        raise RuntimeError("Scraper output does not match the expected normalized format.")

    print("All returned events matched the expected contract.")

    print_header("5. Output Summary")
    if isinstance(result, dict):
        if result.get("db_path"):
            print(f"SQLite DB: {result['db_path']}")
        if isinstance(result.get("persisted"), dict):
            print_json("Persistence summary", result["persisted"])
        if isinstance(result.get("platform_stats"), dict):
            print_json("Platform stats", result["platform_stats"])

    if events:
        summary = [
            {
                "title": event.get("title"),
                "platform": event.get("platform"),
                "deadline": event.get("deadline") or event.get("deadline_at") or event.get("registration_deadline"),
                "start_at": event.get("start_at") or event.get("execute_at"),
                "event_url": event.get("event_url") or event.get("resource_url"),
                "source_id": event.get("source_id"),
            }
            for event in events
        ]
        print_json("Event summary", summary)
        if args.json:
            print_json("Full scraper output", events)
    else:
        print("No events were returned.")

    print_contract()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print_header("Scraper Test Failed")
        print(str(exc))
        sys.exit(1)
