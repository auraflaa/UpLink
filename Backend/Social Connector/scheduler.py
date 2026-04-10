from __future__ import annotations

import base64
import heapq
import hashlib
import json
import os
import secrets
import ssl
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
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
TELEGRAM_LINKS_PATH = os.path.join(os.path.dirname(__file__), "telegram_links.json")
TELEGRAM_LINK_TOKENS_PATH = os.path.join(os.path.dirname(__file__), "telegram_link_tokens.json")
DEFAULT_DEADLINE_REMINDER_OFFSETS = [10080, 4320, 1440]


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
        return list(DEFAULT_DEADLINE_REMINDER_OFFSETS)
    if isinstance(value, int):
        values = [value]
    elif isinstance(value, list):
        values = value
    elif isinstance(value, str):
        values = [part.strip() for part in value.split(",") if part.strip()]
    else:
        raise ValueError("Unsupported reminder_offsets_minutes format.")

    normalized = sorted({int(item) for item in values if int(item) >= 0}, reverse=True)
    return normalized or list(DEFAULT_DEADLINE_REMINDER_OFFSETS)


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _load_dotenv(path: str) -> dict[str, str]:
    if not os.path.exists(path):
        return {}

    loaded: dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                loaded[key] = value

    return loaded


def _get_env_setting(*keys: str) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value

    env_settings = _load_dotenv(ENV_PATH)
    for key in keys:
        value = env_settings.get(key)
        if value:
            return value

    return None


def _build_ssl_context() -> ssl.SSLContext:
    cafile = _get_env_setting("TELEGRAM_CA_BUNDLE", "SSL_CERT_FILE")
    if cafile:
        return ssl.create_default_context(cafile=cafile)

    allow_insecure = str(_get_env_setting("TELEGRAM_ALLOW_INSECURE_SSL") or "").strip().lower()
    if allow_insecure in {"1", "true", "yes"}:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    return ssl.create_default_context()


