from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sqlite3
import ssl
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable
from urllib import error, parse, request
from zoneinfo import ZoneInfo


BASE_DIR = os.path.dirname(__file__)
DEFAULT_DB_PATH = os.getenv("SCRAPER_DB_PATH", os.path.join(BASE_DIR, "events.sqlite3"))
DEFAULT_EVENT_HANDLER_URL = os.getenv("EVENT_HANDLER_URL", "http://127.0.0.1:8003/events/ingest")
DEFAULT_SCAN_TIME = os.getenv("SCRAPER_SCAN_TIME", "08:00")
DEFAULT_TIMEZONE = os.getenv("SCRAPER_TIMEZONE", "Asia/Calcutta")
DEFAULT_MAX_EVENTS_PER_PLATFORM = int(os.getenv("SCRAPER_MAX_EVENTS_PER_PLATFORM", "12"))
DEFAULT_REQUEST_TIMEOUT_SECONDS = int(os.getenv("SCRAPER_REQUEST_TIMEOUT_SECONDS", "20"))
SCRAPER_USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
)


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


def _build_ssl_context() -> ssl.SSLContext:
    cafile = os.getenv("SCRAPER_CA_BUNDLE") or os.getenv("SSL_CERT_FILE")
    if cafile:
        return ssl.create_default_context(cafile=cafile)

    allow_insecure = str(os.getenv("SCRAPER_ALLOW_INSECURE_SSL") or "").strip().lower()
    if allow_insecure in {"1", "true", "yes"}:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    return ssl.create_default_context()


