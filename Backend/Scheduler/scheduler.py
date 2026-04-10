from __future__ import annotations

import heapq
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib import error, parse, request


DEFAULT_HOST = os.getenv("SCHEDULER_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("SCHEDULER_PORT", "8002"))
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "calendar_credentials.json")


def _parse_datetime(value: str | datetime | None) -> datetime:
    if value is None:
        raise ValueError("A datetime value is required.")

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _isoformat(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value else None


def _as_string_list(value: Any, fallback: list[str]) -> list[str]:
    if value is None:
        return list(fallback)
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value).strip()]


def _normalize_offsets(value: Any) -> list[int]:
    if value is None:
        return [60, 15]
    if isinstance(value, int):
        values = [value]
    elif isinstance(value, list):
        values = value
    elif isinstance(value, str):
        values = [part.strip() for part in value.split(",") if part.strip()]
    else:
        raise ValueError("Unsupported reminder_offsets_minutes format.")

    return sorted({int(item) for item in values if int(item) >= 0}, reverse=True)


@dataclass(slots=True)
class ScheduledAction:
    action_id: str
    job_id: str
    action_type: str
    scheduled_for: datetime
    offset_minutes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "job_id": self.job_id,
            "action_type": self.action_type,
            "scheduled_for": _isoformat(self.scheduled_for),
            "offset_minutes": self.offset_minutes,
        }


@dataclass(slots=True)
class ScheduledJob:
    job_id: str
    title: str
    kind: str
    execute_at: datetime
    description: str = ""
    end_at: datetime | None = None
    channels: list[str] = field(default_factory=lambda: ["telegram", "calendar"])
    reminder_offsets_minutes: list[int] = field(default_factory=lambda: [60, 15])
    source: str = "event_handler"
    status: str = "scheduled"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "title": self.title,
            "kind": self.kind,
            "description": self.description,
            "execute_at": _isoformat(self.execute_at),
            "end_at": _isoformat(self.end_at),
            "channels": self.channels,
            "reminder_offsets_minutes": self.reminder_offsets_minutes,
            "source": self.source,
            "status": self.status,
            "created_at": _isoformat(self.created_at),
            "metadata": self.metadata,
            "history": self.history,
        }


