from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib import error, request


DEFAULT_SCHEDULER_URL = os.getenv("SCHEDULER_URL", "http://127.0.0.1:8002")
DEFAULT_EVENT_HANDLER_HOST = os.getenv("EVENT_HANDLER_HOST", "0.0.0.0")
DEFAULT_EVENT_HANDLER_PORT = int(os.getenv("EVENT_HANDLER_PORT", "8003"))


def _parse_datetime(value: str | datetime | None) -> datetime:
    if value is None:
        raise ValueError("A datetime value is required.")

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _isoformat(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value else None


def _as_list(value: Any, fallback: list[str] | None = None) -> list[str]:
    if value is None:
        return list(fallback or [])
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value).strip()]


@dataclass(slots=True)
class NormalizedScheduleRequest:
    title: str
    kind: str
    execute_at: datetime
    description: str = ""
    end_at: datetime | None = None
    channels: list[str] = field(default_factory=lambda: ["telegram", "calendar"])
    reminder_offsets_minutes: list[int] = field(default_factory=lambda: [60, 15])
    source: str = "main_server"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_scheduler_payload(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "kind": self.kind,
            "description": self.description,
            "execute_at": _isoformat(self.execute_at),
            "end_at": _isoformat(self.end_at),
            "channels": self.channels,
            "reminder_offsets_minutes": self.reminder_offsets_minutes,
            "source": self.source,
            "metadata": self.metadata,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["execute_at"] = _isoformat(self.execute_at)
        payload["end_at"] = _isoformat(self.end_at)
        return payload


class EventNormalizer:
    """Turns raw main-server events into scheduler-ready jobs."""

    def normalize(self, payload: dict[str, Any]) -> NormalizedScheduleRequest:
        title = self._pick_first(payload, "title", "name", "summary")
        if not title:
            raise ValueError("Missing event title/name/summary.")

        execute_at = self._pick_first(
            payload,
            "execute_at",
            "scheduled_for",
            "occurs_at",
            "due_at",
            "start_at",
            "start_time",
        )
        if not execute_at:
            raise ValueError(
                "Missing schedule time. Expected one of execute_at, scheduled_for, occurs_at, due_at, start_at, or start_time."
            )

        end_at = self._pick_first(payload, "end_at", "ends_at", "finish_at")
        raw_kind = str(self._pick_first(payload, "kind", "type", "category") or "").strip().lower()
        kind = raw_kind if raw_kind in {"task", "event"} else self._infer_kind(payload)

        reminder_offsets = payload.get("reminder_offsets_minutes")
        if reminder_offsets is None:
            reminder_offsets = payload.get("remind_before_minutes", payload.get("notification_offsets"))

        normalized = NormalizedScheduleRequest(
            title=title,
            kind=kind,
            description=str(self._pick_first(payload, "description", "details", "body") or "").strip(),
            execute_at=_parse_datetime(execute_at),
            end_at=_parse_datetime(end_at) if end_at else None,
            channels=_as_list(payload.get("channels"), ["telegram", "calendar"]),
            reminder_offsets_minutes=self._normalize_offsets(reminder_offsets),
            source=str(payload.get("source") or "main_server"),
            metadata={
                "priority": payload.get("priority"),
                "tags": _as_list(payload.get("tags")),
                "resource": payload.get("resource"),
                "resource_url": payload.get("resource_url") or payload.get("url"),
                "location": payload.get("location"),
                "timezone": payload.get("timezone"),
                "calendar_id": payload.get("calendar_id"),
                "calendar_event_id": payload.get("calendar_event_id"),
                "attendees": payload.get("attendees") or [],
                "meeting_link": payload.get("meeting_link"),
                "default_duration_minutes": payload.get("default_duration_minutes"),
                "user_id": payload.get("user_id"),
                "app_user_id": payload.get("app_user_id"),
                "owner_id": payload.get("owner_id"),
                "telegram_chat_id": payload.get("telegram_chat_id"),
                "telegram_user_id": payload.get("telegram_user_id"),
                "telegram_username": payload.get("telegram_username"),
                "telegram_parse_mode": payload.get("telegram_parse_mode"),
                "origin_payload": payload,
            },
        )
        return normalized

    @staticmethod
    def _pick_first(payload: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = payload.get(key)
            if value not in (None, ""):
                return value
        return None

    @staticmethod
    def _infer_kind(payload: dict[str, Any]) -> str:
        if payload.get("location") or payload.get("end_at") or payload.get("ends_at"):
            return "event"
        return "task"

    @staticmethod
    def _normalize_offsets(raw_offsets: Any) -> list[int]:
        if raw_offsets is None:
            return [60, 15]

        if isinstance(raw_offsets, int):
            values = [raw_offsets]
        elif isinstance(raw_offsets, list):
            values = raw_offsets
        elif isinstance(raw_offsets, str):
            values = [part.strip() for part in raw_offsets.split(",") if part.strip()]
        else:
            raise ValueError("Unsupported reminder offset format.")

        normalized = sorted(
            {
                int(value)
                for value in values
                if str(value).strip() and int(value) >= 0
            },
            reverse=True,
        )
        return normalized or [15]


class SchedulerGateway:
    """Forwards normalized jobs to the scheduler service on port 8002."""

    def __init__(self, scheduler_url: str = DEFAULT_SCHEDULER_URL) -> None:
        self.scheduler_url = scheduler_url.rstrip("/")

    def submit(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self.scheduler_url}/schedule",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Scheduler rejected the request: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Unable to reach scheduler at {self.scheduler_url}.") from exc


class EventHandlerService:
    def __init__(self, scheduler_url: str = DEFAULT_SCHEDULER_URL) -> None:
        self.normalizer = EventNormalizer()
        self.scheduler = SchedulerGateway(scheduler_url)

    def preview(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = self.normalizer.normalize(payload)
        return {
            "status": "normalized",
            "scheduler_payload": normalized.to_scheduler_payload(),
            "normalized_event": normalized.to_dict(),
        }

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = self.normalizer.normalize(payload)
        scheduler_response = self.scheduler.submit(normalized.to_scheduler_payload())
        return {
            "status": "accepted",
            "scheduler_response": scheduler_response,
            "normalized_event": normalized.to_dict(),
        }


class EventRequestHandler(BaseHTTPRequestHandler):
    service = EventHandlerService()

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
            return

        self._send_json(
            {
                "service": "event_handler",
                "status": "healthy",
                "scheduler_url": self.service.scheduler.scheduler_url,
            }
        )

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self._read_json()
            if self.path == "/events/preview":
                response = self.service.preview(payload)
                self._send_json(response, status=HTTPStatus.OK)
                return

            if self.path == "/events/ingest":
                response = self.service.ingest(payload)
                self._send_json(response, status=HTTPStatus.ACCEPTED)
                return

            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except RuntimeError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else b"{}"
        return json.loads(body.decode("utf-8"))

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def run_server(
    host: str = DEFAULT_EVENT_HANDLER_HOST,
    port: int = DEFAULT_EVENT_HANDLER_PORT,
) -> None:
    server = ThreadingHTTPServer((host, port), EventRequestHandler)
    print(f"Event handler listening on http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    run_server()


if __name__ == "__main__":
    main()
