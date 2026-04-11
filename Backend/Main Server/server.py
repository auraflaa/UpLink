from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

import requests
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from tinydb import Query, TinyDB
import google.generativeai as genai
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(os.path.dirname(BASE_DIR), "RAG Pipeline", ".env")
load_dotenv(dotenv_path=env_path)

if os.getenv("GOOGLE_API_KEY"):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
MAIN_SERVER_PORT = int(os.getenv("MAIN_SERVER_PORT", "8000"))
MAIN_SERVER_HOST = os.getenv("MAIN_SERVER_HOST", "0.0.0.0")
WORKSPACE_DB_PATH = os.path.join(BASE_DIR, "workspaces.json")
UI_RESOURCE_PATH = os.path.join(BASE_DIR, "ui_resources.json")

RAG_URL = os.getenv("RAG_URL", "http://127.0.0.1:6399").rstrip("/")
SCHEDULER_URL = os.getenv("SCHEDULER_URL", "http://127.0.0.1:8002").rstrip("/")
EVENT_HANDLER_URL = os.getenv("EVENT_HANDLER_URL", "http://127.0.0.1:8003").rstrip("/")
DOCUMENT_PARSER_URL = os.getenv("DOC_PARSER_URL", "http://127.0.0.1:8004").rstrip("/")