class SchedulerEngine:
    """Owns task/event scheduling, reminders, and delivery hooks."""

    def __init__(self) -> None:
        self.jobs: dict[str, ScheduledJob] = {}
        self._queue: list[tuple[float, int, ScheduledAction]] = []
        self._sequence = 0
        self._lock = threading.RLock()
        self._wakeup = threading.Condition(self._lock)
        self._running = True
        self._worker = threading.Thread(target=self._run, name="scheduler-worker", daemon=True)
        self._worker.start()

    def schedule(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = str(payload.get("title") or "").strip()
        if not title:
            raise ValueError("title is required.")

        kind = str(payload.get("kind") or "task").strip().lower()
        if kind not in {"task", "event"}:
            raise ValueError("kind must be either 'task' or 'event'.")

        execute_at = _parse_datetime(payload.get("execute_at"))
        end_at = payload.get("end_at")
        channels = _as_string_list(payload.get("channels"), ["telegram", "calendar"])
        reminder_offsets = _normalize_offsets(payload.get("reminder_offsets_minutes"))

        job = ScheduledJob(
            job_id=str(payload.get("job_id") or uuid.uuid4()),
            title=title,
            kind=kind,
            description=str(payload.get("description") or "").strip(),
            execute_at=execute_at,
            end_at=_parse_datetime(end_at) if end_at else None,
            channels=channels,
            reminder_offsets_minutes=reminder_offsets,
            source=str(payload.get("source") or "event_handler"),
            metadata=dict(payload.get("metadata") or {}),
        )

        with self._wakeup:
            self.jobs[job.job_id] = job
            self._enqueue_action(job, "execute", job.execute_at)
            for offset in reminder_offsets:
                reminder_time = job.execute_at - timedelta(minutes=offset)
                if reminder_time > datetime.now(timezone.utc):
                    self._enqueue_action(job, "reminder", reminder_time, offset_minutes=offset)

            job.history.append(
                {
                    "timestamp": _isoformat(datetime.now(timezone.utc)),
                    "status": "scheduled",
                    "message": "Job accepted by scheduler.",
                }
            )
            self._wakeup.notify_all()

        if "calendar" in job.channels:
            self._sync_calendar(job)

        return {
            "status": "scheduled",
            "job": job.to_dict(),
        }

    def list_jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            return [job.to_dict() for job in self.jobs.values()]

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                raise KeyError(job_id)
            return job.to_dict()

    def cancel(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                raise KeyError(job_id)
            job.status = "cancelled"
            job.history.append(
                {
                    "timestamp": _isoformat(datetime.now(timezone.utc)),
                    "status": "cancelled",
                    "message": "Job cancelled manually.",
                }
            )
            return {"status": "cancelled", "job": job.to_dict()}

    def trigger(self, job_id: str, action_type: str = "reminder") -> dict[str, Any]:
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                raise KeyError(job_id)

        action = ScheduledAction(
            action_id=str(uuid.uuid4()),
            job_id=job_id,
            action_type=action_type,
            scheduled_for=datetime.now(timezone.utc),
        )
        result = self._dispatch(action)
        return {"status": "triggered", "result": result, "job": self.get_job(job_id)}

    def shutdown(self) -> None:
        with self._wakeup:
            self._running = False
            self._wakeup.notify_all()
        self._worker.join(timeout=5)

    def _enqueue_action(
        self,
        job: ScheduledJob,
        action_type: str,
        scheduled_for: datetime,
        offset_minutes: int = 0,
    ) -> None:
        action = ScheduledAction(
            action_id=str(uuid.uuid4()),
            job_id=job.job_id,
            action_type=action_type,
            scheduled_for=scheduled_for,
            offset_minutes=offset_minutes,
        )
        heapq.heappush(self._queue, (scheduled_for.timestamp(), self._sequence, action))
        self._sequence += 1

    def _run(self) -> None:
        while True:
            with self._wakeup:
                while self._running and not self._queue:
                    self._wakeup.wait()

                if not self._running:
                    return

                scheduled_for, _, action = self._queue[0]
                wait_seconds = scheduled_for - time.time()
                if wait_seconds > 0:
                    self._wakeup.wait(timeout=wait_seconds)
                    continue

                heapq.heappop(self._queue)

            self._dispatch(action)

    def _dispatch(self, action: ScheduledAction) -> dict[str, Any]:
        with self._lock:
            job = self.jobs.get(action.job_id)
            if not job:
                return {"status": "ignored", "reason": "job_missing", "action": action.to_dict()}
            if job.status == "cancelled":
                return {"status": "ignored", "reason": "job_cancelled", "action": action.to_dict()}

        delivery_results: list[dict[str, Any]] = []
        if "telegram" in job.channels:
            delivery_results.append(self._send_telegram(job, action))

        if action.action_type == "execute":
            with self._lock:
                job.status = "completed"

        history_record = {
            "timestamp": _isoformat(datetime.now(timezone.utc)),
            "status": action.action_type,
            "message": self._build_message(job, action),
            "delivery_results": delivery_results,
        }

        with self._lock:
            job.history.append(history_record)

        return {
            "status": "processed",
            "job_id": job.job_id,
            "action": action.to_dict(),
            "delivery_results": delivery_results,
        }

    def _send_telegram(self, job: ScheduledJob, action: ScheduledAction) -> dict[str, Any]:
        return {
            "channel": "telegram",
            "status": "queued",
            "message": self._build_message(job, action),
        }

    def _sync_calendar(self, job: ScheduledJob) -> None:
        result = self._create_or_update_calendar_event(job)
        job.history.append(
            {
                "timestamp": _isoformat(datetime.now(timezone.utc)),
                "status": "calendar_sync",
                "message": f"Calendar sync processed for {job.kind} '{job.title}'.",
                "delivery_results": [result],
            }
        )

    def _create_or_update_calendar_event(self, job: ScheduledJob) -> dict[str, Any]:
        credentials = self._load_calendar_credentials()
        token = (
            credentials.get("access_token")
            or credentials.get("token")
            or credentials.get("google_calendar_access_token")
        )
        calendar_id = str(job.metadata.get("calendar_id") or credentials.get("calendar_id") or "primary")

        if not token:
            return {
                "channel": "calendar",
                "status": "skipped",
                "reason": "missing_access_token_in_calendar_credentials",
            }

        payload = self._build_calendar_payload(job)
        encoded_calendar_id = parse.quote(calendar_id, safe="")
        existing_event_id = str(job.metadata.get("calendar_event_id") or "").strip()

        if existing_event_id:
            method = "PATCH"
            encoded_event_id = parse.quote(existing_event_id, safe="")
            url = (
                "https://www.googleapis.com/calendar/v3/calendars/"
                f"{encoded_calendar_id}/events/{encoded_event_id}"
            )
        else:
            method = "POST"
            url = f"https://www.googleapis.com/calendar/v3/calendars/{encoded_calendar_id}/events"

        req = request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method=method,
        )

        try:
            with request.urlopen(req, timeout=10) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
                calendar_event_id = response_payload.get("id")
                if calendar_event_id:
                    job.metadata["calendar_event_id"] = calendar_event_id
                return {
                    "channel": "calendar",
                    "status": "synced",
                    "calendar_id": calendar_id,
                    "calendar_event_id": calendar_event_id,
                    "html_link": response_payload.get("htmlLink"),
                }
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return {
                "channel": "calendar",
                "status": "failed",
                "calendar_id": calendar_id,
                "reason": f"google_calendar_http_error: {detail}",
            }
        except error.URLError as exc:
            return {
                "channel": "calendar",
                "status": "failed",
                "calendar_id": calendar_id,
                "reason": f"google_calendar_connection_error: {exc.reason}",
            }

    def _load_calendar_credentials(self) -> dict[str, Any]:
        if not os.path.exists(CREDENTIALS_PATH):
            return {}

        with open(CREDENTIALS_PATH, "r", encoding="utf-8") as file:
            raw = file.read().strip()

        if not raw:
            return {}

        loaded = json.loads(raw)
        if isinstance(loaded, dict):
            return loaded
        if isinstance(loaded, str):
            return {"access_token": loaded}
        return {}

    def _build_calendar_payload(self, job: ScheduledJob) -> dict[str, Any]:
        timezone_name = str(job.metadata.get("timezone") or "UTC")
        end_at = job.end_at or (
            job.execute_at + timedelta(minutes=int(job.metadata.get("default_duration_minutes") or 30))
        )

        attendees = []
        raw_attendees = job.metadata.get("attendees") or []
        if isinstance(raw_attendees, list):
            attendees = [
                {"email": attendee["email"]} if isinstance(attendee, dict) and attendee.get("email") else {"email": str(attendee)}
                for attendee in raw_attendees
                if attendee
            ]

        reminder_minutes = [
            {"method": "popup", "minutes": offset}
            for offset in job.reminder_offsets_minutes
        ]

        return {
            "summary": job.title,
            "description": job.description or f"{job.kind.title()} scheduled from UpLink.",
            "location": job.metadata.get("location"),
            "start": {
                "dateTime": job.execute_at.isoformat(),
                "timeZone": timezone_name,
            },
            "end": {
                "dateTime": end_at.isoformat(),
                "timeZone": timezone_name,
            },
            "attendees": attendees,
            "reminders": {
                "useDefault": False,
                "overrides": reminder_minutes,
            },
            "source": {
                "title": "UpLink Scheduler",
                "url": str(job.metadata.get("resource_url") or ""),
            },
            "conferenceData": {
                "createRequest": {
                    "requestId": job.job_id,
                }
            }
            if job.metadata.get("meeting_link")
            else None,
        }

    @staticmethod
    def _build_message(job: ScheduledJob, action: ScheduledAction) -> str:
        if action.action_type == "reminder":
            return (
                f"Reminder: {job.kind} '{job.title}' starts at "
                f"{job.execute_at.astimezone(timezone.utc).isoformat()} "
                f"(in {action.offset_minutes} minutes)."
            )
        return f"{job.kind.title()} '{job.title}' is due now."


class SchedulerRequestHandler(BaseHTTPRequestHandler):
    engine = SchedulerEngine()

    def do_GET(self) -> None:  # noqa: N802
        try:
            if self.path == "/health":
                self._send_json(
                    {
                        "service": "scheduler",
                        "status": "healthy",
                        "port": DEFAULT_PORT,
                    }
                )
                return

            if self.path == "/jobs":
                self._send_json({"jobs": self.engine.list_jobs()})
                return

            if self.path.startswith("/jobs/"):
                job_id = self.path.removeprefix("/jobs/")
                self._send_json({"job": self.engine.get_job(job_id)})
                return

            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
        except KeyError:
            self._send_json({"error": "Job not found."}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        try:
            if self.path in {"/schedule", "/tasks", "/events"}:
                payload = self._read_json()
                result = self.engine.schedule(payload)
                self._send_json(result, status=HTTPStatus.ACCEPTED)
                return

            if self.path.endswith("/cancel") and self.path.startswith("/jobs/"):
                job_id = self.path[len("/jobs/") : -len("/cancel")].strip("/")
                result = self.engine.cancel(job_id)
                self._send_json(result, status=HTTPStatus.OK)
                return

            if self.path.endswith("/trigger") and self.path.startswith("/jobs/"):
                job_id = self.path[len("/jobs/") : -len("/trigger")].strip("/")
                payload = self._read_json()
                result = self.engine.trigger(job_id, str(payload.get("action_type") or "reminder"))
                self._send_json(result, status=HTTPStatus.OK)
                return

            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except KeyError:
            self._send_json({"error": "Job not found."}, status=HTTPStatus.NOT_FOUND)

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


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = ThreadingHTTPServer((host, port), SchedulerRequestHandler)
    print(f"Scheduler listening on http://{host}:{port}")
    try:
        server.serve_forever()
    finally:
        SchedulerRequestHandler.engine.shutdown()


def main() -> None:
    run_server()


if __name__ == "__main__":
    main()
