"""Metadata providers for Danish Radio."""

from __future__ import annotations

from typing import Any

from ..const import PROVIDER_BAUER_RAYO, PROVIDER_DR, PROVIDER_ICY
from ..models import NowPlayingData
from .bauer_rayo import fetch_bauer_rayo
from .dr import fetch_dr
from .icy import fetch_icy


def fetch_station(station: dict[str, Any]) -> NowPlayingData:
    """Fetch metadata for one station."""
    provider = station["provider"]
    if provider == PROVIDER_DR:
        return fetch_dr(station)
    if provider == PROVIDER_BAUER_RAYO:
        return fetch_bauer_rayo(station)
    if provider == PROVIDER_ICY:
        return fetch_icy(station)
    raise ValueError(f"Unsupported provider: {provider}")
