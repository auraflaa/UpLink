from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable
from urllib import error, request
from zoneinfo import ZoneInfo


BASE_DIR = os.path.dirname(__file__)
DEFAULT_DB_PATH = os.getenv("SCRAPER_DB_PATH", os.path.join(BASE_DIR, "events.sqlite3"))
DEFAULT_EVENT_HANDLER_URL = os.getenv("EVENT_HANDLER_URL", "http://127.0.0.1:8003/events/ingest")
DEFAULT_SCAN_TIME = os.getenv("SCRAPER_SCAN_TIME", "08:00")
DEFAULT_TIMEZONE = os.getenv("SCRAPER_TIMEZONE", "Asia/Calcutta")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _local_now(timezone_name: str = DEFAULT_TIMEZONE) -> datetime:
    try:
        return datetime.now(ZoneInfo(timezone_name))
    except Exception:
        return _utc_now()


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _isoformat(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value else None


def _as_string(value: Any) -> str:
    return str(value or "").strip()


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value).strip()]


def _safe_json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _normalize_mode(value: Any) -> str:
    normalized = _as_string(value).lower()
    return normalized if normalized in {"online", "offline", "hybrid"} else ""


def _event_score(event: dict[str, Any]) -> int:
    score = 0
    for value in event.values():
        if isinstance(value, list):
            score += len(value)
        elif value not in (None, "", []):
            score += 1
    return score


def _derive_source_id(platform: str, raw: dict[str, Any]) -> str:
    explicit = _as_string(raw.get("source_id"))
    if explicit:
        return explicit

    event_url = _as_string(raw.get("event_url") or raw.get("url"))
    if event_url:
        return f"{platform}:{event_url}"

    title = _as_string(raw.get("title") or raw.get("name"))
    schedule_hint = _as_string(
        raw.get("deadline")
        or raw.get("deadline_at")
        or raw.get("registration_deadline")
        or raw.get("start_at")
        or raw.get("execute_at")
    )
    digest = hashlib.sha256(f"{platform}|{title}|{schedule_hint}".encode("utf-8")).hexdigest()[:16]
    return f"{platform}:{digest}"


def _derive_dedupe_key(event: dict[str, Any]) -> str:
    source_id = _as_string(event.get("source_id"))
    if source_id:
        return f"source:{source_id}"

    event_url = _as_string(event.get("event_url"))
    if event_url:
        return f"url:{event_url}"

    title = _as_string(event.get("title"))
    deadline = _as_string(event.get("deadline") or event.get("deadline_at") or event.get("registration_deadline"))
    platform = _as_string(event.get("platform"))
    digest = hashlib.sha256(f"{platform}|{title}|{deadline}".encode("utf-8")).hexdigest()
    return f"hash:{digest}"


@dataclass(slots=True)
class NormalizedEvent:
    title: str
    description: str = ""
    platform: str = ""
    source_id: str = ""
    event_url: str = ""
    registration_url: str = ""
    start_at: str | None = None
    end_at: str | None = None
    deadline: str | None = None
    location: str = ""
    mode: str = ""
    tags: list[str] = field(default_factory=list)
    organizer: str = ""
    prize: str = ""
    timezone: str = DEFAULT_TIMEZONE
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("raw_payload", None)
        return payload