def _load_json_file(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default

    with open(path, "r", encoding="utf-8") as file:
        raw = file.read().strip()

    if not raw:
        return default

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _save_json_file(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


class TelegramLinkStore:
    """Stores pending link tokens and resolved Telegram chat mappings."""

    def __init__(
        self,
        links_path: str = TELEGRAM_LINKS_PATH,
        tokens_path: str = TELEGRAM_LINK_TOKENS_PATH,
    ) -> None:
        self.links_path = links_path
        self.tokens_path = tokens_path
        self._lock = threading.RLock()

    def create_link_token(self, user_id: str, expires_in_minutes: int = 15) -> dict[str, Any]:
        normalized_user_id = str(user_id).strip()
        if not normalized_user_id:
            raise ValueError("user_id is required to create a Telegram link token.")

        token = secrets.token_urlsafe(24)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=max(1, expires_in_minutes))
        token_record = {
            "token": token,
            "token_hash": self._hash_token(token),
            "user_id": normalized_user_id,
            "expires_at": _isoformat(expires_at),
            "created_at": _isoformat(datetime.now(timezone.utc)),
        }

        with self._lock:
            tokens = self._load_tokens()
            self._cleanup_tokens(tokens)
            tokens[token_record["token_hash"]] = token_record
            _save_json_file(self.tokens_path, tokens)

        bot_username = _get_env_setting("TELEGRAM_BOT_USERNAME", "BOT_USERNAME")
        return {
            "status": "token_created",
            "user_id": normalized_user_id,
            "token": token,
            "expires_at": token_record["expires_at"],
            "deep_link": f"https://t.me/{bot_username}?start={token}" if bot_username else None,
        }

    def consume_start_token(self, token: str, update: dict[str, Any]) -> dict[str, Any]:
        token_hash = self._hash_token(token)
        chat = update.get("message", {}).get("chat", {})
        sender = update.get("message", {}).get("from", {})
        chat_id = chat.get("id")
        if chat_id is None:
            raise ValueError("Telegram update did not include a chat ID.")

        with self._lock:
            tokens = self._load_tokens()
            self._cleanup_tokens(tokens)
            token_record = tokens.get(token_hash)
            if not token_record:
                raise ValueError("Invalid or expired Telegram link token.")

            links = self._load_links()
            links[token_record["user_id"]] = {
                "user_id": token_record["user_id"],
                "telegram_chat_id": str(chat_id),
                "telegram_from_id": str(sender.get("id") or ""),
                "telegram_username": sender.get("username"),
                "telegram_first_name": sender.get("first_name"),
                "linked_at": _isoformat(datetime.now(timezone.utc)),
            }
            tokens.pop(token_hash, None)
            _save_json_file(self.links_path, links)
            _save_json_file(self.tokens_path, tokens)

        return {
            "status": "linked",
            "user_id": token_record["user_id"],
            "telegram_chat_id": str(chat_id),
            "telegram_username": sender.get("username"),
        }

    def get_link(self, user_id: str) -> dict[str, Any] | None:
        normalized_user_id = str(user_id).strip()
        if not normalized_user_id:
            return None

        with self._lock:
            links = self._load_links()
            link = links.get(normalized_user_id)
            return dict(link) if link else None

    def resolve_chat_id(self, metadata: dict[str, Any]) -> str | None:
        explicit_chat_id = metadata.get("telegram_chat_id")
        if explicit_chat_id:
            return str(explicit_chat_id)

        user_id = (
            metadata.get("user_id")
            or metadata.get("app_user_id")
            or metadata.get("owner_id")
        )
        if not user_id:
            return None

        link = self.get_link(str(user_id))
        if not link:
            return None
        return str(link.get("telegram_chat_id") or "")

    def _load_links(self) -> dict[str, Any]:
        loaded = _load_json_file(self.links_path, {})
        return loaded if isinstance(loaded, dict) else {}

    def _load_tokens(self) -> dict[str, Any]:
        loaded = _load_json_file(self.tokens_path, {})
        return loaded if isinstance(loaded, dict) else {}

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _cleanup_tokens(tokens: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        expired = []
        for token_hash, token_record in tokens.items():
            expires_at = token_record.get("expires_at")
            if not expires_at:
                expired.append(token_hash)
                continue
            if _parse_datetime(expires_at) <= now:
                expired.append(token_hash)

        for token_hash in expired:
            tokens.pop(token_hash, None)


@dataclass(slots=True)
class ScheduledAction:
    action_id: str
    job_id: str
    action_type: str
    scheduled_for: datetime
    offset_minutes: int = 0
    revision: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "job_id": self.job_id,
            "action_type": self.action_type,
            "scheduled_for": _isoformat(self.scheduled_for),
            "offset_minutes": self.offset_minutes,
            "revision": self.revision,
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
    reminder_offsets_minutes: list[int] = field(
        default_factory=lambda: list(DEFAULT_DEADLINE_REMINDER_OFFSETS)
    )
    source: str = "event_handler"
    status: str = "scheduled"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    schedule_key: str | None = None
    revision: int = 0

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
            "schedule_key": self.schedule_key,
            "revision": self.revision,
        }


class SchedulerEngine:
    """Owns task/event scheduling, reminders, and delivery hooks."""

    def __init__(self) -> None:
        self.jobs: dict[str, ScheduledJob] = {}
        self.job_keys: dict[str, str] = {}
        self.telegram_links = TelegramLinkStore()
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
        metadata = dict(payload.get("metadata") or {})
        schedule_key = self._derive_schedule_key(payload, metadata)

        with self._wakeup:
            existing_job = self._resolve_existing_job(payload, schedule_key)
            if existing_job:
                updated_job = self._update_existing_job(
                    existing_job=existing_job,
                    payload=payload,
                    title=title,
                    kind=kind,
                    execute_at=execute_at,
                    end_at=_parse_datetime(end_at) if end_at else None,
                    channels=channels,
                    reminder_offsets=reminder_offsets,
                    metadata=metadata,
                    schedule_key=schedule_key,
                )
                self._wakeup.notify_all()
                if "calendar" in updated_job.channels:
                    self._sync_calendar(updated_job)
                return {
                    "status": "updated",
                    "job": updated_job.to_dict(),
                }

            if schedule_key:
                metadata["schedule_key"] = schedule_key

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
                metadata=metadata,
                schedule_key=schedule_key,
            )

            self.jobs[job.job_id] = job
            if schedule_key:
                self.job_keys[schedule_key] = job.job_id
            self._enqueue_job_actions(job)

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
            if job.schedule_key:
                self.job_keys.pop(job.schedule_key, None)
            job.history.append(
                {
                    "timestamp": _isoformat(datetime.now(timezone.utc)),
                    "status": "cancelled",
                    "message": "Job cancelled manually.",
                }
            )

        if "calendar" in job.channels:
            self._delete_calendar_event(job)

        with self._lock:
            return {"status": "cancelled", "job": job.to_dict()}

    def list_jira_projects(self) -> dict[str, Any]:
        return self._jira_request("GET", "/rest/api/3/project/search")

    def search_jira_issues(self, jql: str | None = None, max_results: int = 25) -> dict[str, Any]:
        configured_project_key = str(_get_env_setting("JIRA_PROJECT_KEY") or "").strip()
        default_jql = (
            f"project = {configured_project_key} ORDER BY updated DESC"
            if configured_project_key
            else "updated >= -30d ORDER BY updated DESC"
        )
        effective_jql = str(jql or "").strip() or default_jql
        query = parse.urlencode(
            {
                "jql": effective_jql,
                "maxResults": max(1, min(int(max_results), 100)),
                "fields": ",".join(
                    [
                        "summary",
                        "description",
                        "duedate",
                        "priority",
                        "status",
                        "assignee",
                        "project",
                        "issuetype",
                        "labels",
                    ]
                ),
            }
        )
        return self._jira_request("GET", f"/rest/api/3/search/jql?{query}")

    def create_jira_issue(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_key = str(
            payload.get("jira_project_key")
            or payload.get("project_key")
            or _get_env_setting("JIRA_PROJECT_KEY")
            or ""
        ).strip()
        summary = str(payload.get("summary") or payload.get("title") or "").strip()
        issue_type = str(payload.get("issue_type") or payload.get("jira_issue_type") or "Task").strip()
        description = str(payload.get("description") or "").strip()
        due_date = str(payload.get("due_date") or payload.get("jira_due_date") or "").strip()
        labels = payload.get("labels") or payload.get("jira_labels") or []

        if not project_key:
            raise ValueError("jira_project_key or project_key is required.")
        if not summary:
            raise ValueError("summary or title is required to create a Jira issue.")

        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }

        if description:
            fields["description"] = self._build_jira_description(description)
        if due_date:
            parsed_due = _parse_datetime(due_date)
            fields["duedate"] = parsed_due.date().isoformat()
        if labels:
            fields["labels"] = [str(label).strip() for label in labels if str(label).strip()]

        assignee = payload.get("assignee_account_id") or payload.get("jira_assignee_account_id")
        if assignee:
            fields["assignee"] = {"accountId": str(assignee)}

        priority = payload.get("priority") or payload.get("jira_priority")
        if priority:
            fields["priority"] = {"name": str(priority)}

        created_issue = self._jira_request("POST", "/rest/api/3/issue", payload={"fields": fields})
        if _as_bool(payload.get("schedule_due_date"), default=True):
            issue_key = str(created_issue.get("key") or "").strip()
            due_source = {
                "issue_key": issue_key,
                "project_key": project_key,
                "default_reminder_offsets_minutes": (
                    payload.get("reminder_offsets_minutes") or list(DEFAULT_DEADLINE_REMINDER_OFFSETS)
                ),
            }
            schedule_result = self.schedule_jira_issue_due_date(due_source, issue_payload=created_issue)
            created_issue["scheduled_due_date"] = schedule_result

        return created_issue

    def schedule_jira_issue_due_date(
        self,
        payload: dict[str, Any],
        issue_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        issue = issue_payload or self._fetch_jira_issue(
            issue_key=str(payload.get("issue_key") or payload.get("jira_issue_key") or "").strip(),
            issue_id=str(payload.get("issue_id") or payload.get("jira_issue_id") or "").strip(),
        )
        normalized_job = self._build_schedule_payload_from_jira_issue(
            issue,
            default_offsets=payload.get("default_reminder_offsets_minutes"),
        )
        if not normalized_job:
            raise ValueError("Jira issue does not have a due date to schedule.")
        return self.schedule(normalized_job)

    def analyze_jira_link(self, jira_url: str) -> dict[str, Any]:
        parsed = self._detect_jira_target(jira_url)
        entity_type = parsed.get("entity_type")
        base_url = parsed["base_url"]

        if entity_type == "issue":
            issue = self._fetch_jira_issue_public(base_url=base_url, issue_key=parsed["issue_key"])
            return {
                "status": "completed",
                "source_type": "jira",
                "entity_type": "issue",
                "input_url": jira_url,
                "issue_key": issue.get("key"),
                "analysis": self._summarise_jira_issue(issue),
                "raw": issue,
            }

        if entity_type == "project":
            project = self._fetch_jira_project_public(base_url=base_url, project_key=parsed["project_key"])
            return {
                "status": "completed",
                "source_type": "jira",
                "entity_type": "project",
                "input_url": jira_url,
                "project_key": project.get("key"),
                "analysis": self._summarise_jira_project(project),
                "raw": project,
            }

        return {
            "status": "detected",
            "source_type": "jira",
            "entity_type": entity_type,
            "input_url": jira_url,
            "message": "Jira site detected. Detailed analysis currently supports project and issue links.",
        }

    def build_jira_rag_document(self, payload: dict[str, Any]) -> dict[str, Any]:
        jira_url = str(payload.get("url") or payload.get("jira_url") or "").strip()
        if not jira_url:
            raise ValueError("url or jira_url is required.")

        analysis = self.analyze_jira_link(jira_url)
        entity_type = str(analysis.get("entity_type") or "unknown")
        raw = analysis.get("raw") or {}

        if entity_type == "issue":
            rag_document = self._build_issue_rag_document(jira_url, raw)
        elif entity_type == "project":
            rag_document = self._build_project_rag_document(jira_url, raw)
        else:
            rag_document = {
                "document_id": f"jira-site::{jira_url}",
                "title": "Jira Site Link",
                "content": analysis.get("message", "Jira site detected."),
                "metadata": {
                    "source_type": "jira",
                    "entity_type": entity_type,
                    "input_url": jira_url,
                },
            }

        return {
            "status": "completed",
            "source_type": "jira",
            "entity_type": entity_type,
            "input_url": jira_url,
            "analysis": analysis.get("analysis"),
            "rag_document": rag_document,
        }

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

    def create_telegram_link_token(self, payload: dict[str, Any]) -> dict[str, Any]:
        user_id = str(payload.get("user_id") or payload.get("app_user_id") or payload.get("owner_id") or "").strip()
        expires_in_minutes = int(payload.get("expires_in_minutes") or 15)
        result = self.telegram_links.create_link_token(user_id, expires_in_minutes=expires_in_minutes)
        existing_link = self.telegram_links.get_link(user_id)
        if existing_link:
            result["existing_link"] = existing_link
        return result

    def process_telegram_update(self, payload: dict[str, Any]) -> dict[str, Any]:
        message = payload.get("message") or payload.get("edited_message") or {}
        text = str(message.get("text") or "").strip()
        if not text:
            return {"status": "ignored", "reason": "missing_message_text"}

        if not text.startswith("/start"):
            return {"status": "ignored", "reason": "unsupported_message"}

        _, _, raw_token = text.partition(" ")
        token = raw_token.strip()
        if not token:
            return {"status": "ignored", "reason": "missing_start_token"}

        start_update = {"message": message}
        link_result = self.telegram_links.consume_start_token(token, start_update)
        confirmation = self._send_direct_telegram_message(
            chat_id=link_result["telegram_chat_id"],
            text="Telegram notifications are now linked to your UpLink account.",
            parse_mode=None,
        )
        return {
            "status": "processed",
            "link_result": link_result,
            "confirmation": confirmation,
        }

    def get_telegram_link(self, user_id: str) -> dict[str, Any]:
        link = self.telegram_links.get_link(user_id)
        if not link:
            raise KeyError(user_id)
        return link

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
            revision=job.revision,
        )
        heapq.heappush(self._queue, (scheduled_for.timestamp(), self._sequence, action))
        self._sequence += 1

    def _enqueue_job_actions(self, job: ScheduledJob) -> None:
        self._enqueue_action(job, "execute", job.execute_at)
        for offset in job.reminder_offsets_minutes:
            reminder_time = job.execute_at - timedelta(minutes=offset)
            if reminder_time > datetime.now(timezone.utc):
                self._enqueue_action(job, "reminder", reminder_time, offset_minutes=offset)

    def _resolve_existing_job(self, payload: dict[str, Any], schedule_key: str | None) -> ScheduledJob | None:
        explicit_job_id = str(payload.get("job_id") or "").strip()
        if explicit_job_id:
            existing = self.jobs.get(explicit_job_id)
            if existing and existing.status != "cancelled":
                return existing

        if schedule_key:
            existing_job_id = self.job_keys.get(schedule_key)
            if existing_job_id:
                existing = self.jobs.get(existing_job_id)
                if existing and existing.status != "cancelled":
                    return existing

        return None

    def _update_existing_job(
        self,
        existing_job: ScheduledJob,
        payload: dict[str, Any],
        title: str,
        kind: str,
        execute_at: datetime,
        end_at: datetime | None,
        channels: list[str],
        reminder_offsets: list[int],
        metadata: dict[str, Any],
        schedule_key: str | None,
    ) -> ScheduledJob:
        previous_schedule_key = existing_job.schedule_key
        merged_metadata = dict(existing_job.metadata)
        merged_metadata.update(metadata)

        if previous_schedule_key and not schedule_key:
            schedule_key = previous_schedule_key
        if schedule_key:
            merged_metadata["schedule_key"] = schedule_key

        existing_job.title = title
        existing_job.kind = kind
        existing_job.description = str(payload.get("description") or "").strip()
        existing_job.execute_at = execute_at
        existing_job.end_at = end_at
        existing_job.channels = channels
        existing_job.reminder_offsets_minutes = reminder_offsets
        existing_job.source = str(payload.get("source") or existing_job.source or "event_handler")
        existing_job.status = "scheduled"
        existing_job.metadata = merged_metadata
        existing_job.revision += 1
        existing_job.schedule_key = schedule_key

        if previous_schedule_key and previous_schedule_key != schedule_key:
            self.job_keys.pop(previous_schedule_key, None)
        if schedule_key:
            self.job_keys[schedule_key] = existing_job.job_id

        self._enqueue_job_actions(existing_job)
        existing_job.history.append(
            {
                "timestamp": _isoformat(datetime.now(timezone.utc)),
                "status": "updated",
                "message": "Job schedule updated by scheduler.",
            }
        )
        return existing_job

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
            if action.revision != job.revision:
                return {"status": "ignored", "reason": "stale_action", "action": action.to_dict()}

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
        token = (
            _get_env_setting("TELEGRAM_BOT_TOKEN", "BOT_TOKEN", "TELEGRAM_TOKEN")
        )
        chat_id = (
            self.telegram_links.resolve_chat_id(job.metadata)
            or _get_env_setting("TELEGRAM_CHAT_ID", "CHAT_ID")
        )
        parse_mode = (
            str(job.metadata.get("telegram_parse_mode") or "").strip()
            or _get_env_setting("TELEGRAM_PARSE_MODE")
            or "Markdown"
        )
        message = self._build_telegram_message(job, action)

        if not token:
            return {
                "channel": "telegram",
                "status": "skipped",
                "reason": "missing_telegram_bot_token",
            }

        if not chat_id:
            return {
                "channel": "telegram",
                "status": "skipped",
                "reason": "missing_telegram_chat_id",
                "message": message,
            }

        return self._send_direct_telegram_message(str(chat_id), message, parse_mode=parse_mode)

    def _send_direct_telegram_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str | None,
    ) -> dict[str, Any]:
        token = _get_env_setting("TELEGRAM_BOT_TOKEN", "BOT_TOKEN", "TELEGRAM_TOKEN")
        if not token:
            return {
                "channel": "telegram",
                "status": "skipped",
                "reason": "missing_telegram_bot_token",
            }

        payload = {
            "chat_id": str(chat_id),
            "text": text,
            "disable_web_page_preview": True,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        req = request.Request(
            url=f"https://api.telegram.org/bot{token}/sendMessage",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=10, context=_build_ssl_context()) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
                telegram_result = response_payload.get("result", {})
                return {
                    "channel": "telegram",
                    "status": "sent",
                    "chat_id": str(chat_id),
                    "message_id": telegram_result.get("message_id"),
                }
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return {
                "channel": "telegram",
                "status": "failed",
                "chat_id": str(chat_id),
                "reason": f"telegram_http_error: {detail}",
            }
        except error.URLError as exc:
            return {
                "channel": "telegram",
                "status": "failed",
                "chat_id": str(chat_id),
                "reason": f"telegram_connection_error: {exc.reason}",
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
        credentials, token_error = self._resolve_google_calendar_access_token()
        if token_error:
            return {
                "channel": "calendar",
                "status": "failed",
                "reason": token_error,
            }

        token = str(credentials.get("access_token") or "").strip()
        calendar_id = str(job.metadata.get("calendar_id") or credentials.get("calendar_id") or "primary")

        payload = self._build_calendar_payload(job)
        encoded_calendar_id = parse.quote(calendar_id, safe="")
        existing_event_id = str(job.metadata.get("calendar_event_id") or "").strip()
        query_params: dict[str, Any] = {}
        if _as_bool(job.metadata.get("create_meet_link")):
            query_params["conferenceDataVersion"] = 1

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

        if query_params:
            url = f"{url}?{parse.urlencode(query_params)}"

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

    def _delete_calendar_event(self, job: ScheduledJob) -> dict[str, Any]:
        existing_event_id = str(job.metadata.get("calendar_event_id") or "").strip()
        if not existing_event_id:
            result = {
                "channel": "calendar",
                "status": "skipped",
                "reason": "missing_calendar_event_id",
            }
            job.history.append(
                {
                    "timestamp": _isoformat(datetime.now(timezone.utc)),
                    "status": "calendar_delete",
                    "message": f"No Google Calendar event ID stored for '{job.title}'.",
                    "delivery_results": [result],
                }
            )
            return result

        credentials, token_error = self._resolve_google_calendar_access_token()
        if token_error:
            result = {
                "channel": "calendar",
                "status": "failed",
                "reason": token_error,
            }
            job.history.append(
                {
                    "timestamp": _isoformat(datetime.now(timezone.utc)),
                    "status": "calendar_delete",
                    "message": f"Failed to delete Google Calendar event for '{job.title}'.",
                    "delivery_results": [result],
                }
            )
            return result

        calendar_id = str(job.metadata.get("calendar_id") or credentials.get("calendar_id") or "primary")
        encoded_calendar_id = parse.quote(calendar_id, safe="")
        encoded_event_id = parse.quote(existing_event_id, safe="")
        url = (
            "https://www.googleapis.com/calendar/v3/calendars/"
            f"{encoded_calendar_id}/events/{encoded_event_id}"
        )
        req = request.Request(
            url=url,
            headers={"Authorization": f"Bearer {credentials['access_token']}"},
            method="DELETE",
        )

        try:
            with request.urlopen(req, timeout=10) as response:
                delete_status = response.status
            result = {
                "channel": "calendar",
                "status": "deleted",
                "calendar_id": calendar_id,
                "calendar_event_id": existing_event_id,
                "http_status": delete_status,
            }
            job.metadata.pop("calendar_event_id", None)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            result = {
                "channel": "calendar",
                "status": "failed",
                "calendar_id": calendar_id,
                "calendar_event_id": existing_event_id,
                "reason": f"google_calendar_http_error: {detail}",
            }
        except error.URLError as exc:
            result = {
                "channel": "calendar",
                "status": "failed",
                "calendar_id": calendar_id,
                "calendar_event_id": existing_event_id,
                "reason": f"google_calendar_connection_error: {exc.reason}",
            }

        job.history.append(
            {
                "timestamp": _isoformat(datetime.now(timezone.utc)),
                "status": "calendar_delete",
                "message": f"Processed Google Calendar deletion for '{job.title}'.",
                "delivery_results": [result],
            }
        )
        return result

    def _jira_request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        base_url_override: str | None = None,
        allow_anonymous: bool = False,
    ) -> dict[str, Any]:
        configured_base_url = str(_get_env_setting("JIRA_BASE_URL", "JIRA_URL", "JIRA_DOMAIN") or "").strip().rstrip("/")
        base_url = str(base_url_override or configured_base_url).strip().rstrip("/")
        if not base_url:
            raise ValueError("Missing Jira base URL. Set JIRA_BASE_URL in Scheduler/.env")

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self._can_use_jira_auth(base_url):
            email = str(_get_env_setting("JIRA_EMAIL", "ATLASSIAN_EMAIL") or "").strip()
            token = str(_get_env_setting("JIRA_API_TOKEN", "JIRA_API_KEY", "ATLASSIAN_API_TOKEN") or "").strip()
            if not email:
                raise ValueError("Missing Jira email. Set JIRA_EMAIL in Scheduler/.env")
            if not token:
                raise ValueError("Missing Jira API token/key. Set JIRA_API_TOKEN or JIRA_API_KEY in Scheduler/.env")

            auth_value = base64.b64encode(f"{email}:{token}".encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {auth_value}"
        elif not allow_anonymous:
            raise ValueError(
                "Jira auth is only configured for the Jira site in Scheduler/.env. Arbitrary external Jira links require public access."
            )

        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = request.Request(
            url=f"{base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )

        try:
            with request.urlopen(req, timeout=15) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return {"status": response.status}
                return json.loads(raw)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ValueError(f"Jira API request failed: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Unable to reach Jira at {base_url}: {exc.reason}") from exc

    def _fetch_jira_issue_public(self, base_url: str, issue_key: str) -> dict[str, Any]:
        query = parse.urlencode(
            {
                "fields": "summary,description,duedate,priority,status,assignee,project,issuetype,labels",
            }
        )
        try:
            return self._jira_request(
                "GET",
                f"/rest/api/3/issue/{issue_key}?{query}",
                base_url_override=base_url,
                allow_anonymous=True,
            )
        except ValueError as exc:
            raise ValueError(f"Unable to access Jira issue {issue_key}: {exc}") from exc

    def _fetch_jira_project_public(self, base_url: str, project_key: str) -> dict[str, Any]:
        try:
            return self._jira_request(
                "GET",
                f"/rest/api/3/project/{project_key}",
                base_url_override=base_url,
                allow_anonymous=True,
            )
        except ValueError as exc:
            raise ValueError(f"Unable to access Jira project {project_key}: {exc}") from exc

    def _fetch_jira_issue(self, issue_key: str = "", issue_id: str = "") -> dict[str, Any]:
        identifier = issue_key or issue_id
        if not identifier:
            raise ValueError("issue_key or issue_id is required to fetch a Jira issue.")

        query = parse.urlencode(
            {
                "fields": "summary,description,duedate,priority,status,assignee,project,issuetype,labels",
            }
        )
        return self._jira_request("GET", f"/rest/api/3/issue/{identifier}?{query}")

    def _build_schedule_payload_from_jira_issue(
        self,
        issue: dict[str, Any],
        default_offsets: Any = None,
    ) -> dict[str, Any] | None:
        fields = issue.get("fields") or {}
        due_date_raw = str(fields.get("duedate") or "").strip()
        if not due_date_raw:
            return None

        due_datetime = _parse_datetime(f"{due_date_raw}T09:00:00+00:00")
        project = fields.get("project") or {}
        priority = fields.get("priority") or {}
        status = fields.get("status") or {}
        assignee = fields.get("assignee") or {}
        issue_type = fields.get("issuetype") or {}
        issue_key = str(issue.get("key") or "").strip()
        base_url = str(_get_env_setting("JIRA_BASE_URL", "JIRA_URL", "JIRA_DOMAIN") or "").strip().rstrip("/")
        issue_url = f"{base_url}/browse/{issue_key}" if base_url and issue_key else ""

        return {
            "title": str(fields.get("summary") or issue_key or "Jira issue"),
            "kind": "task",
            "description": f"Jira issue {issue_key} due date reminder.",
            "execute_at": _isoformat(due_datetime),
            "channels": ["telegram"],
            "reminder_offsets_minutes": default_offsets or list(DEFAULT_DEADLINE_REMINDER_OFFSETS),
            "source": "jira",
            "metadata": {
                "jira_issue_id": issue.get("id"),
                "jira_issue_key": issue_key,
                "jira_project_key": project.get("key"),
                "jira_project_id": project.get("id"),
                "jira_issue_type": issue_type.get("name"),
                "jira_status": status.get("name"),
                "jira_priority": priority.get("name"),
                "jira_assignee": assignee.get("displayName"),
                "jira_labels": fields.get("labels") or [],
                "jira_url": issue_url,
                "resource_url": issue_url,
            },
        }

    def _can_use_jira_auth(self, base_url: str) -> bool:
        configured_base_url = str(_get_env_setting("JIRA_BASE_URL", "JIRA_URL", "JIRA_DOMAIN") or "").strip().rstrip("/")
        if not configured_base_url:
            return False
        return configured_base_url.lower() == base_url.lower()

    @staticmethod
    def _detect_jira_target(jira_url: str) -> dict[str, Any]:
        parsed = parse.urlparse(jira_url)
        host = parsed.netloc.lower()
        if "atlassian.net" not in host:
            raise ValueError("The provided URL is not a Jira Cloud URL.")

        base_url = f"{parsed.scheme or 'https'}://{host}"
        path_parts = [part for part in parsed.path.strip("/").split("/") if part]
        lowered = [part.lower() for part in path_parts]

        if len(path_parts) >= 2 and lowered[0] == "browse":
            return {
                "entity_type": "issue",
                "base_url": base_url,
                "issue_key": path_parts[1],
            }

        if "projects" in lowered:
            project_index = lowered.index("projects")
            if len(path_parts) > project_index + 1:
                return {
                    "entity_type": "project",
                    "base_url": base_url,
                    "project_key": path_parts[project_index + 1],
                }

        return {
            "entity_type": "site",
            "base_url": base_url,
        }

    @staticmethod
    def _summarise_jira_issue(issue: dict[str, Any]) -> str:
        fields = issue.get("fields") or {}
        project = fields.get("project") or {}
        status = fields.get("status") or {}
        priority = fields.get("priority") or {}
        assignee = fields.get("assignee") or {}
        issue_type = fields.get("issuetype") or {}

        lines = [
            f"Issue {issue.get('key')} belongs to project {project.get('key', 'unknown')}.",
            f"Summary: {fields.get('summary', 'No summary available')}.",
            f"Type: {issue_type.get('name', 'Unknown')}.",
            f"Status: {status.get('name', 'Unknown')}.",
            f"Priority: {priority.get('name', 'Unknown')}.",
        ]
        if assignee.get("displayName"):
            lines.append(f"Assigned to {assignee['displayName']}.")
        if fields.get("duedate"):
            lines.append(f"Due date: {fields['duedate']}.")
        labels = fields.get("labels") or []
        if labels:
            lines.append(f"Labels: {', '.join(labels)}.")
        return " ".join(lines)

    @staticmethod
    def _summarise_jira_project(project: dict[str, Any]) -> str:
        style = project.get("style", "")
        category = (project.get("projectCategory") or {}).get("name")
        summary = [
            f"Project {project.get('key', 'unknown')} is named {project.get('name', 'unknown')}."
        ]
        if style:
            summary.append(f"Style: {style}.")
        if category:
            summary.append(f"Category: {category}.")
        lead = (project.get("lead") or {}).get("displayName")
        if lead:
            summary.append(f"Lead: {lead}.")
        return " ".join(summary)

    @staticmethod
    def _build_issue_rag_document(jira_url: str, issue: dict[str, Any]) -> dict[str, Any]:
        fields = issue.get("fields") or {}
        project = fields.get("project") or {}
        issue_type = fields.get("issuetype") or {}
        status = fields.get("status") or {}
        priority = fields.get("priority") or {}
        assignee = fields.get("assignee") or {}
        reporter = fields.get("reporter") or {}
        labels = fields.get("labels") or []
        description = fields.get("description")

        description_text = json.dumps(description) if isinstance(description, (dict, list)) else str(description or "")
        lines = [
            f"Jira Issue: {issue.get('key', 'unknown')}",
            f"Project: {project.get('key', 'unknown')} - {project.get('name', 'unknown')}",
            f"Summary: {fields.get('summary', 'No summary available')}",
            f"Type: {issue_type.get('name', 'Unknown')}",
            f"Status: {status.get('name', 'Unknown')}",
            f"Priority: {priority.get('name', 'Unknown')}",
            f"Assignee: {assignee.get('displayName', 'Unassigned')}",
            f"Reporter: {reporter.get('displayName', 'Unknown')}",
            f"Due Date: {fields.get('duedate', 'Not set')}",
            f"Labels: {', '.join(labels) if labels else 'None'}",
            f"URL: {jira_url}",
        ]
        if description_text:
            lines.append("Description:")
            lines.append(description_text)

        issue_key = str(issue.get("key") or "unknown")
        return {
            "document_id": f"jira-issue::{issue_key}",
            "title": f"Jira Issue {issue_key}",
            "content": "\n".join(lines),
            "metadata": {
                "source_type": "jira",
                "entity_type": "issue",
                "jira_issue_id": issue.get("id"),
                "jira_issue_key": issue_key,
                "jira_project_key": project.get("key"),
                "jira_status": status.get("name"),
                "jira_priority": priority.get("name"),
                "jira_assignee": assignee.get("displayName"),
                "jira_url": jira_url,
            },
        }

    @staticmethod
    def _build_project_rag_document(jira_url: str, project: dict[str, Any]) -> dict[str, Any]:
        category = (project.get("projectCategory") or {}).get("name")
        lead = (project.get("lead") or {}).get("displayName")
        description = str(project.get("description") or "").strip()

        lines = [
            f"Jira Project: {project.get('key', 'unknown')}",
            f"Name: {project.get('name', 'unknown')}",
            f"Style: {project.get('style', 'Unknown')}",
            f"Type: {project.get('projectTypeKey', 'Unknown')}",
            f"Category: {category or 'None'}",
            f"Lead: {lead or 'Unknown'}",
            f"URL: {jira_url}",
        ]
        if description:
            lines.append("Description:")
            lines.append(description)

        project_key = str(project.get("key") or "unknown")
        return {
            "document_id": f"jira-project::{project_key}",
            "title": f"Jira Project {project_key}",
            "content": "\n".join(lines),
            "metadata": {
                "source_type": "jira",
                "entity_type": "project",
                "jira_project_id": project.get("id"),
                "jira_project_key": project_key,
                "jira_project_name": project.get("name"),
                "jira_url": jira_url,
            },
        }

    @staticmethod
    def _build_jira_description(text: str) -> dict[str, Any]:
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": text,
                        }
                    ],
                }
            ],
        }

    def _resolve_google_calendar_access_token(self) -> tuple[dict[str, Any], str | None]:
        credentials = self._load_calendar_credentials()
        validation_error = self._validate_calendar_credentials(credentials)
        if validation_error:
            return credentials, validation_error

        expires_at_raw = credentials.get("expires_at")
        access_token = str(
            credentials.get("access_token")
            or credentials.get("token")
            or credentials.get("google_calendar_access_token")
            or ""
        ).strip()

        should_refresh = False
        if expires_at_raw:
            expires_at = _parse_datetime(expires_at_raw)
            should_refresh = expires_at <= datetime.now(timezone.utc) + timedelta(minutes=5)
        elif not access_token and credentials.get("refresh_token"):
            should_refresh = True

        if should_refresh:
            refreshed, refresh_error = self._refresh_google_access_token(credentials)
            if refresh_error:
                return credentials, refresh_error
            credentials = refreshed
            access_token = str(credentials.get("access_token") or "").strip()

        if not access_token:
            return credentials, "missing_google_calendar_access_token"

        return credentials, None

    @staticmethod
    def _validate_calendar_credentials(credentials: dict[str, Any]) -> str | None:
        if not credentials:
            return "missing_calendar_credentials"

        access_token = credentials.get("access_token") or credentials.get("token") or credentials.get("google_calendar_access_token")
        refresh_token = credentials.get("refresh_token")
        client_id = credentials.get("client_id")
        client_secret = credentials.get("client_secret")

        if access_token:
            return None

        if refresh_token and client_id and client_secret:
            return None

        return (
            "calendar_credentials_incomplete: expected access_token, or refresh_token + client_id + client_secret"
        )

    def _refresh_google_access_token(self, credentials: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
        refresh_token = str(credentials.get("refresh_token") or "").strip()
        client_id = str(credentials.get("client_id") or "").strip()
        client_secret = str(credentials.get("client_secret") or "").strip()
        token_uri = str(credentials.get("token_uri") or "https://oauth2.googleapis.com/token").strip()

        if not refresh_token or not client_id or not client_secret:
            return credentials, "calendar_refresh_not_possible: missing refresh_token/client_id/client_secret"

        token_request_body = parse.urlencode(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode("utf-8")
        req = request.Request(
            url=token_uri,
            data=token_request_body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=10) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return credentials, f"calendar_refresh_http_error: {detail}"
        except error.URLError as exc:
            return credentials, f"calendar_refresh_connection_error: {exc.reason}"

        new_access_token = str(response_payload.get("access_token") or "").strip()
        if not new_access_token:
            return credentials, "calendar_refresh_failed: access_token_missing_in_response"

        refreshed = dict(credentials)
        refreshed["access_token"] = new_access_token
        refreshed["token_type"] = response_payload.get("token_type", refreshed.get("token_type", "Bearer"))
        refreshed["scope"] = response_payload.get("scope", refreshed.get("scope"))
        refreshed["refreshed_at"] = _isoformat(datetime.now(timezone.utc))

        expires_in = response_payload.get("expires_in")
        if expires_in:
            refreshed["expires_at"] = _isoformat(
                datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
            )

        _save_json_file(CREDENTIALS_PATH, refreshed)
        return refreshed, None

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

        payload = {
            "summary": str(job.metadata.get("calendar_summary") or job.title),
            "description": str(
                job.metadata.get("calendar_description")
                or job.description
                or f"{job.kind.title()} scheduled from UpLink."
            ),
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
        }
        if job.metadata.get("calendar_visibility"):
            payload["visibility"] = job.metadata["calendar_visibility"]
        if job.metadata.get("calendar_status"):
            payload["status"] = job.metadata["calendar_status"]

        recurrence = job.metadata.get("recurrence")
        if isinstance(recurrence, list) and recurrence:
            payload["recurrence"] = [str(item) for item in recurrence if str(item).strip()]
        elif isinstance(recurrence, str) and recurrence.strip():
            payload["recurrence"] = [recurrence.strip()]

        if _as_bool(job.metadata.get("create_meet_link")):
            payload["conferenceData"] = {
                "createRequest": {
                    "requestId": f"{job.job_id}-{uuid.uuid4().hex[:8]}",
                }
            }

        if job.metadata.get("meeting_link"):
            payload["description"] = (
                f"{payload['description']}\nMeeting link: {job.metadata['meeting_link']}".strip()
            )

        return payload

    @staticmethod
    def _build_message(job: ScheduledJob, action: ScheduledAction) -> str:
        if action.action_type == "reminder":
            return (
                f"Reminder: {job.kind} '{job.title}' starts at "
                f"{job.execute_at.astimezone(timezone.utc).isoformat()} "
                f"(in {SchedulerEngine._format_offset_minutes(action.offset_minutes)})."
            )
        return f"{job.kind.title()} '{job.title}' is due now."

    @staticmethod
    def _build_telegram_message(job: ScheduledJob, action: ScheduledAction) -> str:
        execute_at = job.execute_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        description = job.description.strip()
        location = str(job.metadata.get("location") or "").strip()
        resource_url = str(job.metadata.get("resource_url") or "").strip()
        platform = str(job.metadata.get("platform") or "").strip()
        organizer = str(job.metadata.get("organizer") or "").strip()
        deadline = str(job.metadata.get("deadline") or "").strip()

        if action.action_type == "reminder":
            heading = f"*Reminder*: {job.title}"
            timing = f"In {SchedulerEngine._format_offset_minutes(action.offset_minutes)}"
        else:
            heading = f"*Due Now*: {job.title}"
            timing = "Happening now"

        lines = [
            heading,
            f"Type: {job.kind}",
            f"When: {execute_at}",
            f"Status: {timing}",
        ]
        if platform:
            lines.append(f"Platform: {platform}")
        if organizer:
            lines.append(f"Organizer: {organizer}")
        if deadline:
            lines.append(f"Deadline: {deadline}")
        if description:
            lines.append(f"Details: {description}")
        if location:
            lines.append(f"Location: {location}")
        if resource_url:
            lines.append(f"Link: {resource_url}")

        return "\n".join(lines)

    @staticmethod
    def _format_offset_minutes(offset_minutes: int) -> str:
        if offset_minutes % 10080 == 0:
            weeks = offset_minutes // 10080
            return f"{weeks} week" if weeks == 1 else f"{weeks} weeks"
        if offset_minutes % 1440 == 0:
            days = offset_minutes // 1440
            return f"{days} day" if days == 1 else f"{days} days"
        if offset_minutes % 60 == 0:
            hours = offset_minutes // 60
            return f"{hours} hour" if hours == 1 else f"{hours} hours"
        return f"{offset_minutes} minutes"

    @staticmethod
    def _derive_schedule_key(payload: dict[str, Any], metadata: dict[str, Any]) -> str | None:
        explicit_schedule_key = str(
            payload.get("schedule_key") or metadata.get("schedule_key") or ""
        ).strip()
        if explicit_schedule_key:
            return explicit_schedule_key

        source_id = str(metadata.get("source_id") or "").strip()
        if source_id:
            return f"scrape:source_id:{source_id}"

        event_url = str(metadata.get("event_url") or metadata.get("resource_url") or "").strip()
        if event_url:
            return f"scrape:event_url:{event_url}"

        jira_issue_key = str(metadata.get("jira_issue_key") or "").strip()
        if jira_issue_key:
            return f"jira:issue:{jira_issue_key}"

        calendar_event_id = str(metadata.get("calendar_event_id") or "").strip()
        if calendar_event_id:
            return f"calendar:event:{calendar_event_id}"

        return None


class SchedulerRequestHandler(BaseHTTPRequestHandler):
    engine = SchedulerEngine()

    def do_GET(self) -> None:  # noqa: N802
        try:
            parsed = parse.urlparse(self.path)
            path = parsed.path
            query = parse.parse_qs(parsed.query)

            if path == "/health":
                self._send_json(
                    {
                        "service": "scheduler",
                        "status": "healthy",
                        "port": DEFAULT_PORT,
                    }
                )
                return

            if path == "/jobs":
                self._send_json({"jobs": self.engine.list_jobs()})
                return

            if path == "/jira/projects":
                self._send_json(self.engine.list_jira_projects())
                return

            if path == "/jira/issues":
                jql = query.get("jql", [None])[0]
                max_results = int(query.get("max_results", ["25"])[0])
                self._send_json(self.engine.search_jira_issues(jql=jql, max_results=max_results))
                return

            if path == "/jira/analyze-link":
                jira_url = query.get("url", [None])[0]
                if not jira_url:
                    self._send_json({"error": "Missing Jira url query parameter."}, status=HTTPStatus.BAD_REQUEST)
                    return
                self._send_json(self.engine.analyze_jira_link(jira_url))
                return

            if path == "/jira/rag-document":
                jira_url = query.get("url", [None])[0]
                if not jira_url:
                    self._send_json({"error": "Missing Jira url query parameter."}, status=HTTPStatus.BAD_REQUEST)
                    return
                self._send_json(self.engine.build_jira_rag_document({"url": jira_url}))
                return

            if path.startswith("/telegram/links/"):
                user_id = path.removeprefix("/telegram/links/")
                self._send_json({"link": self.engine.get_telegram_link(user_id)})
                return

            if path.startswith("/jobs/"):
                job_id = path.removeprefix("/jobs/")
                self._send_json({"job": self.engine.get_job(job_id)})
                return

            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
        except KeyError:
            self._send_json({"error": "Job not found."}, status=HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except RuntimeError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)

    def do_POST(self) -> None:  # noqa: N802
        try:
            parsed = parse.urlparse(self.path)
            path = parsed.path

            if path in {"/schedule", "/tasks", "/events"}:
                payload = self._read_json()
                result = self.engine.schedule(payload)
                self._send_json(result, status=HTTPStatus.ACCEPTED)
                return

            if path == "/jira/issues":
                payload = self._read_json()
                result = self.engine.create_jira_issue(payload)
                self._send_json(result, status=HTTPStatus.CREATED)
                return

            if path == "/jira/analyze-link":
                payload = self._read_json()
                jira_url = str(payload.get("url") or payload.get("jira_url") or "").strip()
                if not jira_url:
                    self._send_json({"error": "url or jira_url is required."}, status=HTTPStatus.BAD_REQUEST)
                    return
                result = self.engine.analyze_jira_link(jira_url)
                self._send_json(result, status=HTTPStatus.OK)
                return

            if path == "/jira/rag-document":
                payload = self._read_json()
                result = self.engine.build_jira_rag_document(payload)
                self._send_json(result, status=HTTPStatus.OK)
                return

            if path == "/jira/issues/schedule":
                payload = self._read_json()
                result = self.engine.schedule_jira_issue_due_date(payload)
                self._send_json(result, status=HTTPStatus.ACCEPTED)
                return

            if path == "/telegram/link-token":
                payload = self._read_json()
                result = self.engine.create_telegram_link_token(payload)
                self._send_json(result, status=HTTPStatus.CREATED)
                return

            if path == "/telegram/update":
                payload = self._read_json()
                result = self.engine.process_telegram_update(payload)
                self._send_json(result, status=HTTPStatus.OK)
                return

            if path.endswith("/cancel") and path.startswith("/jobs/"):
                job_id = path[len("/jobs/") : -len("/cancel")].strip("/")
                result = self.engine.cancel(job_id)
                self._send_json(result, status=HTTPStatus.OK)
                return

            if path.endswith("/trigger") and path.startswith("/jobs/"):
                job_id = path[len("/jobs/") : -len("/trigger")].strip("/")
                payload = self._read_json()
                result = self.engine.trigger(job_id, str(payload.get("action_type") or "reminder"))
                self._send_json(result, status=HTTPStatus.OK)
                return

            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except KeyError:
            self._send_json({"error": "Job not found."}, status=HTTPStatus.NOT_FOUND)
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
