"""Sensors for Danish Radio."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CONF_NAME, CONF_STATION_ID, CONF_STATIONS, DOMAIN
from .models import NowPlayingData
from .providers import fetch_station
from .util import slugify

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up configured station sensors."""
    entities: list[DanishRadioSensor] = []
    for station in hass.data[DOMAIN][CONF_STATIONS]:
        coordinator = DanishRadioCoordinator(hass, station)
        # YAML platform: no config entry, so async_config_entry_first_refresh()
        # is not allowed. A failed first refresh leaves the sensor unavailable
        # until the next poll instead of failing setup.
        await coordinator.async_refresh()
        entities.append(DanishRadioSensor(coordinator, station))
    async_add_entities(entities)


class DanishRadioCoordinator(DataUpdateCoordinator[NowPlayingData]):
    """Coordinator that polls one radio metadata provider."""

    def __init__(self, hass: HomeAssistant, station: dict[str, Any]) -> None:
        self.station = station
        super().__init__(
            hass,
            _LOGGER,
            config_entry=None,
            name=f"{station[CONF_NAME]} now playing",
            update_interval=station["scan_interval"],
        )

    async def _async_update_data(self) -> NowPlayingData:
        """Fetch station metadata."""
        try:
            return await self.hass.async_add_executor_job(fetch_station, self.station)
        except Exception as err:  # noqa: BLE001 - surface provider failures to HA
            raise UpdateFailed(str(err)) from err


class DanishRadioSensor(CoordinatorEntity[DanishRadioCoordinator], SensorEntity):
    """Danish radio now-playing sensor."""

    _attr_icon = "mdi:radio"

    def __init__(
        self, coordinator: DanishRadioCoordinator, station: dict[str, Any]
    ) -> None:
        super().__init__(coordinator)
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
