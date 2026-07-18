"""Generic ICY metadata provider."""

from __future__ import annotations

from typing import Any

from ..const import CONF_NAME, CONF_STREAM_URL
from ..models import NowPlayingData
from ..util import parse_stream_title, read_icy_metadata, split_artist_title, utcnow


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
