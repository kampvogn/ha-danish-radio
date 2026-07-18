"""Danish Radio integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform

from .const import (
    CONF_DR_API_KEY,
    CONF_PROVIDER,
    CONF_RAYO_SLUG,
    CONF_SCHEDULE_SLUG,
    CONF_STATION_ID,
    CONF_STATIONS,
    CONF_STREAM_URL,
    DEFAULT_DR_API_KEY,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    PROVIDER_BAUER_RAYO,
    PROVIDER_DR,
    PROVIDER_ICY,
)

_LOGGER = logging.getLogger(__name__)

STATION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PROVIDER): vol.In(
            [PROVIDER_ICY, PROVIDER_DR, PROVIDER_BAUER_RAYO]
        ),
        vol.Required(CONF_STREAM_URL): cv.url,
        vol.Optional(CONF_STATION_ID): cv.string,
        vol.Optional(CONF_SCHEDULE_SLUG): cv.string,
        vol.Optional(CONF_RAYO_SLUG): cv.string,
        vol.Optional(CONF_DR_API_KEY, default=DEFAULT_DR_API_KEY): cv.string,
        vol.Optional(
            "scan_interval", default=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS)
        ): cv.time_period,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_STATIONS): vol.All(cv.ensure_list, [STATION_SCHEMA]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up Danish Radio from YAML."""
    conf = config.get(DOMAIN)
    if conf is None:
        return True

    stations = conf[CONF_STATIONS]
    hass.data[DOMAIN] = {CONF_STATIONS: stations}
    await async_load_platform(hass, Platform.SENSOR, DOMAIN, {}, config)
    _LOGGER.info("Configured %s radio now-playing station(s)", len(stations))
    return True
