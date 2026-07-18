"""DR metadata provider."""

from __future__ import annotations

import json
from typing import Any
import urllib.error

from ..const import (
    CONF_DR_API_KEY,
    CONF_NAME,
    CONF_SCHEDULE_SLUG,
    CONF_STREAM_URL,
)
from ..models import NowPlayingData
from ..util import (
    parse_stream_title,
    read_icy_metadata,
    read_json,
    split_artist_title,
    utcnow,
)

DR_API_BASE_URL = "https://api.dr.dk/radio/v5"


def fetch_dr(station: dict[str, Any]) -> NowPlayingData:
    """Fetch DR schedule data and ICY metadata."""
    program = get_dr_current_program(
        station[CONF_SCHEDULE_SLUG], station[CONF_DR_API_KEY]
    )
    stream_url = station.get(CONF_STREAM_URL) or program.get("stream_url", "")
    program_attributes = {
        key: value for key, value in program.items() if key != "stream_url"
    }
    metadata = read_icy_metadata(stream_url) if stream_url else ""
    stream_title = parse_stream_title(metadata)
    artist, title = split_artist_title(stream_title)
    return NowPlayingData(
        state=stream_title or program.get("program") or "Ingen metadata",
        station=station[CONF_NAME],
        **program_attributes,
        artist=artist,
        title=title,
        stream_title=stream_title,
        raw_metadata=metadata,
        stream_url=stream_url,
        source="dr",
        updated_at=utcnow(),
    )


def get_dr_current_program(channel_slug: str, api_key: str) -> dict[str, str]:
    """Fetch current DR programme for a channel slug."""
    try:
        schedules = read_json(
            f"{DR_API_BASE_URL}/schedules/all/now",
            headers={"x-apikey": api_key},
        )
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return {}

    if not isinstance(schedules, list):
        return {}

    for item in schedules:
        if not isinstance(item, dict):
            continue
        channel = item.get("channel")
        if isinstance(channel, dict) and channel.get("slug") == channel_slug:
            return {
                "program": str(item.get("title") or ""),
                "program_start": str(item.get("startTime") or ""),
                "program_end": str(item.get("endTime") or ""),
                "program_slug": str(item.get("slug") or ""),
                "program_description": str(item.get("description") or ""),
                "stream_url": best_dr_stream_url(item.get("audioAssets")),
            }
    return {}


def best_dr_stream_url(audio_assets: Any) -> str:
    """Pick the best ICY stream from a DR schedule item."""
    if not isinstance(audio_assets, list):
        return ""
    icy_assets = [
        asset
        for asset in audio_assets
        if isinstance(asset, dict)
        and asset.get("format") == "ICY"
        and isinstance(asset.get("url"), str)
    ]
    if not icy_assets:
        return ""
    return str(
        max(icy_assets, key=lambda asset: int(asset.get("bitrate") or 0)).get("url")
    )
