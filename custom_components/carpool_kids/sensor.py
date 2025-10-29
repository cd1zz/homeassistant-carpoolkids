"""Sensor platform for Carpool Kids."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    SENSOR_TODAY,
    SENSOR_UPCOMING,
    SENSOR_NEXT_EVENT,
    SENSOR_STATUS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Carpool Kids sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        CarpoolTodaySensor(coordinator, entry),
        CarpoolUpcomingSensor(coordinator, entry),
        CarpoolNextEventSensor(coordinator, entry),
        CarpoolStatusSensor(coordinator, entry),
    ]

    # Add individual event sensors
    for i in range(5):
        entities.append(CarpoolEventSensor(coordinator, entry, i))

    async_add_entities(entities)


class CarpoolSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Carpool Kids sensors."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_has_entity_name = False
        self.sensor_type = sensor_type

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class CarpoolTodaySensor(CarpoolSensorBase):
    """Sensor for today's carpool events."""

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, SENSOR_TODAY)
        self._attr_name = "Carpool Today"
        self._attr_icon = "mdi:car-multiple"

    @property
    def native_value(self) -> str | int:
        """Return the state of the sensor."""
        today_events = self.coordinator.data.get("today", [])
        return len(today_events) if today_events else "none"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        today_events = self.coordinator.data.get("today", [])
        attrs = {}
        if today_events:
            attrs["events"] = today_events
            attrs["unit_of_measurement"] = "events"
        return attrs


class CarpoolUpcomingSensor(CarpoolSensorBase):
    """Sensor for upcoming carpool events."""

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, SENSOR_UPCOMING)
        self._attr_name = "Carpool Upcoming"
        self._attr_icon = "mdi:calendar-clock"

    @property
    def native_value(self) -> str | int:
        """Return the state of the sensor."""
        upcoming_events = self.coordinator.data.get("upcoming", [])
        return len(upcoming_events) if upcoming_events else "none"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        upcoming_events = self.coordinator.data.get("upcoming", [])
        attrs = {}
        if upcoming_events:
            attrs["events"] = upcoming_events
            attrs["unit_of_measurement"] = "events"
        return attrs


class CarpoolNextEventSensor(CarpoolSensorBase):
    """Sensor for the next carpool event."""

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, SENSOR_NEXT_EVENT)
        self._attr_name = "Carpool Next Event"
        self._attr_icon = "mdi:clock-outline"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        next_event = self.coordinator.data.get("next_event")
        if not next_event:
            return "No events scheduled"

        legs = next_event.get("legs", [])
        if legs:
            first_leg = legs[0]
            return f"{next_event['date']} {first_leg['time_formatted']}"
        return next_event["date"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        next_event = self.coordinator.data.get("next_event")
        if not next_event:
            return {}

        attrs = {
            "date": next_event["date"],
            "day": next_event["day_name"],
            "location": next_event["location"],
        }

        legs = next_event.get("legs", [])
        if legs:
            first_leg = legs[0]
            attrs["time"] = first_leg["time_formatted"]
            attrs["driver"] = first_leg["driver_name"]
            attrs["riders"] = first_leg["rider_count"]

        return attrs


class CarpoolStatusSensor(CarpoolSensorBase):
    """Sensor for carpool monitor status."""

    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, SENSOR_STATUS)
        self._attr_name = "Carpool Status"
        self._attr_icon = "mdi:check-circle"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return "online" if self.coordinator.last_update_success else "error"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        all_events = self.coordinator.data.get("all_events", [])
        attrs = {
            "last_update": datetime.now().isoformat(),
            "total_events": len(all_events),
        }

        if not self.coordinator.last_update_success:
            attrs["error"] = "Failed to update data"

        return attrs


class CarpoolEventSensor(CarpoolSensorBase):
    """Sensor for individual carpool events."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        event_index: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, f"event_{event_index + 1}")
        self.event_index = event_index
        self._attr_name = f"Carpool Event {event_index + 1}"
        self._attr_icon = "mdi:car"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        all_events = self.coordinator.data.get("all_events", [])
        return len(all_events) > self.event_index

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        all_events = self.coordinator.data.get("all_events", [])
        if len(all_events) <= self.event_index:
            return "unavailable"

        event_data = all_events[self.event_index]
        try:
            event_date = datetime.fromisoformat(
                event_data["dateTime"].replace("Z", "").replace(".000", "")
            )
            legs = event_data.get("eventLegs", [])
            if legs:
                leg_time = datetime.fromisoformat(
                    legs[0]["dateTime"].replace("Z", "").replace(".000", "")
                )
                return f"{event_date.strftime('%Y-%m-%d')} {leg_time.strftime('%I:%M %p')}"
            return event_date.strftime("%Y-%m-%d")
        except Exception as err:
            _LOGGER.error("Error parsing event data: %s", err)
            return "error"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        all_events = self.coordinator.data.get("all_events", [])
        if len(all_events) <= self.event_index:
            return {}

        event_data = all_events[self.event_index]
        try:
            event_date = datetime.fromisoformat(
                event_data["dateTime"].replace("Z", "").replace(".000", "")
            )

            return {
                "date": event_date.strftime("%Y-%m-%d"),
                "day": event_date.strftime("%A"),
                "location": event_data.get("location", "Unknown"),
                "total_legs": len(event_data.get("eventLegs", [])),
            }
        except Exception as err:
            _LOGGER.error("Error parsing event attributes: %s", err)
            return {}