def _fetch_html(url: str, timeout: int = DEFAULT_REQUEST_TIMEOUT_SECONDS) -> str:
    req = request.Request(
        url=url,
        headers={
            "User-Agent": SCRAPER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
        },
        method="GET",
    )
    with request.urlopen(req, timeout=timeout, context=_build_ssl_context()) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _strip_tags(value: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    text = re.sub(r"(?is)<!--.*?-->", " ", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|section|article|li|ul|ol|h1|h2|h3|h4|h5|h6|tr)>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def _extract_text_lines(value: str) -> list[str]:
    stripped = _strip_tags(value)
    lines = []
    for raw_line in stripped.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if line:
            lines.append(line)
    return lines


def _extract_text_fragment(html_text: str, position: int, window: int = 2500) -> str:
    start = max(0, position - 300)
    end = min(len(html_text), position + window)
    return " ".join(_extract_text_lines(html_text[start:end]))


def _extract_links(html_text: str, base_url: str) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    anchor_pattern = re.compile(
        r'(?is)<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
    )
    for match in anchor_pattern.finditer(html_text):
        href_raw = html.unescape(match.group(1)).strip()
        href = parse.urljoin(base_url, href_raw)
        text = " ".join(_extract_text_lines(match.group(2)))
        links.append(
            {
                "href": href,
                "href_raw": href_raw,
                "text": text,
                "position": match.start(),
            }
        )
    return links


def _extract_meta_content(html_text: str, key: str) -> str:
    escaped_key = re.escape(key)
    patterns = [
        re.compile(
            rf'(?is)<meta\b[^>]*property=["\']{escaped_key}["\'][^>]*content=["\']([^"\']+)["\']'
        ),
        re.compile(
            rf'(?is)<meta\b[^>]*name=["\']{escaped_key}["\'][^>]*content=["\']([^"\']+)["\']'
        ),
        re.compile(
            rf'(?is)<meta\b[^>]*content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']{escaped_key}["\']'
        ),
    ]
    for pattern in patterns:
        match = pattern.search(html_text)
        if match:
            return html.unescape(match.group(1)).strip()
    return ""


def _slug_from_url(url: str) -> str:
    path = parse.urlparse(url).path.strip("/")
    return path.split("/")[-1] if path else hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _first_matching_line(lines: list[str], pattern: str, start_index: int = 0) -> tuple[int, str] | None:
    compiled = re.compile(pattern, re.IGNORECASE)
    for index in range(start_index, len(lines)):
        if compiled.search(lines[index]):
            return index, lines[index]
    return None


def _parse_date_text(
    value: str,
    *,
    default_hour: int = 9,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> datetime | None:
    text = " ".join(str(value or "").replace("(UTC)", "UTC").split())
    if not text:
        return None

    local_zone = ZoneInfo(timezone_name)
    simple_formats = [
        ("%Y-%m-%d", local_zone),
        ("%d/%m/%y", local_zone),
        ("%d/%m/%Y", local_zone),
        ("%d %b %Y", local_zone),
        ("%b %d %Y", local_zone),
    ]
    for date_format, zone in simple_formats:
        try:
            parsed = datetime.strptime(text, date_format)
            parsed = parsed.replace(hour=default_hour, minute=0, second=0, microsecond=0, tzinfo=zone)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue

    match = re.search(r"(\d{1,2} [A-Za-z]{3})'(\d{2}), (\d{1,2}:\d{2}) ([AP]M) IST", text)
    if match:
        normalized = f"{match.group(1)} 20{match.group(2)} {match.group(3)} {match.group(4)}"
        parsed = datetime.strptime(normalized, "%d %b %Y %I:%M %p")
        return parsed.replace(tzinfo=local_zone).astimezone(timezone.utc)

    match = re.search(r"([A-Za-z]{3} \d{1,2}, \d{4}, \d{1,2}:\d{2} [AP]M) UTC", text)
    if match:
        parsed = datetime.strptime(match.group(1), "%b %d, %Y, %I:%M %p")
        return parsed.replace(tzinfo=timezone.utc)

    match = re.search(r"(\d{1,2} [A-Za-z]{3} \d{4})", text)
    if match:
        parsed = datetime.strptime(match.group(1), "%d %b %Y")
        return parsed.replace(hour=default_hour, minute=0, second=0, microsecond=0, tzinfo=local_zone).astimezone(
            timezone.utc
        )

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(hour=default_hour, minute=0, second=0, microsecond=0, tzinfo=local_zone)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _iso_from_text(value: str) -> str | None:
    parsed = _parse_date_text(value)
    return _isoformat(parsed) if parsed else None


def _extract_title_from_lines(lines: list[str], blocked_patterns: list[str] | None = None) -> str:
    blockers = [re.compile(pattern, re.IGNORECASE) for pattern in blocked_patterns or []]
    for line in lines:
        if len(line) < 3:
            continue
        if any(pattern.search(line) for pattern in blockers):
            continue
        return line
    return ""


def _has_schedule_field(event: dict[str, Any]) -> bool:
    return any(
        _as_string(event.get(key))
        for key in ["deadline", "deadline_at", "registration_deadline", "start_at", "execute_at"]
    )


def detect_platform_from_url(event_url: str) -> str:
    host = parse.urlparse(event_url).netloc.lower()
    if "unstop.com" in host:
        return "unstop"
    if "devfolio.co" in host:
        return "devfolio"
    if "hackerearth.com" in host:
        return "hackerearth"
    if "reskilll.com" in host:
        return "reskilll"
    raise ValueError("Unsupported event platform URL.")


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
    listing_url = ""

    def fetch_html(self, url: str) -> str:
        return _fetch_html(url)

    def dedupe_links(self, links: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for link in links:
            href = _as_string(link.get("href"))
            if not href or href in seen:
                continue
            seen.add(href)
            deduped.append(link)
        return deduped

    def parse_event_link(self, event_url: str) -> dict[str, Any]:
        raise NotImplementedError

    def fetch_events(self) -> list[dict[str, Any]]:
        raise NotImplementedError


class UnstopScraper(BaseScraper):
    platform = "unstop"
    listing_url = "https://api.unstop.com/hackathons/"

    def parse_event_link(self, event_url: str) -> dict[str, Any]:
        detail_html = self.fetch_html(event_url)
        detail_lines = _extract_text_lines(detail_html)
        title = (
            _extract_meta_content(detail_html, "og:title")
            or _extract_meta_content(detail_html, "twitter:title")
            or _extract_title_from_lines(
                detail_lines,
                blocked_patterns=[
                    r"registrations?",
                    r"deadline",
                    r"overview",
                    r"stages and timelines",
                ],
            )
        )
        title = re.sub(r"\s*//\s*Unstop.*$", "", title).strip()
        description = (
            _extract_meta_content(detail_html, "description")
            or _extract_meta_content(detail_html, "og:description")
        )
        organizer = ""
        if title in detail_lines:
            title_index = detail_lines.index(title)
            if title_index + 1 < len(detail_lines):
                candidate = detail_lines[title_index + 1]
                if len(candidate) < 120:
                    organizer = candidate

        joined_text = " ".join(detail_lines)
        deadline_match = re.search(
            r"Registration Deadline\s+([A-Za-z0-9,' :]+(?:IST|UTC)?)",
            joined_text,
            re.IGNORECASE,
        )
        prize_match = re.search(
            r"Total Prize Worth\s+([A-Za-z0-9 ,./+-]+)",
            joined_text,
            re.IGNORECASE,
        )
        start_match = re.search(
            r"Starts? On\s+([A-Za-z0-9,' :]+(?:IST|UTC)?)",
            joined_text,
            re.IGNORECASE,
        )
        tags = [line.lstrip("#").strip() for line in detail_lines if line.startswith("#")]

        mode = ""
        lower_text = joined_text.lower()
        if "online round" in lower_text or re.search(r"\bonline\b", lower_text):
            mode = "online"
        elif re.search(r"\boffline\b", lower_text):
            mode = "offline"

        return {
            "title": title,
            "description": description,
            "platform": self.platform,
            "source_id": f"{self.platform}:{_slug_from_url(event_url)}",
            "event_url": event_url,
            "registration_url": event_url,
            "start_at": _iso_from_text(start_match.group(1)) if start_match else None,
            "deadline": _iso_from_text(deadline_match.group(1)) if deadline_match else None,
            "location": "",
            "mode": mode,
            "tags": tags,
            "organizer": organizer,
            "prize": prize_match.group(1).strip() if prize_match else "",
            "timezone": DEFAULT_TIMEZONE,
        }

    def fetch_events(self) -> list[dict[str, Any]]:
        listing_html = self.fetch_html(self.listing_url)
        links = self.dedupe_links(_extract_links(listing_html, self.listing_url))
        event_links = [
            link
            for link in links
            if "/hackathons/" in link["href"] and link["href"].rstrip("/") != self.listing_url.rstrip("/")
        ]

        events: list[dict[str, Any]] = []
        for link in event_links[:DEFAULT_MAX_EVENTS_PER_PLATFORM]:
            try:
                events.append(self.parse_event_link(link["href"]))
            except Exception:
                continue

        return events


class DevfolioScraper(BaseScraper):
    platform = "devfolio"
    listing_url = "https://devfolio.co/hackathons"

    def parse_event_link(self, event_url: str) -> dict[str, Any]:
        detail_html = self.fetch_html(event_url)
        detail_lines = _extract_text_lines(detail_html)
        title = (
            _extract_meta_content(detail_html, "og:title")
            or _extract_meta_content(detail_html, "twitter:title")
            or _extract_title_from_lines(detail_lines, blocked_patterns=[r"hackathon", r"theme", r"apply now"])
        )
        title = re.sub(r"\s*\|\s*Devfolio.*$", "", title).strip()
        description = (
            _extract_meta_content(detail_html, "description")
            or _extract_meta_content(detail_html, "og:description")
        )
        joined = " ".join(detail_lines)
        start_match = re.search(r"Starts?\s+(\d{2}/\d{2}/\d{2})", joined, re.IGNORECASE)
        open_match = re.search(r"Opens?\s+(\d{2}/\d{2}/\d{2})", joined, re.IGNORECASE)
        mode_match = re.search(r"\b(Online|Offline|Hybrid)\b", joined, re.IGNORECASE)
        organizer = ""
        theme_match = re.search(
            r"Theme\s+(.+?)(?:\+\d+\s+participating|\bOnline\b|\bOffline\b|\bHybrid\b|\bOpen\b|\bUpcoming\b|\bEnded\b|\bStarts?\b|\bOpens?\b)",
            joined,
            re.IGNORECASE,
        )
        tags = []
        if theme_match:
            tags = [
                token.strip(" ,")
                for token in re.split(r"\s{2,}|,", theme_match.group(1))
                if token.strip(" ,")
            ]

        return {
            "title": title,
            "description": description,
            "platform": self.platform,
            "source_id": f"{self.platform}:{_slug_from_url(event_url)}",
            "event_url": event_url,
            "registration_url": event_url,
            "start_at": _iso_from_text(start_match.group(1)) if start_match else None,
            "deadline": _iso_from_text(open_match.group(1)) if open_match else None,
            "location": "",
            "mode": mode_match.group(1).lower() if mode_match else "",
            "tags": tags,
            "organizer": organizer,
            "prize": "",
            "timezone": DEFAULT_TIMEZONE,
        }

    def fetch_events(self) -> list[dict[str, Any]]:
        listing_html = self.fetch_html(self.listing_url)
        links = self.dedupe_links(_extract_links(listing_html, self.listing_url))
        blocked_texts = {
            "all open hackathons",
            "apply now",
            "remind me",
            "see projects",
        }
        events: list[dict[str, Any]] = []

        for link in links:
            href = link["href"]
            if "devfolio.co" not in parse.urlparse(href).netloc:
                continue
            if href.rstrip("/") == self.listing_url.rstrip("/"):
                continue
            if not link["text"] or link["text"].strip().lower() in blocked_texts:
                continue

            snippet = _extract_text_fragment(listing_html, link["position"], window=2200)
            if re.search(r"\b(ended|past)\b", snippet, re.IGNORECASE):
                continue

            start_match = re.search(r"Starts?\s+(\d{2}/\d{2}/\d{2})", snippet, re.IGNORECASE)
            mode_match = re.search(r"\b(Online|Offline)\b", snippet, re.IGNORECASE)
            theme_match = re.search(
                r"Theme\s+(.+?)(?:\+\d+\s+participating|\bOnline\b|\bOffline\b|\bOpen\b|\bUpcoming\b|\bEnded\b|\bStarts?\b)",
                snippet,
                re.IGNORECASE,
            )

            tags = []
            if theme_match:
                tags = [
                    token.strip(" ,")
                    for token in re.split(r"\s{2,}|,", theme_match.group(1))
                    if token.strip(" ,")
                ]

            events.append(
                {
                    "title": link["text"],
                    "description": "",
                    "platform": self.platform,
                    "source_id": f"{self.platform}:{_slug_from_url(href)}",
                    "event_url": href,
                    "registration_url": href,
                    "start_at": _iso_from_text(start_match.group(1)) if start_match else None,
                    "location": "",
                    "mode": mode_match.group(1).lower() if mode_match else "",
                    "tags": tags,
                    "organizer": "",
                    "prize": "",
                    "timezone": DEFAULT_TIMEZONE,
                }
            )

            if len(events) >= DEFAULT_MAX_EVENTS_PER_PLATFORM:
                break

        return events


class HackerEarthScraper(BaseScraper):
    platform = "hackerearth"
    listing_url = "https://www.hackerearth.com/challenges/hackathon/"

    def parse_event_link(self, event_url: str) -> dict[str, Any]:
        detail_html = self.fetch_html(event_url)
        detail_lines = _extract_text_lines(detail_html)
        detail_text = " ".join(detail_lines)

        title = (
            _extract_meta_content(detail_html, "og:title")
            or _extract_meta_content(detail_html, "twitter:title")
        )
        title = re.sub(r"\s*\|\s*HackerEarth.*$", "", title).strip()

        description = (
            _extract_meta_content(detail_html, "description")
            or _extract_meta_content(detail_html, "og:description")
        )
        start_match = re.search(
            r"starts on:\s*([A-Za-z]{3} \d{1,2}, \d{4}, \d{1,2}:\d{2} [AP]M UTC)",
            detail_text,
            re.IGNORECASE,
        )
        end_match = re.search(
            r"ends on:\s*([A-Za-z]{3} \d{1,2}, \d{4}, \d{1,2}:\d{2} [AP]M UTC)",
            detail_text,
            re.IGNORECASE,
        )
        prize_match = re.search(r"Prizes?\s+([A-Za-z0-9 ,./+-]+?)\s+in prizes", detail_text, re.IGNORECASE)
        mode_match = re.search(r"\b(Online|Offline)\b", detail_text, re.IGNORECASE)

        tags: list[str] = []
        theme_index = _first_matching_line(detail_lines, r"^Themes?$")
        if theme_index:
            for line in detail_lines[theme_index[0] + 1 :]:
                if re.search(r"^Prizes?$", line, re.IGNORECASE):
                    break
                if len(line) > 2 and len(tags) < 5:
                    tags.append(line)

        return {
            "title": title,
            "description": description,
            "platform": self.platform,
            "source_id": f"{self.platform}:{_slug_from_url(event_url)}",
            "event_url": event_url,
            "registration_url": event_url,
            "start_at": _iso_from_text(start_match.group(1)) if start_match else None,
            "end_at": _iso_from_text(end_match.group(1)) if end_match else None,
            "location": "",
            "mode": mode_match.group(1).lower() if mode_match else "",
            "tags": tags,
            "organizer": "HackerEarth",
            "prize": prize_match.group(1).strip() if prize_match else "",
            "timezone": DEFAULT_TIMEZONE,
        }

    def fetch_events(self) -> list[dict[str, Any]]:
        listing_html = self.fetch_html(self.listing_url)
        links = self.dedupe_links(_extract_links(listing_html, self.listing_url))
        challenge_links = [
            link
            for link in links
            if "/challenges/hackathon/" in link["href"]
            and link["href"].rstrip("/") != self.listing_url.rstrip("/")
        ]

        events: list[dict[str, Any]] = []
        for link in challenge_links[:DEFAULT_MAX_EVENTS_PER_PLATFORM]:
            try:
                events.append(self.parse_event_link(link["href"]))
            except Exception:
                continue

        return events


class ReskilllScraper(BaseScraper):
    platform = "reskilll"
    listing_url = "https://www.reskilll.com/"

    def parse_event_link(self, event_url: str) -> dict[str, Any]:
        detail_html = self.fetch_html(event_url)
        detail_lines = _extract_text_lines(detail_html)
        detail_text = " ".join(detail_lines)
        title = (
            _extract_meta_content(detail_html, "og:title")
            or _extract_meta_content(detail_html, "twitter:title")
            or _extract_title_from_lines(detail_lines, blocked_patterns=[r"register", r"view details"])
        )
        description = (
            _extract_meta_content(detail_html, "description")
            or _extract_meta_content(detail_html, "og:description")
        )
        start_match = re.search(r"Start\s+(\d{4}-\d{2}-\d{2})", detail_text, re.IGNORECASE)
        end_match = re.search(r"End\s+(\d{4}-\d{2}-\d{2})", detail_text, re.IGNORECASE)
        mode_match = re.search(r"\b(online|offline|hybrid)\b", detail_text, re.IGNORECASE)

        return {
            "title": title,
            "description": description,
            "platform": self.platform,
            "source_id": f"{self.platform}:{_slug_from_url(event_url)}",
            "event_url": event_url,
            "registration_url": event_url,
            "start_at": _iso_from_text(start_match.group(1)) if start_match else None,
            "end_at": _iso_from_text(end_match.group(1)) if end_match else None,
            "location": "",
            "mode": mode_match.group(1).lower() if mode_match else "",
            "tags": ["hackathon"],
            "organizer": "Reskilll",
            "prize": "",
            "timezone": DEFAULT_TIMEZONE,
        }

    def fetch_events(self) -> list[dict[str, Any]]:
        listing_html = self.fetch_html(self.listing_url)
        listing_lines = _extract_text_lines(listing_html)
        links = self.dedupe_links(_extract_links(listing_html, self.listing_url))
        lower_lines = [line.lower() for line in listing_lines]

        try:
            start_index = lower_lines.index("our current hackathons")
        except ValueError:
            start_index = 0

        try:
            end_index = lower_lines.index("our community")
        except ValueError:
            end_index = len(listing_lines)

        events: list[dict[str, Any]] = []
        index = start_index
        while index < end_index:
            line = listing_lines[index]
            if line.upper() not in {"OPEN", "UPCOMING", "CLOSED"}:
                index += 1
                continue

            status = line.upper()
            if status == "CLOSED":
                index += 1
                continue

            title = listing_lines[index + 1] if index + 1 < end_index else ""
            index += 2
            description_lines: list[str] = []
            start_at = None
            end_at = None

            while index < end_index:
                current = listing_lines[index]
                if current == "Start" and index + 1 < end_index:
                    start_at = _iso_from_text(listing_lines[index + 1])
                    index += 2
                    continue
                if current == "End" and index + 1 < end_index:
                    end_at = _iso_from_text(listing_lines[index + 1])
                    index += 2
                    continue
                if current in {"Register Now", "View Details"}:
                    index += 1
                    break
                if current.upper() in {"OPEN", "UPCOMING", "CLOSED"}:
                    break
                description_lines.append(current)
                index += 1

            event_url = ""
            if title:
                title_position = listing_html.find(title)
                if title_position >= 0:
                    nearby_links = [
                        link
                        for link in links
                        if title_position <= link["position"] <= title_position + 2500
                        and parse.urlparse(link["href"]).netloc.endswith("reskilll.com")
                    ]
                    for link in nearby_links:
                        if link["text"] in {"Register Now", "View Details"}:
                            event_url = link["href"]
                            break
                    if not event_url and nearby_links:
                        event_url = nearby_links[0]["href"]

            if title:
                events.append(
                    {
                        "title": title,
                        "description": " ".join(description_lines).strip(),
                        "platform": self.platform,
                        "source_id": f"{self.platform}:{_slug_from_url(event_url or title)}",
                        "event_url": event_url,
                        "registration_url": event_url,
                        "start_at": start_at,
                        "end_at": end_at,
                        "location": "",
                        "mode": "",
                        "tags": ["hackathon"],
                        "organizer": "Reskilll",
                        "prize": "",
                        "timezone": DEFAULT_TIMEZONE,
                    }
                )

            if len(events) >= DEFAULT_MAX_EVENTS_PER_PLATFORM:
                break

        return events


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


def scrape_event_link(event_url: str, *, persist: bool = True, db_path: str = DEFAULT_DB_PATH) -> dict[str, Any]:
    platform = detect_platform_from_url(event_url)
    scraper = SCRAPER_REGISTRY[platform]()
    normalized_event = normalize_event(scraper.parse_event_link(event_url), platform)
    persisted = {"inserted": 0, "updated": 0, "persisted": 0}
    if persist:
        persisted = EventStore(db_path=db_path).upsert_events([normalized_event])
    return {
        "status": "completed",
        "platform": platform,
        "event": normalized_event,
        "persisted": persisted,
        "db_path": db_path if persist else None,
        "schedulable": _has_schedule_field(normalized_event),
    }


def schedule_selected_event_link(
    event_url: str,
    *,
    db_path: str = DEFAULT_DB_PATH,
    event_handler_url: str = DEFAULT_EVENT_HANDLER_URL,
) -> dict[str, Any]:
    scraped = scrape_event_link(event_url, persist=True, db_path=db_path)
    event = dict(scraped["event"])
    if not _has_schedule_field(event):
        return {
            "status": "needs_schedule_details",
            "message": (
                "Event link was stored, but no schedule field could be extracted from the page. "
                "You will need to provide the date manually or add OCR support for image-only schedules."
            ),
            "platform": scraped["platform"],
            "event": event,
            "persisted": scraped["persisted"],
            "db_path": scraped["db_path"],
        }

    ingestion_results = ingest_events_to_event_handler([event], event_handler_url=event_handler_url)
    return {
        "status": "scheduled" if ingestion_results and ingestion_results[0]["status"] == "accepted" else "failed",
        "platform": scraped["platform"],
        "event": event,
        "persisted": scraped["persisted"],
        "db_path": scraped["db_path"],
        "event_handler_results": ingestion_results,
    }


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
                "raw_discovered": len(normalized_events),
                "missing_schedule": sum(1 for event in normalized_events if not _has_schedule_field(event)),
                "status": "ok",
            }
        except Exception as exc:
            platform_stats[scraper.platform] = {
                "discovered": 0,
                "raw_discovered": 0,
                "missing_schedule": 0,
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
    parser.add_argument(
        "--event-url",
        help="Scrape a single event detail page from a supported platform.",
    )
    parser.add_argument(
        "--schedule-selected",
        action="store_true",
        help="When used with --event-url, schedule reminders only for that selected event link.",
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

    if args.event_url:
        if args.schedule_selected:
            result = schedule_selected_event_link(
                args.event_url,
                db_path=args.db_path,
                event_handler_url=args.event_handler_url,
            )
        else:
            result = scrape_event_link(args.event_url, persist=True, db_path=args.db_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
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