class BaseScraper:
    platform = "base"

    def fetch_events(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class UnstopScraper(BaseScraper):
    platform = "unstop"

    def fetch_events(self) -> list[dict[str, Any]]:
        return []


class DevfolioScraper(BaseScraper):
    platform = "devfolio"

    def fetch_events(self) -> list[dict[str, Any]]:
        return []


class HackerEarthScraper(BaseScraper):
    platform = "hackerearth"

    def fetch_events(self) -> list[dict[str, Any]]:
        return []


class ReskilllScraper(BaseScraper):
    platform = "reskilll"

    def fetch_events(self) -> list[dict[str, Any]]:
        return []


SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {
    UnstopScraper.platform: UnstopScraper,
    DevfolioScraper.platform: DevfolioScraper,
    HackerEarthScraper.platform: HackerEarthScraper,
    ReskilllScraper.platform: ReskilllScraper,
}


def normalize_event(raw: dict[str, Any], platform: str) -> dict[str, Any]:
    title = _as_string(raw.get("title") or raw.get("name") or raw.get("summary"))
    if not title:
        raise ValueError(f"Scraped event from {platform} is missing a title.")

    start_at = _parse_datetime(raw.get("start_at") or raw.get("start_time") or raw.get("execute_at"))
    end_at = _parse_datetime(raw.get("end_at") or raw.get("end_time"))
    deadline = _parse_datetime(
        raw.get("deadline") or raw.get("deadline_at") or raw.get("registration_deadline")
    )

    normalized = NormalizedEvent(
        title=title,
        description=_as_string(raw.get("description") or raw.get("details") or raw.get("body")),
        platform=platform,
        source_id=_derive_source_id(platform, raw),
        event_url=_as_string(raw.get("event_url") or raw.get("url")),
        registration_url=_as_string(raw.get("registration_url")),
        start_at=_isoformat(start_at),
        end_at=_isoformat(end_at),
        deadline=_isoformat(deadline),
        location=_as_string(raw.get("location")),
        mode=_normalize_mode(raw.get("mode")),
        tags=_as_string_list(raw.get("tags")),
        organizer=_as_string(raw.get("organizer")),
        prize=_as_string(raw.get("prize")),
        timezone=_as_string(raw.get("timezone")) or DEFAULT_TIMEZONE,
        raw_payload=dict(raw),
    )
    return normalized.to_dict()


def dedupe_events(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for event in events:
        key = _derive_dedupe_key(event)
        current = deduped.get(key)
        if current is None or _event_score(event) >= _event_score(current):
            deduped[key] = event
    return list(deduped.values())


class EventStore:
    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS events (
                    dedupe_key TEXT PRIMARY KEY,
                    source_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    platform TEXT NOT NULL,
                    event_url TEXT,
                    registration_url TEXT,
                    start_at TEXT,
                    end_at TEXT,
                    deadline TEXT,
                    location TEXT,
                    mode TEXT,
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    organizer TEXT,
                    prize TEXT,
                    timezone TEXT,
                    raw_payload_json TEXT NOT NULL DEFAULT '{}',
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_events_platform ON events(platform);
                CREATE INDEX IF NOT EXISTS idx_events_deadline ON events(deadline);

                CREATE TABLE IF NOT EXISTS scan_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    platforms_json TEXT NOT NULL,
                    discovered_count INTEGER NOT NULL DEFAULT 0,
                    inserted_count INTEGER NOT NULL DEFAULT 0,
                    updated_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    error_message TEXT
                );
                """
            )

    def upsert_events(self, events: Iterable[dict[str, Any]]) -> dict[str, int]:
        inserted = 0
        updated = 0
        now = _isoformat(_utc_now()) or ""

        with self._connect() as connection:
            for event in events:
                dedupe_key = _derive_dedupe_key(event)
                existing = connection.execute(
                    "SELECT dedupe_key FROM events WHERE dedupe_key = ?",
                    (dedupe_key,),
                ).fetchone()

                connection.execute(
                    """
                    INSERT INTO events (
                        dedupe_key,
                        source_id,
                        title,
                        description,
                        platform,
                        event_url,
                        registration_url,
                        start_at,
                        end_at,
                        deadline,
                        location,
                        mode,
                        tags_json,
                        organizer,
                        prize,
                        timezone,
                        raw_payload_json,
                        first_seen_at,
                        last_seen_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(dedupe_key) DO UPDATE SET
                        source_id = excluded.source_id,
                        title = excluded.title,
                        description = excluded.description,
                        platform = excluded.platform,
                        event_url = excluded.event_url,
                        registration_url = excluded.registration_url,
                        start_at = excluded.start_at,
                        end_at = excluded.end_at,
                        deadline = excluded.deadline,
                        location = excluded.location,
                        mode = excluded.mode,
                        tags_json = excluded.tags_json,
                        organizer = excluded.organizer,
                        prize = excluded.prize,
                        timezone = excluded.timezone,
                        raw_payload_json = excluded.raw_payload_json,
                        last_seen_at = excluded.last_seen_at,
                        updated_at = excluded.updated_at
                    """,
                    (
                        dedupe_key,
                        _as_string(event.get("source_id")),
                        _as_string(event.get("title")),
                        _as_string(event.get("description")),
                        _as_string(event.get("platform")),
                        _as_string(event.get("event_url")),
                        _as_string(event.get("registration_url")),
                        _as_string(event.get("start_at")),
                        _as_string(event.get("end_at")),
                        _as_string(event.get("deadline")),
                        _as_string(event.get("location")),
                        _as_string(event.get("mode")),
                        _safe_json_dumps(_as_string_list(event.get("tags"))),
                        _as_string(event.get("organizer")),
                        _as_string(event.get("prize")),
                        _as_string(event.get("timezone")) or DEFAULT_TIMEZONE,
                        _safe_json_dumps(event),
                        now,
                        now,
                        now,
                    ),
                )

                if existing:
                    updated += 1
                else:
                    inserted += 1

        return {
            "inserted": inserted,
            "updated": updated,
            "persisted": inserted + updated,
        }

    def list_events(self, limit: int = 50, platform: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM events"
        params: list[Any] = []
        if platform:
            query += " WHERE platform = ?"
            params.append(platform)
        query += " ORDER BY COALESCE(deadline, start_at, updated_at) ASC LIMIT ?"
        params.append(max(1, int(limit)))

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        events: list[dict[str, Any]] = []
        for row in rows:
            events.append(
                {
                    "source_id": row["source_id"],
                    "title": row["title"],
                    "description": row["description"],
                    "platform": row["platform"],
                    "event_url": row["event_url"],
                    "registration_url": row["registration_url"],
                    "start_at": row["start_at"],
                    "end_at": row["end_at"],
                    "deadline": row["deadline"],
                    "location": row["location"],
                    "mode": row["mode"],
                    "tags": json.loads(row["tags_json"] or "[]"),
                    "organizer": row["organizer"],
                    "prize": row["prize"],
                    "timezone": row["timezone"],
                    "first_seen_at": row["first_seen_at"],
                    "last_seen_at": row["last_seen_at"],
                    "updated_at": row["updated_at"],
                }
            )
        return events

    def record_scan_run(
        self,
        *,
        started_at: str,
        finished_at: str,
        platforms: list[str],
        discovered_count: int,
        inserted_count: int,
        updated_count: int,
        status: str,
        error_message: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scan_runs (
                    started_at,
                    finished_at,
                    platforms_json,
                    discovered_count,
                    inserted_count,
                    updated_count,
                    status,
                    error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    started_at,
                    finished_at,
                    _safe_json_dumps(platforms),
                    int(discovered_count),
                    int(inserted_count),
                    int(updated_count),
                    status,
                    error_message,
                ),
            )


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=20) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def ingest_events_to_event_handler(
    events: Iterable[dict[str, Any]],
    event_handler_url: str = DEFAULT_EVENT_HANDLER_URL,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for event in events:
        try:
            response_payload = _post_json(event_handler_url, event)
            results.append(
                {
                    "title": event.get("title"),
                    "status": "accepted",
                    "response": response_payload,
                }
            )
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            results.append(
                {
                    "title": event.get("title"),
                    "status": "failed",
                    "reason": f"http_error: {detail}",
                }
            )
        except error.URLError as exc:
            results.append(
                {
                    "title": event.get("title"),
                    "status": "failed",
                    "reason": f"connection_error: {exc.reason}",
                }
            )
    return results


def _build_scrapers(platforms: list[str] | None = None) -> list[BaseScraper]:
    selected = [platform.lower() for platform in platforms] if platforms else list(SCRAPER_REGISTRY)
    scrapers: list[BaseScraper] = []
    for platform in selected:
        scraper_cls = SCRAPER_REGISTRY.get(platform)
        if scraper_cls is None:
            raise ValueError(f"Unsupported scraper platform: {platform}")
        scrapers.append(scraper_cls())
    return scrapers


def run_scrapers(
    platforms: list[str] | None = None,
    *,
    persist: bool = True,
    db_path: str = DEFAULT_DB_PATH,
    push_to_event_handler: bool = False,
    event_handler_url: str = DEFAULT_EVENT_HANDLER_URL,
) -> dict[str, Any]:
    started_at = _isoformat(_utc_now()) or ""
    selected_platforms = [platform.lower() for platform in platforms] if platforms else list(SCRAPER_REGISTRY)
    discovered_events: list[dict[str, Any]] = []
    platform_stats: dict[str, dict[str, Any]] = {}
    scan_errors: list[dict[str, str]] = []

    for scraper in _build_scrapers(selected_platforms):
        try:
            raw_events = scraper.fetch_events()
            normalized_events = [normalize_event(raw, scraper.platform) for raw in raw_events]
            discovered_events.extend(normalized_events)
            platform_stats[scraper.platform] = {
                "discovered": len(normalized_events),
                "status": "ok",
            }
        except Exception as exc:
            platform_stats[scraper.platform] = {
                "discovered": 0,
                "status": "failed",
                "reason": str(exc),
            }
            scan_errors.append({"platform": scraper.platform, "reason": str(exc)})

    deduped_events = dedupe_events(discovered_events)
    persisted = {"inserted": 0, "updated": 0, "persisted": 0}
    db_file = db_path
    repository = EventStore(db_path=db_file) if persist else None

    if repository:
        persisted = repository.upsert_events(deduped_events)

    ingestion_results: list[dict[str, Any]] = []
    if push_to_event_handler and deduped_events:
        ingestion_results = ingest_events_to_event_handler(deduped_events, event_handler_url=event_handler_url)

    status = "completed" if not scan_errors else "partial"
    finished_at = _isoformat(_utc_now()) or ""

    if repository:
        repository.record_scan_run(
            started_at=started_at,
            finished_at=finished_at,
            platforms=selected_platforms,
            discovered_count=len(deduped_events),
            inserted_count=persisted["inserted"],
            updated_count=persisted["updated"],
            status=status,
            error_message=_safe_json_dumps(scan_errors) if scan_errors else None,
        )

    return {
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "platforms": selected_platforms,
        "events": deduped_events,
        "platform_stats": platform_stats,
        "persisted": persisted,
        "db_path": db_file if persist else None,
        "event_handler_results": ingestion_results,
        "errors": scan_errors,
    }


def seconds_until_next_scan(scan_time: str = DEFAULT_SCAN_TIME, timezone_name: str = DEFAULT_TIMEZONE) -> float:
    hour_text, minute_text = scan_time.split(":", 1)
    now_local = _local_now(timezone_name)
    target = now_local.replace(
        hour=int(hour_text),
        minute=int(minute_text),
        second=0,
        microsecond=0,
    )
    if target <= now_local:
        target = target + timedelta(days=1)
    return max((target - now_local).total_seconds(), 0.0)


def run_daily_scan_loop(
    platforms: list[str] | None = None,
    *,
    scan_time: str = DEFAULT_SCAN_TIME,
    timezone_name: str = DEFAULT_TIMEZONE,
    persist: bool = True,
    db_path: str = DEFAULT_DB_PATH,
    push_to_event_handler: bool = False,
    event_handler_url: str = DEFAULT_EVENT_HANDLER_URL,
    stop_event: threading.Event | None = None,
) -> None:
    while True:
        wait_seconds = seconds_until_next_scan(scan_time=scan_time, timezone_name=timezone_name)
        if stop_event and stop_event.wait(timeout=wait_seconds):
            return
        run_scrapers(
            platforms=platforms,
            persist=persist,
            db_path=db_path,
            push_to_event_handler=push_to_event_handler,
            event_handler_url=event_handler_url,
        )


def start_daily_scan_thread(
    platforms: list[str] | None = None,
    *,
    scan_time: str = DEFAULT_SCAN_TIME,
    timezone_name: str = DEFAULT_TIMEZONE,
    persist: bool = True,
    db_path: str = DEFAULT_DB_PATH,
    push_to_event_handler: bool = False,
    event_handler_url: str = DEFAULT_EVENT_HANDLER_URL,
) -> tuple[threading.Thread, threading.Event]:
    stop_event = threading.Event()
    worker = threading.Thread(
        target=run_daily_scan_loop,
        kwargs={
            "platforms": platforms,
            "scan_time": scan_time,
            "timezone_name": timezone_name,
            "persist": persist,
            "db_path": db_path,
            "push_to_event_handler": push_to_event_handler,
            "event_handler_url": event_handler_url,
            "stop_event": stop_event,
        },
        name="scraper-daily-scan",
        daemon=True,
    )
    worker.start()
    return worker, stop_event


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the UpLink scraper service.")
    parser.add_argument("--platforms", nargs="*", help="Optional platform filter such as unstop devfolio")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument(
        "--push-to-event-handler",
        action="store_true",
        help="Forward discovered events to the event handler after persistence.",
    )
    parser.add_argument(
        "--event-handler-url",
        default=DEFAULT_EVENT_HANDLER_URL,
        help="Event handler ingest endpoint.",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Keep the scraper running and scan every morning.",
    )
    parser.add_argument(
        "--scan-time",
        default=DEFAULT_SCAN_TIME,
        help="Daily scan time in HH:MM format using the scraper timezone.",
    )
    parser.add_argument(
        "--timezone",
        default=DEFAULT_TIMEZONE,
        help="Timezone used for the daily scan loop.",
    )
    parser.add_argument(
        "--list-events",
        action="store_true",
        help="Print stored events from the SQLite database and exit.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    store = EventStore(db_path=args.db_path)
    if args.list_events:
        print(
            json.dumps(
                {
                    "db_path": args.db_path,
                    "events": store.list_events(limit=100),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    if args.daemon:
        print(
            f"Scraper daemon running. Daily scan scheduled at {args.scan_time} "
            f"({args.timezone}). Database: {args.db_path}"
        )
        run_daily_scan_loop(
            platforms=args.platforms,
            scan_time=args.scan_time,
            timezone_name=args.timezone,
            persist=True,
            db_path=args.db_path,
            push_to_event_handler=args.push_to_event_handler,
            event_handler_url=args.event_handler_url,
        )
        return

    result = run_scrapers(
        platforms=args.platforms,
        persist=True,
        db_path=args.db_path,
        push_to_event_handler=args.push_to_event_handler,
        event_handler_url=args.event_handler_url,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