app = FastAPI(
    title="UpLink Main Server",
    description="Frontend-facing orchestration layer for analyzer and future product APIs.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestMeta(BaseModel):
    action: str
    ui_surface: str = "unknown"
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "anonymous"
    workspace_id: str | None = None
    source_kind: str | None = None


class ActionEnvelope(BaseModel):
    meta: RequestMeta
    payload: dict[str, Any] = Field(default_factory=dict)


workspace_db = TinyDB(WORKSPACE_DB_PATH)
WorkspaceQuery = Query()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonicalize_url(value: str | None) -> str:
    return str(value or "").strip().rstrip("/")


def _derive_source_kind(github_url: str, jira_url: str) -> str:
    if github_url and jira_url:
        return "dual"
    if github_url:
        return "github"
    if jira_url:
        return "jira"
    return "unknown"


def _safe_collection_name(user_id: str, github_url: str, jira_url: str) -> str:
    fingerprint = hashlib.sha1(
        f"{user_id}|{github_url}|{jira_url}".encode("utf-8")
    ).hexdigest()[:16]
    base = re.sub(r"[^a-zA-Z0-9_]+", "_", user_id or "anonymous").strip("_") or "anonymous"
    return f"workspace_{base}_{fingerprint}"


def _load_ui_resources() -> dict[str, Any]:
    fallback = {
        "home": {
            "welcome_title": "Welcome back",
            "welcome_subtitle": "Here is a live snapshot of your backend activity.",
            "empty_recent_projects_title": "No recent workspaces yet",
            "empty_recent_projects_body": "Connect a GitHub repository or Jira workspace to begin.",
            "recent_projects_button_label": "Refresh",
            "modules": {},
        },
        "analyzer": {
            "intro_title": "Link your workspace",
            "intro_subtitle": "Paste a GitHub repository or Jira workspace link below to begin live analysis.",
            "assistant_name": "Project Analyser",
            "assistant_tagline": "AI Code and Task Assistant",
            "visualizer_title": "Dynamic Visualiser",
            "visualizer_subtitle": "Real-time project architecture flow",
            "visualizer_caption": "Link a repository or board to generate a live architecture graph.",
            "cards": [],
            "copy": {
                "default_greeting": "Hello! I am your project assistant.",
                "linked_prefix": "I am ready to work with",
                "linked_suffix": "What would you like me to do?",
                "fallback_waiting": "Workspace analysis is still warming up.",
            },
        },
        "events": {
            "title": "Events and Momentum",
            "subtitle": "Track your scheduler activity.",
            "empty_state_title": "No scheduled events yet",
            "empty_state_body": "Add an event to begin.",
            "momentum_title": "Momentum Score",
            "momentum_default_body": "Momentum is based on live reminders.",
            "add_button_label": "Add Custom Event",
        },
    }
    try:
        with open(UI_RESOURCE_PATH, "r", encoding="utf-8") as resource_file:
            loaded = json.load(resource_file)
        if isinstance(loaded, dict):
            return loaded
    except (OSError, json.JSONDecodeError):
        pass
    return fallback


def _parse_iso_datetime(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _relative_time(value: datetime | None) -> str:
    if value is None:
        return "Unknown"

    now = datetime.now(timezone.utc)
    delta_seconds = int((value.astimezone(timezone.utc) - now).total_seconds())
    future = delta_seconds > 0
    seconds = abs(delta_seconds)

    if seconds < 60:
        return "In under a minute" if future else "Just now"

    minutes = seconds // 60
    if minutes < 60:
        return f"In {minutes} min" if future else f"{minutes} min ago"

    hours = minutes // 60
    if hours < 24:
        return f"In {hours} hr" if future else f"{hours} hr ago"

    days = hours // 24
    if days < 7:
        if future:
            return f"In {days} day" if days == 1 else f"In {days} days"
        return f"{days} day ago" if days == 1 else f"{days} days ago"

    weeks = max(1, days // 7)
    return f"In {weeks} wk" if future else f"{weeks} wk ago"


def _title_case_status(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "Unknown"
    return raw.replace("_", " ").replace("-", " ").title()


def _load_user_workspaces(user_id: str) -> list[dict[str, Any]]:
    records = workspace_db.all()
    normalized_user_id = str(user_id or "").strip()
    if normalized_user_id and normalized_user_id != "anonymous":
        matched = [record for record in records if str(record.get("user_id") or "") == normalized_user_id]
        if matched:
            return matched
    return records


def _fetch_scheduler_jobs() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        response = requests.get(f"{SCHEDULER_URL}/jobs", timeout=5)
        response.raise_for_status()
        payload = response.json()
        jobs = payload.get("jobs", [])
        return jobs if isinstance(jobs, list) else [], []
    except requests.RequestException as exc:
        return [], [{"message": str(exc), "type": "scheduler_jobs"}]


def _workspace_display_name(record: dict[str, Any]) -> str:
    github_url = _canonicalize_url(record.get("github_url"))
    jira_url = _canonicalize_url(record.get("jira_url"))
    github_name = ""
    jira_name = ""

    if github_url:
        path_bits = [bit for bit in urlparse(github_url).path.split("/") if bit]
        if len(path_bits) >= 2:
            github_name = f"{path_bits[0]}/{path_bits[1]}"
        elif path_bits:
            github_name = path_bits[-1]

    if jira_url:
        parsed = urlparse(jira_url)
        path_bits = [bit for bit in parsed.path.split("/") if bit]
        jira_name = path_bits[-1] if path_bits else parsed.netloc.split(".")[0]

    if github_name and jira_name:
        return f"{github_name} + {jira_name}"
    if github_name:
        return github_name
    if jira_name:
        return jira_name
    return record.get("workspace_id", "workspace")


def _workspace_source_label(record: dict[str, Any]) -> str:
    source_kind = str(record.get("source_kind") or "").strip().lower()
    if source_kind == "dual":
        return "GitHub + Jira"
    if source_kind == "github":
        return "GitHub"
    if source_kind == "jira":
        return "Jira"
    return "Workspace"


def _build_activity_series(workspaces: list[dict[str, Any]], jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    today = datetime.now(timezone.utc).date()
    buckets: list[dict[str, Any]] = []
    raw_counts: list[int] = []

    for index in range(6, -1, -1):
        bucket_date = today - timedelta(days=index)
        count = 0
        for record in workspaces:
            updated_at = _parse_iso_datetime(record.get("updated_at") or record.get("created_at"))
            if updated_at and updated_at.astimezone(timezone.utc).date() == bucket_date:
                count += 1
        for job in jobs:
            created_at = _parse_iso_datetime(job.get("created_at") or job.get("execute_at"))
            if created_at and created_at.astimezone(timezone.utc).date() == bucket_date:
                count += 1
        raw_counts.append(count)
        buckets.append(
            {
                "day": bucket_date.strftime("%a"),
                "count": count,
            }
        )

    max_count = max(raw_counts) if raw_counts else 0
    for bucket in buckets:
        count = int(bucket["count"])
        if max_count == 0 or count == 0:
            bucket["value"] = 0
        else:
            bucket["value"] = max(12, int((count / max_count) * 100))
    return buckets


def _build_dashboard_stats(workspaces: list[dict[str, Any]], jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    github_urls = {
        _canonicalize_url(record.get("github_url"))
        for record in workspaces
        if _canonicalize_url(record.get("github_url"))
    }
    jira_urls = {
        _canonicalize_url(record.get("jira_url"))
        for record in workspaces
        if _canonicalize_url(record.get("jira_url"))
    }
    active_workspaces = [
        record
        for record in workspaces
        if str(record.get("status") or "").strip().lower() in {"accepted", "indexing", "ready", "partial"}
    ]
    ready_workspaces = [
        record
        for record in workspaces
        if str(record.get("status") or "").strip().lower() in {"ready", "partial"}
    ]

    now = datetime.now(timezone.utc)
    upcoming_jobs = []
    for job in jobs:
        execute_at = _parse_iso_datetime(job.get("execute_at"))
        if execute_at and execute_at >= now and str(job.get("status") or "").strip().lower() != "cancelled":
            upcoming_jobs.append(job)

    next_due = min(
        (_parse_iso_datetime(job.get("execute_at")) for job in upcoming_jobs),
        default=None,
    )
    growth_score = min(
        999,
        (len(ready_workspaces) * 140)
        + (len(upcoming_jobs) * 35)
        + (len(github_urls) * 25)
        + (len(jira_urls) * 20),
    )

    next_due_label = _relative_time(next_due) if next_due else "No reminders queued"

    return [
        {
            "label": "Growth Score",
            "value": str(growth_score),
            "trend": f"{len(ready_workspaces)} ready workspace(s)",
            "icon_key": "trending_up",
        },
        {
            "label": "Analyzed Repos",
            "value": str(len(github_urls)),
            "trend": f"{len(active_workspaces)} active workspace(s)",
            "icon_key": "github",
        },
        {
            "label": "Linked Workspaces",
            "value": str(len(workspaces)),
            "trend": f"{len(jira_urls)} Jira source(s)",
            "icon_key": "file_text",
        },
        {
            "label": "Upcoming Deadlines",
            "value": str(len(upcoming_jobs)),
            "trend": next_due_label,
            "icon_key": "calendar",
        },
    ]


def _build_recent_projects(workspaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_workspaces = sorted(
        workspaces,
        key=lambda record: _parse_iso_datetime(record.get("updated_at") or record.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    results = []
    for record in sorted_workspaces[:3]:
        updated_at = _parse_iso_datetime(record.get("updated_at") or record.get("created_at"))
        results.append(
            {
                "name": _workspace_display_name(record),
                "tech": _workspace_source_label(record),
                "status": _title_case_status(record.get("status") or "accepted"),
                "time": _relative_time(updated_at),
            }
        )
    return results


def _job_color_key(job: dict[str, Any]) -> str:
    metadata = job.get("metadata") or {}
    explicit = str(metadata.get("color") or "").strip().lower()
    if explicit in {"purple", "blue", "emerald", "amber", "slate"}:
        return explicit

    kind = str(job.get("kind") or metadata.get("type") or "").strip().lower()
    if "hackathon" in kind:
        return "purple"
    if "conference" in kind:
        return "blue"
    if "deadline" in kind or kind == "task":
        return "amber"
    if kind == "event":
        return "emerald"
    return "slate"


def _job_status(job: dict[str, Any], execute_at: datetime | None) -> str:
    raw_status = str(job.get("status") or "").strip().lower()
    if raw_status and raw_status != "scheduled":
        return _title_case_status(raw_status)
    if execute_at is None:
        return "Scheduled"
    now = datetime.now(timezone.utc)
    if execute_at <= now:
        return "Due now"
    if execute_at <= now + timedelta(days=1):
        return "Within 24 hours"
    if execute_at <= now + timedelta(days=7):
        return "This week"
    return "Upcoming"


def _build_momentum_card(jobs: list[dict[str, Any]], resources: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    upcoming = 0
    soon = 0
    platforms: set[str] = set()
    for job in jobs:
        execute_at = _parse_iso_datetime(job.get("execute_at"))
        status = str(job.get("status") or "").strip().lower()
        if status == "cancelled":
            continue
        if execute_at and execute_at >= now:
            upcoming += 1
            if execute_at <= now + timedelta(days=7):
                soon += 1
        platform = str((job.get("metadata") or {}).get("platform") or "").strip().lower()
        if platform:
            platforms.add(platform)

    score = min(100, (upcoming * 18) + (soon * 10) + (len(platforms) * 8))
    body = resources.get("events", {}).get("momentum_default_body", "")
    if upcoming:
        body = f"{upcoming} reminder(s) are queued, and {soon} land within the next 7 days."

    return {
        "title": resources.get("events", {}).get("momentum_title", "Momentum Score"),
        "score": score,
        "max_score": 100,
        "body": body,
    }


def _build_events_summary(jobs: list[dict[str, Any]], resources: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    formatted_events: list[dict[str, Any]] = []
    sortable_jobs = []
    for job in jobs:
        execute_at = _parse_iso_datetime(job.get("execute_at"))
        status = str(job.get("status") or "").strip().lower()
        if status == "cancelled":
            continue
        sortable_jobs.append((execute_at or now, job))

    for execute_at, job in sorted(sortable_jobs, key=lambda item: item[0]):
        metadata = job.get("metadata") or {}
        formatted_events.append(
            {
                "id": str(job.get("job_id") or ""),
                "title": str(job.get("title") or "Untitled event"),
                "date": execute_at.astimezone().strftime("%b %d, %Y") if execute_at else "TBD",
                "time": execute_at.astimezone().strftime("%I:%M %p") if execute_at else "TBD",
                "location": str(metadata.get("location") or "Online"),
                "type": str(metadata.get("type") or job.get("kind") or "Event"),
                "status": _job_status(job, execute_at),
                "color": _job_color_key(job),
                "url": str(
                    metadata.get("resource_url")
                    or metadata.get("event_url")
                    or metadata.get("registration_url")
                    or ""
                ).strip(),
            }
        )

    upcoming_count = sum(
        1
        for job in jobs
        if (
            _parse_iso_datetime(job.get("execute_at"))
            and _parse_iso_datetime(job.get("execute_at")) >= now
            and str(job.get("status") or "").strip().lower() != "cancelled"
        )
    )
    next_due = min(
        (
            _parse_iso_datetime(job.get("execute_at"))
            for job in jobs
            if _parse_iso_datetime(job.get("execute_at"))
            and str(job.get("status") or "").strip().lower() != "cancelled"
        ),
        default=None,
    )

    return {
        "header": {
            "title": resources.get("events", {}).get("title", "Events and Momentum"),
            "subtitle": resources.get("events", {}).get("subtitle", ""),
            "add_button_label": resources.get("events", {}).get("add_button_label", "Add Custom Event"),
        },
        "events": formatted_events,
        "empty_state": {
            "title": resources.get("events", {}).get("empty_state_title", "No scheduled events yet"),
            "body": resources.get("events", {}).get("empty_state_body", ""),
        },
        "summary": {
            "total": len(formatted_events),
            "upcoming": upcoming_count,
            "next_due": _relative_time(next_due) if next_due else "No reminders queued",
        },
        "momentum": _build_momentum_card(jobs, resources),
    }


def _build_ui_bootstrap(meta: RequestMeta) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    resources = _load_ui_resources()
    workspaces = _load_user_workspaces(meta.user_id)
    jobs, job_errors = _fetch_scheduler_jobs()
    home_resources = resources.get("home", {})
    user_label = "Builder"
    if str(meta.user_id or "").strip() and str(meta.user_id or "").strip().lower() != "anonymous":
        user_label = str(meta.user_id).strip()

    home_payload = {
        "welcome": {
            "title": f"{home_resources.get('welcome_title', 'Welcome back')}, {user_label}",
            "subtitle": home_resources.get("welcome_subtitle", ""),
        },
        "stats": _build_dashboard_stats(workspaces, jobs),
        "activity": _build_activity_series(workspaces, jobs),
        "recent_projects": _build_recent_projects(workspaces),
        "empty_state": {
            "title": home_resources.get("empty_recent_projects_title", "No recent workspaces yet"),
            "body": home_resources.get("empty_recent_projects_body", ""),
            "button_label": home_resources.get("recent_projects_button_label", "Refresh"),
        },
        "modules": home_resources.get("modules", {}),
    }

    analyzer_payload = resources.get("analyzer", {})
    events_overview = _build_events_summary(jobs, resources)
    status = "partial" if job_errors else "ready"

    return (
        {
            "home": home_payload,
            "analyzer": analyzer_payload,
            "events_overview": events_overview,
        },
        job_errors,
        status,
    )


def _response(
    meta: RequestMeta,
    *,
    status: str,
    data: dict[str, Any] | None = None,
    errors: list[dict[str, Any]] | None = None,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    return {
        "meta": {
            "action": meta.action,
            "status": status,
            "request_id": meta.request_id,
            "workspace_id": workspace_id or meta.workspace_id,
        },
        "data": data or {},
        "errors": errors or [],
    }


def _service_probe(service_name: str, url: str) -> dict[str, Any]:
    try:
        response = requests.get(url, timeout=3)
        payload = {}
        try:
            payload = response.json()
        except Exception:
            payload = {"raw": response.text[:200]}
        return {
            "service": service_name,
            "status": "online" if response.ok else "degraded",
            "http_status": response.status_code,
            "url": url,
            "details": payload,
        }
    except requests.RequestException as exc:
        return {
            "service": service_name,
            "status": "offline",
            "url": url,
            "reason": str(exc),
        }


def _load_workspace(workspace_id: str) -> dict[str, Any] | None:
    return workspace_db.get(WorkspaceQuery.workspace_id == workspace_id)


def _get_or_create_workspace(meta: RequestMeta, payload: dict[str, Any]) -> dict[str, Any]:
    github_url = _canonicalize_url(payload.get("github_url"))
    jira_url = _canonicalize_url(payload.get("jira_url"))

    if meta.workspace_id:
        existing = _load_workspace(meta.workspace_id)
        if existing:
            if not github_url:
                github_url = _canonicalize_url(existing.get("github_url"))
            if not jira_url:
                jira_url = _canonicalize_url(existing.get("jira_url"))
            source_kind = _derive_source_kind(github_url, jira_url)
            updated = {
                **existing,
                "github_url": github_url,
                "jira_url": jira_url,
                "source_kind": source_kind,
                "updated_at": _now_iso(),
                "last_request_id": meta.request_id,
                "last_action": meta.action,
                "user_id": meta.user_id or existing.get("user_id") or "anonymous",
            }
            workspace_db.update(updated, WorkspaceQuery.workspace_id == meta.workspace_id)
            return updated

    source_kind = _derive_source_kind(github_url, jira_url)
    if source_kind == "unknown":
        raise ValueError("At least one of github_url or jira_url is required.")

    existing = workspace_db.get(
        (WorkspaceQuery.user_id == meta.user_id)
        & (WorkspaceQuery.github_url == github_url)
        & (WorkspaceQuery.jira_url == jira_url)
    )
    if existing:
        updated = {
            **existing,
            "updated_at": _now_iso(),
            "last_request_id": meta.request_id,
            "last_action": meta.action,
        }
        workspace_db.update(updated, WorkspaceQuery.workspace_id == existing["workspace_id"])
        return updated

    workspace_id = str(uuid.uuid4())
    record = {
        "workspace_id": workspace_id,
        "user_id": meta.user_id or "anonymous",
        "github_url": github_url,
        "jira_url": jira_url,
        "source_kind": source_kind,
        "collection_name": _safe_collection_name(meta.user_id, github_url, jira_url),
        "status": "accepted",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "last_request_id": meta.request_id,
        "last_action": meta.action,
    }
    workspace_db.insert(record)
    return record


def _update_workspace_status(workspace_id: str, status: str) -> None:
    workspace_db.update(
        {
            "status": status,
            "updated_at": _now_iso(),
        },
        WorkspaceQuery.workspace_id == workspace_id,
    )


def _rag_post(path: str, payload: dict[str, Any], timeout: int = 45) -> dict[str, Any]:
    response = requests.post(f"{RAG_URL}{path}", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _rag_get(path: str, params: dict[str, Any], timeout: int = 15) -> dict[str, Any]:
    response = requests.get(f"{RAG_URL}{path}", params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _build_source_status(workspace: dict[str, Any]) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    sources: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    ready_count = 0
    present_count = 0

    for kind, url_key in (("github", "github_url"), ("jira", "jira_url")):
        source_url = _canonicalize_url(workspace.get(url_key))
        if not source_url:
            continue
        present_count += 1

        try:
            payload = _rag_get(
                "/status",
                {
                    "source_url": source_url,
                    "collection_name": workspace["collection_name"],
                },
            )
            indexed = bool(payload.get("indexed"))
            source_status = "ready" if indexed else "indexing"
            if indexed:
                ready_count += 1
            sources.append(
                {
                    "kind": kind,
                    "url": source_url,
                    "status": source_status,
                    "indexed": indexed,
                    "collection_name": payload.get("collection", workspace["collection_name"]),
                    "telemetry": payload.get("telemetry", {}),
                }
            )
        except requests.RequestException as exc:
            errors.append({"kind": kind, "url": source_url, "message": str(exc)})
            sources.append(
                {
                    "kind": kind,
                    "url": source_url,
                    "status": "failed",
                    "indexed": False,
                }
            )

    if present_count == 0:
        overall = "failed"
    elif ready_count == present_count:
        overall = "ready"
    elif ready_count > 0:
        overall = "partial"
    elif errors:
        overall = "failed"
    else:
        overall = "indexing"

    _update_workspace_status(workspace["workspace_id"], overall)
    return sources, overall, errors


def _strip_markdown_label(raw: str | None) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    if len(text) >= 2 and text[0] in "[({" and text[-1] in "])}":
        return text[1:-1].strip().strip('"')
    if len(text) >= 4 and text.startswith("((") and text.endswith("))"):
        return text[2:-2].strip().strip('"')
    if len(text) >= 4 and text.startswith("[[") and text.endswith("]]"):
        return text[2:-2].strip().strip('"')
    return text.strip('"')


def _parse_node_token(token: str, source_group: str) -> dict[str, str] | None:
    cleaned = token.strip().rstrip(";")
    if not cleaned or cleaned.startswith("subgraph") or cleaned == "end":
        return None

    match = re.match(
        r"^(?P<id>[A-Za-z0-9_:\-]+)(?P<label>\[\[.*?\]\]|\(\(.*?\)\)|\[.*?\]|\(.*?\)|\{.*?\})?$",
        cleaned,
    )
    if not match:
        return None

    raw_id = match.group("id")
    raw_label = match.group("label")
    label = _strip_markdown_label(raw_label) or raw_id
    node_type = "component"
    if raw_label and raw_label.startswith("{"):
        node_type = "decision"
    elif raw_label and raw_label.startswith("("):
        node_type = "service"

    return {
        "id": f"{source_group}:{raw_id}",
        "label": label,
        "type": node_type,
        "group": source_group,
    }


def _parse_mermaid_to_graph(mermaid: str, source_group: str) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    pipe_edge_pattern = re.compile(r"^(?P<left>.+?)\s*-->\|(?P<label>.+?)\|\s*(?P<right>.+)$")
    text_edge_pattern = re.compile(r"^(?P<left>.+?)\s*--\s*(?P<label>.+?)\s*-->\s*(?P<right>.+)$")
    basic_edge_pattern = re.compile(r"^(?P<left>.+?)\s*(?:-->|-.->|==>)\s*(?P<right>.+)$")

    for raw_line in mermaid.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("graph ") or line.startswith("%%") or line.startswith("subgraph") or line == "end":
            continue

        edge_match = pipe_edge_pattern.match(line)
        edge_label = ""
        if not edge_match:
            edge_match = text_edge_pattern.match(line)
        if edge_match:
            edge_label = str(edge_match.groupdict().get("label") or "").strip()
        if not edge_match:
            edge_match = basic_edge_pattern.match(line)

        if edge_match:
            left_node = _parse_node_token(edge_match.group("left"), source_group)
            right_node = _parse_node_token(edge_match.group("right"), source_group)
            if not left_node or not right_node:
                continue
            nodes[left_node["id"]] = {**left_node, "data": {"source_group": source_group}}
            nodes[right_node["id"]] = {**right_node, "data": {"source_group": source_group}}
            edges.append(
                {
                    "id": f"{left_node['id']}->{right_node['id']}:{len(edges)}",
                    "source": left_node["id"],
                    "target": right_node["id"],
                    "label": edge_label,
                    "type": "flow",
                    "data": {"source_group": source_group},
                }
            )
            continue

        node = _parse_node_token(line, source_group)
        if node:
            nodes[node["id"]] = {**node, "data": {"source_group": source_group}}

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "layout": {"algorithm": "mermaid_flowchart", "direction": "TD"},
    }


def _fallback_graph(workspace: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = []
    edges = []
    if workspace.get("github_url"):
        nodes.append(
            {
                "id": "github:source",
                "label": "GitHub Source",
                "type": "source",
                "group": "github",
                "data": {"url": workspace["github_url"]},
            }
        )
    if workspace.get("jira_url"):
        nodes.append(
            {
                "id": "jira:source",
                "label": "Jira Source",
                "type": "source",
                "group": "jira",
                "data": {"url": workspace["jira_url"]},
            }
        )
    nodes.append(
        {
            "id": "workspace:analysis",
            "label": "Workspace Analysis",
            "type": "analysis",
            "group": "workspace",
            "data": {"workspace_id": workspace["workspace_id"]},
        }
    )
    for node in nodes:
        if node["id"] != "workspace:analysis":
            edges.append(
                {
                    "id": f"{node['id']}->workspace:analysis",
                    "source": node["id"],
                    "target": "workspace:analysis",
                    "label": "feeds",
                    "type": "flow",
                    "data": {"source_group": node["group"]},
                }
            )
    return {
        "nodes": nodes,
        "edges": edges,
        "layout": {"algorithm": "fallback", "direction": "TD"},
        "source_states": sources,
    }


def _merge_graphs(graphs: list[dict[str, Any]], workspace: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    merged_nodes: dict[str, dict[str, Any]] = {}
    merged_edges: list[dict[str, Any]] = []

    for graph in graphs:
        for node in graph.get("nodes", []):
            merged_nodes[node["id"]] = node
        merged_edges.extend(graph.get("edges", []))

    if not merged_nodes:
        return _fallback_graph(workspace, sources)

    return {
        "nodes": list(merged_nodes.values()),
        "edges": merged_edges,
        "layout": {"algorithm": "merged_flowchart", "direction": "TD"},
        "source_states": sources,
    }


def _split_markdown_sections(markdown_text: str) -> dict[str, Any]:
    sections = {
        "title": "Workspace Analysis",
        "summary_markdown": "",
        "architecture_markdown": "",
        "github_markdown": "",
        "jira_markdown": "",
        "risks": "",
        "recommendations": "",
    }

    title_match = re.search(r"^#\s+(.+)$", markdown_text, flags=re.MULTILINE)
    if title_match:
        sections["title"] = title_match.group(1).strip()

    heading_map = {
        "summary": "summary_markdown",
        "architecture": "architecture_markdown",
        "github": "github_markdown",
        "jira": "jira_markdown",
        "risks": "risks",
        "recommendations": "recommendations",
    }
    parts = re.split(r"^##\s+", markdown_text, flags=re.MULTILINE)
    for part in parts[1:]:
        lines = part.splitlines()
        if not lines:
            continue
        heading = lines[0].strip().lower()
        body = "\n".join(lines[1:]).strip()
        key = heading_map.get(heading)
        if key:
            sections[key] = body

    return sections


def _fallback_content(workspace: dict[str, Any], sources: list[dict[str, Any]], reason: str = "") -> dict[str, Any]:
    github_summary = workspace.get("github_url") or "Not provided."
    jira_summary = workspace.get("jira_url") or "Not provided."
    return {
        "title": "Workspace Analysis",
        "summary_markdown": "Indexed sources are still being prepared or the content generator is unavailable.",
        "architecture_markdown": "Visualization data is limited, so UpLink returned a compatibility summary instead of a full narrative.",
        "github_markdown": f"GitHub Source: {github_summary}",
        "jira_markdown": f"Jira Source: {jira_summary}",
        "risks": reason or "Analysis is incomplete, so downstream insights may be partial.",
        "recommendations": "Retry after the workspace status reaches `ready` or inspect individual source readiness.",
        "source_states": sources,
    }


def _generate_visualization_content(
    workspace: dict[str, Any],
    sources: list[dict[str, Any]],
    user_id: str,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    ready_sources = [source for source in sources if source.get("status") == "ready"]
    if not ready_sources:
        return _fallback_content(workspace, sources), {}, []

    source_lines = []
    for source in ready_sources:
        source_lines.append(f"- {source['kind'].title()}: {source['url']}")

    prompt = (
        "You are generating frontend-ready markdown for the UpLink analyzer. "
        "Use only the indexed workspace knowledge already present in the collection. "
        "Return markdown with exactly these headings:\n"
        "# Title\n"
        "## Summary\n"
        "## Architecture\n"
        "## GitHub\n"
        "## Jira\n"
        "## Risks\n"
        "## Recommendations\n\n"
        "Keep each section concise, technical, and directly grounded in the indexed sources.\n"
        "If a source type is missing, write 'Not provided.'\n\n"
        "Workspace sources:\n"
        f"{chr(10).join(source_lines)}"
    )

    try:
        rag_payload = _rag_post(
            "/chat",
            {
                "query": prompt,
                "user_id": user_id or workspace.get("user_id") or "anonymous",
                "session_id": f"main-server:{workspace['workspace_id']}:visualization",
                "collection_name": workspace["collection_name"],
            },
            timeout=60,
        )
        answer = str(rag_payload.get("answer") or "").strip()
        if not answer:
            return (
                _fallback_content(workspace, sources, reason="RAG returned an empty visualization narrative."),
                rag_payload.get("telemetry", {}),
                [],
            )
        return _split_markdown_sections(answer), rag_payload.get("telemetry", {}), []
    except requests.RequestException as exc:
        return (
            _fallback_content(workspace, sources, reason=str(exc)),
            {},
            [{"message": str(exc), "type": "content_generation"}],
        )


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "service": "main_server",
        "status": "healthy",
        "port": MAIN_SERVER_PORT,
        "workspace_db_path": WORKSPACE_DB_PATH,
    }


@app.get("/dependencies")
def dependencies() -> dict[str, Any]:
    return {
        "service": "main_server",
        "dependencies": {
            "rag_pipeline": _service_probe("rag_pipeline", f"{RAG_URL}/health"),
            "scheduler": _service_probe("scheduler", f"{SCHEDULER_URL}/health"),
            "event_handler": _service_probe("event_handler", f"{EVENT_HANDLER_URL}/health"),
            "document_parser": _service_probe("document_parser", f"{DOCUMENT_PARSER_URL}/status"),
        },
    }


@app.post("/api/main/v1/ui/bootstrap")
def ui_bootstrap(envelope: ActionEnvelope) -> dict[str, Any]:
    data, errors, status = _build_ui_bootstrap(envelope.meta)
    return _response(
        envelope.meta,
        status=status,
        data=data,
        errors=errors,
    )


@app.post("/api/main/v1/events/summary")
def events_summary(envelope: ActionEnvelope) -> dict[str, Any]:
    resources = _load_ui_resources()
    jobs, errors = _fetch_scheduler_jobs()
    data = _build_events_summary(jobs, resources)
    return _response(
        envelope.meta,
        status="partial" if errors else "ready",
        data=data,
        errors=errors,
    )


@app.post("/api/main/v1/workspaces/analyze")
def analyze_workspace(envelope: ActionEnvelope) -> dict[str, Any]:
    try:
        workspace = _get_or_create_workspace(envelope.meta, envelope.payload)
    except ValueError as exc:
        return _response(
            envelope.meta,
            status="failed",
            data={},
            errors=[{"message": str(exc), "type": "validation"}],
        )

    try:
        rag_response = _rag_post(
            "/analyze/dual",
            {
                "github_url": workspace.get("github_url") or None,
                "jira_url": workspace.get("jira_url") or None,
                "collection_name": workspace["collection_name"],
            },
        )
        status = str(rag_response.get("status") or "accepted")
        _update_workspace_status(workspace["workspace_id"], status)
        sources, _, _ = _build_source_status(_load_workspace(workspace["workspace_id"]) or workspace)
        return _response(
            envelope.meta,
            status="accepted" if status == "accepted" else status,
            workspace_id=workspace["workspace_id"],
            data={
                "workspace_id": workspace["workspace_id"],
                "source_kind": workspace["source_kind"],
                "collection_name": workspace["collection_name"],
                "sources": sources,
                "upstream": rag_response,
            },
        )
    except requests.RequestException as exc:
        _update_workspace_status(workspace["workspace_id"], "failed")
        return _response(
            envelope.meta,
            status="failed",
            workspace_id=workspace["workspace_id"],
            data={
                "workspace_id": workspace["workspace_id"],
                "source_kind": workspace["source_kind"],
                "collection_name": workspace["collection_name"],
            },
            errors=[{"message": str(exc), "type": "rag_request"}],
        )


@app.post("/api/main/v1/workspaces/status")
def workspace_status(envelope: ActionEnvelope) -> dict[str, Any]:
    workspace_id = envelope.meta.workspace_id or str(envelope.payload.get("workspace_id") or "").strip()
    workspace = _load_workspace(workspace_id) if workspace_id else None
    if not workspace:
        return _response(
            envelope.meta,
            status="failed",
            errors=[{"message": "workspace_id is missing or unknown.", "type": "validation"}],
        )

    sources, overall_status, errors = _build_source_status(workspace)
    return _response(
        envelope.meta,
        status=overall_status,
        workspace_id=workspace["workspace_id"],
        data={
            "workspace_id": workspace["workspace_id"],
            "source_kind": workspace["source_kind"],
            "collection_name": workspace["collection_name"],
            "sources": sources,
        },
        errors=errors,
    )


@app.post("/api/main/v1/workspaces/visualization")
def workspace_visualization(envelope: ActionEnvelope) -> dict[str, Any]:
    workspace_id = envelope.meta.workspace_id or str(envelope.payload.get("workspace_id") or "").strip()
    workspace = _load_workspace(workspace_id) if workspace_id else None
    if not workspace:
        return _response(
            envelope.meta,
            status="failed",
            errors=[{"message": "workspace_id is missing or unknown.", "type": "validation"}],
        )

    sources, overall_status, status_errors = _build_source_status(workspace)
    ready_sources = [source for source in sources if source.get("status") == "ready"]
    if not ready_sources:
        return _response(
            envelope.meta,
            status="not_ready" if overall_status == "indexing" else overall_status,
            workspace_id=workspace["workspace_id"],
            data={
                "workspace_id": workspace["workspace_id"],
                "status": "not_ready" if overall_status == "indexing" else overall_status,
                "sources": sources,
                "graph": _fallback_graph(workspace, sources),
                "content": _fallback_content(workspace, sources),
                "telemetry": {},
                "raw": {"mermaid": {}},
            },
            errors=status_errors,
        )

    graphs: list[dict[str, Any]] = []
    raw_mermaid: dict[str, str] = {}
    visualization_errors = list(status_errors)
    source_telemetry: dict[str, Any] = {}
    for source in ready_sources:
        try:
            viz_payload = _rag_post(
                "/viz",
                {
                    "source_url": source["url"],
                    "collection_name": workspace["collection_name"],
                },
                timeout=45,
            )
            mermaid = str(viz_payload.get("mermaid") or "").strip()
            raw_mermaid[source["kind"]] = mermaid
            graphs.append(_parse_mermaid_to_graph(mermaid, source["kind"]))
            source_telemetry[source["kind"]] = {
                "source_files": viz_payload.get("source_files"),
            }
        except requests.RequestException as exc:
            visualization_errors.append(
                {"message": str(exc), "type": "visualization_generation", "source_kind": source["kind"]}
            )

    content, content_telemetry, content_errors = _generate_visualization_content(
        workspace,
        sources,
        envelope.meta.user_id,
    )
    visualization_errors.extend(content_errors)

    final_status = overall_status
    if visualization_errors and graphs:
        final_status = "partial"
    elif visualization_errors and not graphs:
        final_status = "failed"
    elif overall_status == "indexing":
        final_status = "not_ready"

    graph_payload = _merge_graphs(graphs, workspace, sources)
    return _response(
        envelope.meta,
        status=final_status,
        workspace_id=workspace["workspace_id"],
        data={
            "workspace_id": workspace["workspace_id"],
            "status": final_status,
            "sources": sources,
            "graph": graph_payload,
            "content": content,
            "telemetry": {
                "visualization": source_telemetry,
                "content": content_telemetry,
            },
            "raw": {"mermaid": raw_mermaid},
        },
        errors=visualization_errors,
    )


@app.post("/api/main/v1/workspaces/chat")
def workspace_chat(envelope: ActionEnvelope) -> dict[str, Any]:
    workspace_id = str(envelope.meta.workspace_id or envelope.payload.get("workspace_id") or "").strip()
    
    if workspace_id == "default_chat":
        workspace = {"workspace_id": "default_chat", "collection_name": "anonymous_default", "user_id": envelope.meta.user_id}
    else:
        workspace = _load_workspace(workspace_id) if workspace_id else None
        if not workspace:
            return _response(
                envelope.meta,
                status="failed",
                errors=[{"message": "workspace_id is missing or unknown.", "type": "validation"}],
            )

    query = str(envelope.payload.get("query") or "").strip()
    if not query:
        return _response(
            envelope.meta,
            status="failed",
            workspace_id=workspace["workspace_id"],
            errors=[{"message": "payload.query is required.", "type": "validation"}],
        )

    # RAG Threshold logic defined in Main Server
    skip_rag = False
    if workspace["workspace_id"] == "default_chat":
        skip_rag = True
    else:
        q_lower = query.lower()
        # Heuristic threshold: if query is extremely short or a standard greeting, bypass RAG
        greetings = ["hey", "hello", "hi", "help", "who are you", "what can you do", "good morning", "good evening"]
        if len(query.split()) < 4 or any(q_lower.startswith(g) for g in greetings):
            skip_rag = True

    if skip_rag and os.getenv("GOOGLE_API_KEY"):
        try:
            model_name = os.getenv("CHAT_MODEL") or os.getenv("LLM_MODEL") or "gemini-1.5-pro"
            if model_name.startswith("models/") == False and not "gemma" in model_name:
                model_name = f"models/{model_name}"
            elif model_name.startswith("models/") == False:
                model_name = f"models/{model_name}"
            
            # Hotfix for open source Gemini models that are strict
            model_name = model_name.replace("models/models/", "models/")

            model = genai.GenerativeModel(model_name)
            prompt = (
                "You are an expert software engineering assistant integrated into the UpLink platform. "
                "Answer the user's question concisely.\n\n"
                f"User: {query}"
            )
            result = model.generate_content(prompt)
            return _response(
                envelope.meta,
                status="ready",
                workspace_id=workspace["workspace_id"],
                data={
                    "workspace_id": workspace["workspace_id"],
                    "answer": result.text,
                    "sources": [],
                    "telemetry": {"source": "main_server_native_llm"},
                    "long_term_hits": 0,
                },
            )
        except Exception as e:
            print(f"[!] Native LLM Error in Main Server: {e}")
            pass

    try:
        rag_payload = _rag_post(
            "/chat",
            {
                "query": query,
                "user_id": envelope.meta.user_id or workspace.get("user_id") or "anonymous",
                "session_id": str(
                    envelope.payload.get("session_id")
                    or f"main-server:{workspace['workspace_id']}:chat"
                ),
                "collection_name": workspace["collection_name"],
                "skip_rag": skip_rag,
            },
            timeout=60,
        )
        return _response(
            envelope.meta,
            status="ready",
            workspace_id=workspace["workspace_id"],
            data={
                "workspace_id": workspace["workspace_id"],
                "answer": rag_payload.get("answer", ""),
                "sources": rag_payload.get("sources", []),
                "telemetry": rag_payload.get("telemetry", {}),
                "long_term_hits": rag_payload.get("long_term_hits", 0),
            },
        )
    except requests.RequestException as exc:
        return _response(
            envelope.meta,
            status="failed",
            workspace_id=workspace["workspace_id"],
            errors=[{"message": str(exc), "type": "rag_chat"}],
        )


if __name__ == "__main__":
    uvicorn.run(app, host=MAIN_SERVER_HOST, port=MAIN_SERVER_PORT)
