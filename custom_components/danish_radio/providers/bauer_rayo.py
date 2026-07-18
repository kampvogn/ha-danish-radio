"""Bauer/Rayo metadata provider."""

from __future__ import annotations

from datetime import datetime, timedelta
import html
import json
import logging
import re
from typing import Any
import urllib.error

from ..const import CONF_NAME, CONF_RAYO_SLUG, CONF_STREAM_URL
from ..models import NowPlayingData
from ..util import (
    parse_stream_title,
    read_icy_metadata,
    read_text,
    split_artist_title,
    utcnow,
)

_LOGGER = logging.getLogger(__name__)


def fetch_bauer_rayo(station: dict[str, Any]) -> NowPlayingData:
    """Fetch Bauer/Rayo station JSON with ICY fallback."""
    rayo_station: dict[str, Any] = {}
    try:
        page = read_text(f"https://rayo.dk/{station[CONF_RAYO_SLUG]}")
        rayo_station = parse_rayo_page(page)
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        _LOGGER.debug("Unable to fetch Rayo metadata for %s", station[CONF_NAME])

    on_air = rayo_station.get("stationOnAir")
    on_air = on_air if isinstance(on_air, dict) else {}
    track, track_source = track_from_rayo_payload(rayo_station)

    artist = str(track.get("nowPlayingArtist") or "")
    title = str(track.get("nowPlayingTrack") or "")
    stream_title = f"{artist} - {title}".strip(" -")
    metadata = ""
    stream_url = station.get(CONF_STREAM_URL) or best_rayo_stream_url(rayo_station)

    if not stream_title and stream_url:
        metadata = read_icy_metadata(stream_url, skip_ads=True, max_blocks=32)
        stream_title = parse_stream_title(metadata)
        artist, title = split_artist_title(stream_title)

    program = str(on_air.get("episodeTitle") or "")
    return NowPlayingData(
        state=stream_title or program or "Ingen metadata",
        station=str(rayo_station.get("stationName") or station[CONF_NAME]),
        program=program,
        program_start=str(on_air.get("episodeStart") or ""),
        program_end=program_end(on_air.get("episodeStart"), on_air.get("episodeDuration")),
        program_slug=str(on_air.get("showId") or ""),
        program_description=str(on_air.get("episodeDescription") or ""),
        artist=artist,
        title=title,
        stream_title=stream_title,
        raw_metadata=metadata,
        stream_url=stream_url,
        image=str(track.get("nowPlayingImage") or on_air.get("episodeImageUrl") or ""),
        source=f"bauer_rayo:{track_source}" if track_source else "bauer_rayo",
        updated_at=utcnow(),
    )


def parse_rayo_page(page: str) -> dict[str, Any]:
    """Extract station payload from a Rayo Next.js page."""
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        page,
        flags=re.S,
    )
    if not match:
        return {}

    data = json.loads(html.unescape(match.group(1)))
    station = (
        data.get("props", {})
        .get("initialState", {})
        .get("station", {})
        .get("data", {})
    )
    return station if isinstance(station, dict) else {}


def track_from_rayo_payload(station: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Return current track or first play-history track from Rayo payload."""
    now_playing = station.get("stationNowPlaying")
    if isinstance(now_playing, dict) and (
        now_playing.get("nowPlayingTrack") or now_playing.get("nowPlayingArtist")
    ):
        return now_playing, "now_playing"

    history = station.get("stationPlayHistory")
    if isinstance(history, list):
        for item in history:
            if isinstance(item, dict) and (
                item.get("nowPlayingTrack") or item.get("nowPlayingArtist")
            ):
                return item, "play_history"

    return {}, ""


def best_rayo_stream_url(station: dict[str, Any]) -> str:
    """Pick a public non-premium Rayo stream URL."""
    streams = station.get("stationStreams")
    if not isinstance(streams, list):
        return ""

    candidates = [
        stream
        for stream in streams
        if isinstance(stream, dict)
        and stream.get("streamUrl")
        and not stream.get("streamPremium")
        and not stream.get("streamUsersOnly")
    ]
    if not candidates:
        return ""

    def score(stream: dict[str, Any]) -> tuple[int, int, int]:
        stream_type = str(stream.get("streamType") or "")
        quality = str(stream.get("streamQuality") or "")
        bitrate = int(stream.get("streamBitRate") or 0)
        return (1 if stream_type == "mp3" else 0, 1 if quality == "hq" else 0, bitrate)

    return str(max(candidates, key=score).get("streamUrl"))


def program_end(start: Any, duration: Any) -> str:
    """Calculate program end timestamp from Rayo start and duration."""
    if not start or not duration:
        return ""
    try:
        start_dt = datetime.strptime(str(start), "%Y-%m-%d %H:%M:%S")
        return (start_dt + timedelta(seconds=int(duration))).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return ""
