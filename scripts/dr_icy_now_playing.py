#!/usr/bin/env python3
"""Read current radio metadata for Home Assistant."""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone


DR_API_KEY = "6Wkh8s98Afx1ZAaTT4FuWODTmvWGDPpR"
DR_API_BASE_URL = "https://api.dr.dk/radio/v5"

STATIONS = {
    "p3": {
        "name": "DR P3",
        "url": "https://live-icy.dr.dk/A/A05H.mp3",
        "provider": "dr",
        "schedule_slug": "p3",
    },
    "p4aarhus": {
        "name": "DR P4 Østjylland",
        "url": "https://live-icy.dr.dk/A/A14H.mp3",
        "provider": "dr",
        "schedule_slug": "p4aarhus",
    },
    "nova": {
        "name": "NOVA",
        "url": "https://live-bauerdk.sharp-stream.com/nova_dk_mp3?direct=true",
        "provider": "bauer",
        "rayo_slug": "nova",
    },
}


def emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def parse_stream_title(metadata: str) -> str:
    match = re.search(r"StreamTitle='([^']*)'", metadata)
    if not match:
        return ""
    title = match.group(1).strip()
    return title[2:].strip() if title.startswith("/ ") else title


def parse_icy_fields(metadata: str) -> dict[str, str]:
    return {
        key: value.strip()
        for key, value in re.findall(r"([A-Za-z0-9_]+)='([^']*)'", metadata)
    }


def is_ad_metadata(metadata: str) -> bool:
    fields = parse_icy_fields(metadata)
    return (
        fields.get("adw_ad", "").lower() == "true"
        or bool(fields.get("insertionType"))
        or (bool(fields) and not fields.get("StreamTitle", "").strip())
    )


def split_artist_title(stream_title: str) -> tuple[str, str]:
    if " - " not in stream_title:
        return "", stream_title
    artist, title = stream_title.split(" - ", 1)
    return artist.strip(), title.strip()


def read_json(url: str, headers: dict[str, str] | None = None) -> object:
    req_headers = {
        "Accept": "application/json",
        "User-Agent": "HomeAssistant-Radio-NowPlaying/1.0",
    }
    if headers:
        req_headers.update(headers)
    request = urllib.request.Request(
        url,
        headers=req_headers,
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode())


def read_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "HomeAssistant-Radio-NowPlaying/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read().decode()


def get_current_program(channel_slug: str) -> dict[str, str]:
    try:
        schedules = read_json(
            f"{DR_API_BASE_URL}/schedules/all/now",
            headers={"x-apikey": DR_API_KEY},
        )
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
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
            }
    return {}


def read_icy_metadata(url: str, *, skip_ads: bool = False, max_blocks: int = 16) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Icy-MetaData": "1",
            "User-Agent": "HomeAssistant-Radio-NowPlaying/1.0",
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
    return ""


def parse_rayo_page(page: str) -> dict[str, object]:
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


def program_end(start: object, duration: object) -> str:
    if not start or not duration:
        return ""
    try:
        start_dt = datetime.strptime(str(start), "%Y-%m-%d %H:%M:%S")
        return (start_dt + timedelta(seconds=int(duration))).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return ""


def track_from_rayo_payload(station: dict[str, object]) -> tuple[dict[str, object], str]:
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


def get_bauer_now_playing(station: dict[str, object]) -> dict[str, object]:
    rayo_station: dict[str, object] = {}
    try:
        page = read_text(f"https://rayo.dk/{station['rayo_slug']}")
        rayo_station = parse_rayo_page(page)
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        pass

    on_air_obj = rayo_station.get("stationOnAir")
    on_air = on_air_obj if isinstance(on_air_obj, dict) else {}
    track, track_source = track_from_rayo_payload(rayo_station)

    artist = str(track.get("nowPlayingArtist") or "")
    title = str(track.get("nowPlayingTrack") or "")
    stream_title = f"{artist} - {title}".strip(" -")
    program = str(on_air.get("episodeTitle") or "")

    metadata = ""
    if not stream_title:
        metadata = read_icy_metadata(str(station["url"]), skip_ads=True, max_blocks=32)
        stream_title = parse_stream_title(metadata)
        artist, title = split_artist_title(stream_title)

    return {
        "state": stream_title or program or "Ingen metadata",
        "station": str(rayo_station.get("stationName") or station["name"]),
        "program": program,
        "program_start": str(on_air.get("episodeStart") or ""),
        "program_end": program_end(on_air.get("episodeStart"), on_air.get("episodeDuration")),
        "program_slug": str(on_air.get("showId") or ""),
        "program_description": str(on_air.get("episodeDescription") or ""),
        "artist": artist,
        "title": title,
        "stream_title": stream_title,
        "raw_metadata": metadata,
        "stream_url": str(station["url"]),
        "image": str(track.get("nowPlayingImage") or on_air.get("episodeImageUrl") or ""),
        "track_source": track_source,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


P3_WEBCAM_FALLBACK = (
    "https://drp3webcamhls.akamaized.net/hls/live/20003007/p3webcam/mastervg.m3u8"
)


def is_live_hls(master_url: str) -> bool:
    """True when the first variant playlist of an HLS master is still live."""
    master = read_text(master_url)
    for line in master.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            variant = urllib.parse.urljoin(master_url, line)
            return "#EXT-X-ENDLIST" not in read_text(variant)
    return False


def get_p3_webcam_stream() -> dict[str, object]:
    """Find a live DR P3 studio webcam HLS stream (video + audio) on dr.dk/lyd.

    dr.dk/lyd lists more than one webcam master; old ones stay listed after
    they have ended (#EXT-X-ENDLIST), so pick the first that is still live.
    """
    url, source = "", "fallback"
    try:
        page = read_text("https://www.dr.dk/lyd")
        candidates = dict.fromkeys(
            re.findall(
                r"https://drp3webcamhls\.akamaized\.net/[^\"'\\\s]*/master[a-z]*\.m3u8",
                page,
            )
        )
        for candidate in candidates:
            try:
                if is_live_hls(candidate):
                    url, source = candidate, "dr.dk/lyd"
                    break
            except (OSError, TimeoutError, urllib.error.URLError):
                continue
    except (OSError, TimeoutError, urllib.error.URLError):
        pass
    return {
        "state": url or P3_WEBCAM_FALLBACK,
        "source": source,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    station_key = sys.argv[1] if len(sys.argv) > 1 else "p3"
    if station_key == "p3webcam":
        emit(get_p3_webcam_stream())
        return 0
    station = STATIONS.get(station_key)
    if station is None:
        emit(
            {
                "state": "Ukendt station",
                "error": f"Unknown station: {station_key}",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return 1

    try:
        if station.get("provider") == "bauer":
            emit(get_bauer_now_playing(station))
            return 0

        program = get_current_program(str(station["schedule_slug"]))
        metadata = read_icy_metadata(station["url"])
        stream_title = parse_stream_title(metadata)
        artist, title = split_artist_title(stream_title)
        emit(
            {
                "state": stream_title or "Ingen metadata",
                "station": station["name"],
                **program,
                "artist": artist,
                "title": title,
                "stream_title": stream_title,
                "raw_metadata": metadata,
                "stream_url": station["url"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return 0
    except (OSError, TimeoutError, urllib.error.URLError) as exc:
        emit(
            {
                "state": "Fejl",
                "station": station["name"],
                "error": str(exc),
                "stream_url": station["url"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
