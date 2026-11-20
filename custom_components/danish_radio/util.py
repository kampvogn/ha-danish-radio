"""Utility helpers for Danish Radio."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any
import urllib.request

USER_AGENT = "HomeAssistant-DanishRadio/0.1 (+https://github.com/kampvogn/ha-danish-radio)"


def read_json(url: str, headers: dict[str, str] | None = None) -> Any:
    """Read JSON from a URL."""
    request = urllib.request.Request(
        url, headers=request_headers("application/json", headers)
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode())


def read_text(url: str) -> str:
    """Read text from a URL."""
    request = urllib.request.Request(url, headers=request_headers("text/html"))
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read().decode()


def request_headers(accept: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    """Build HTTP headers."""
    headers = {"Accept": accept, "User-Agent": USER_AGENT}
    if extra:
        headers.update(extra)
    return headers


def parse_stream_title(metadata: str) -> str:
    """Extract StreamTitle from ICY metadata."""
    match = re.search(r"StreamTitle='([^']*)'", metadata)
    if not match:
        return ""
    title = match.group(1).strip()
    return title[2:].strip() if title.startswith("/ ") else title


def parse_icy_fields(metadata: str) -> dict[str, str]:
    """Parse key='value' ICY metadata fields."""
    return {
        key: value.strip()
        for key, value in re.findall(r"([A-Za-z0-9_]+)='([^']*)'", metadata)
    }


def is_ad_metadata(metadata: str) -> bool:
    """Return true for Adswizz/empty metadata blocks."""
    fields = parse_icy_fields(metadata)
    return (
        fields.get("adw_ad", "").lower() == "true"
        or bool(fields.get("insertionType"))
        or (bool(fields) and not fields.get("StreamTitle", "").strip())
    )


def split_artist_title(stream_title: str) -> tuple[str, str]:
    """Split common Artist - Title metadata."""
    if " - " not in stream_title:
        return "", stream_title
    artist, title = stream_title.split(" - ", 1)
    return artist.strip(), title.strip()


def read_icy_metadata(url: str, *, skip_ads: bool = False, max_blocks: int = 16) -> str:
    """Read ICY metadata from an audio stream."""
    request = urllib.request.Request(
        url,
        headers={
            "Icy-MetaData": "1",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        metaint = int(response.headers.get("icy-metaint", "0") or 0)
        if metaint <= 0:
            return ""

        fallback_metadata = ""
        for _ in range(max_blocks):
            response.read(metaint)
            length_byte = response.read(1)
            if not length_byte:
                return ""
            metadata_length = length_byte[0] * 16
            if metadata_length <= 0:
                continue
            metadata = response.read(metadata_length).decode("utf-8", "replace").strip("\x00")
            if not fallback_metadata:
                fallback_metadata = metadata
            if skip_ads and is_ad_metadata(metadata):
                continue
            if parse_stream_title(metadata):
                return metadata
        return fallback_metadata


def slugify(value: str) -> str:
    """Create a stable slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "station"


def utcnow() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
