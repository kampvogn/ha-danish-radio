"""Sensors for Danish Radio."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import html
import json
import logging
import re
from typing import Any
import urllib.error
import urllib.request

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_DR_API_KEY,
    CONF_PROVIDER,
    CONF_RAYO_SLUG,
    CONF_SCHEDULE_SLUG,
    CONF_STATION_ID,
    CONF_STATIONS,
    CONF_STREAM_URL,
    DOMAIN,
    PROVIDER_BAUER_RAYO,
    PROVIDER_DR,
    PROVIDER_ICY,
)

_LOGGER = logging.getLogger(__name__)
DR_API_BASE_URL = "https://api.dr.dk/radio/v5"
USER_AGENT = "HomeAssistant-DanishRadio/0.1 (+https://github.com/thl/ha-danish-radio)"


@dataclass
class NowPlayingData:
    """Normalized now-playing payload."""

    state: str
    station: str
    program: str = ""
    program_start: str = ""
    program_end: str = ""
    program_slug: str = ""
    program_description: str = ""
    artist: str = ""
    title: str = ""
    stream_title: str = ""
    raw_metadata: str = ""
    stream_url: str = ""
    image: str = ""
    source: str = ""
    updated_at: str = ""

    def attributes(self) -> dict[str, str]:
        """Return Home Assistant attributes."""
        return {
            "station": self.station,
            "program": self.program,
            "program_start": self.program_start,
            "program_end": self.program_end,
            "program_slug": self.program_slug,
            "program_description": self.program_description,
            "artist": self.artist,
            "title": self.title,
            "stream_title": self.stream_title,
            "raw_metadata": self.raw_metadata,
            "stream_url": self.stream_url,
            "image": self.image,
            "source": self.source,
            "updated_at": self.updated_at,
        }


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up configured station sensors."""
    entities: list[RadioNowPlayingSensor] = []
    for station in hass.data[DOMAIN][CONF_STATIONS]:
        coordinator = RadioNowPlayingCoordinator(hass, station)
        await coordinator.async_config_entry_first_refresh()
        entities.append(RadioNowPlayingSensor(coordinator, station))
    async_add_entities(entities)


class RadioNowPlayingCoordinator(DataUpdateCoordinator[NowPlayingData]):
    """Coordinator that polls one radio metadata provider."""

    def __init__(self, hass: HomeAssistant, station: dict[str, Any]) -> None:
        self.station = station
        super().__init__(
            hass,
            _LOGGER,
            name=f"{station[CONF_NAME]} now playing",
            update_interval=station["scan_interval"],
        )

    async def _async_update_data(self) -> NowPlayingData:
        """Fetch station metadata."""
        try:
            return await self.hass.async_add_executor_job(fetch_station, self.station)
        except Exception as err:  # noqa: BLE001 - surface provider failures to HA
            raise UpdateFailed(str(err)) from err


class RadioNowPlayingSensor(CoordinatorEntity[RadioNowPlayingCoordinator], SensorEntity):
    """Radio now-playing sensor."""

    _attr_icon = "mdi:radio"

    def __init__(
        self, coordinator: RadioNowPlayingCoordinator, station: dict[str, Any]
    ) -> None:
        super().__init__(coordinator)
        self._station = station
        station_id = station.get(CONF_STATION_ID) or slugify(station[CONF_NAME])
        self._attr_name = f"{station[CONF_NAME]} nu spiller"
        self._attr_unique_id = f"danish_radio_{station_id}"

    @property
    def native_value(self) -> str:
        """Return current state."""
        return self.coordinator.data.state

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return normalized metadata attributes."""
        return self.coordinator.data.attributes()


def fetch_station(station: dict[str, Any]) -> NowPlayingData:
    """Fetch metadata for one station."""
    provider = station[CONF_PROVIDER]
    if provider == PROVIDER_DR:
        return fetch_dr(station)
    if provider == PROVIDER_BAUER_RAYO:
        return fetch_bauer_rayo(station)
    if provider == PROVIDER_ICY:
        return fetch_icy(station)
    raise ValueError(f"Unsupported provider: {provider}")


def fetch_dr(station: dict[str, Any]) -> NowPlayingData:
    """Fetch DR schedule data and ICY metadata."""
    program = get_dr_current_program(
        station[CONF_SCHEDULE_SLUG], station[CONF_DR_API_KEY]
    )
    metadata = read_icy_metadata(station[CONF_STREAM_URL])
    stream_title = parse_stream_title(metadata)
    artist, title = split_artist_title(stream_title)
    return NowPlayingData(
        state=stream_title or program.get("program") or "Ingen metadata",
        station=station[CONF_NAME],
        **program,
        artist=artist,
        title=title,
        stream_title=stream_title,
        raw_metadata=metadata,
        stream_url=station[CONF_STREAM_URL],
        source="dr",
        updated_at=utcnow(),
    )


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

    if not stream_title:
        metadata = read_icy_metadata(station[CONF_STREAM_URL], skip_ads=True, max_blocks=32)
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
        stream_url=station[CONF_STREAM_URL],
        image=str(track.get("nowPlayingImage") or on_air.get("episodeImageUrl") or ""),
        source=f"bauer_rayo:{track_source}" if track_source else "bauer_rayo",
        updated_at=utcnow(),
    )


def fetch_icy(station: dict[str, Any]) -> NowPlayingData:
    """Fetch generic ICY metadata."""
    metadata = read_icy_metadata(station[CONF_STREAM_URL], skip_ads=True, max_blocks=32)
    stream_title = parse_stream_title(metadata)
    artist, title = split_artist_title(stream_title)
    return NowPlayingData(
        state=stream_title or "Ingen metadata",
        station=station[CONF_NAME],
        artist=artist,
        title=title,
        stream_title=stream_title,
        raw_metadata=metadata,
        stream_url=station[CONF_STREAM_URL],
        source="icy",
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
            }
    return {}


def read_json(url: str, headers: dict[str, str] | None = None) -> Any:
    """Read JSON from a URL."""
    request = urllib.request.Request(url, headers=request_headers("application/json", headers))
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


def parse_rayo_page(page: str) -> dict[str, Any]:
    """Extract station payload from Rayo Next.js page."""
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


def program_end(start: Any, duration: Any) -> str:
    """Calculate program end timestamp from Rayo start and duration."""
    if not start or not duration:
        return ""
    try:
        start_dt = datetime.strptime(str(start), "%Y-%m-%d %H:%M:%S")
        return (start_dt + timedelta(seconds=int(duration))).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return ""


def slugify(value: str) -> str:
    """Create a stable slug."""
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "station"


def utcnow() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
