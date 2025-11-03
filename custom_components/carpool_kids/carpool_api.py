"""API Client for Carpool Kids."""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests

from .const import (
    AUTH_URL,
    CARPOOL_AUTH_URL,
    EVENTS_URL,
)

_LOGGER = logging.getLogger(__name__)


class CarpoolAPI:
    """API client for Carpool Kids."""

    def __init__(
        self,
        email: str,
        android_id: str,
        token: str,
        timezone: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self.email = email
        self.android_id = android_id
        self.token = token
        self.timezone = ZoneInfo(timezone) if timezone else ZoneInfo("UTC")
        self._setup_auth_config()
        self.data: dict[str, Any] = {}

    def _setup_auth_config(self) -> None:
        """Setup authentication configuration."""
        self.auth_headers = {
            "Accept-Encoding": "gzip",
            "app": "com.newwavecoding.carpool_kids",
            "Connection": "Keep-Alive",
            "content-type": "application/x-www-form-urlencoded",
            "device": self.android_id,
            "Host": "android.googleapis.com",
            "User-Agent": "GoogleAuth/1.4 (generic_x86_64_arm64 RSR1.240422.006); gzip",
        }

    def _authenticate_google(self) -> str | None:
        """Authenticate with Google and return access token."""
        post_data = {
            "androidId": self.android_id,
            "lang": "en-US",
            "google_play_services_version": "201817023",
            "sdk_version": "30",
            "device_country": "us",
            "is_dev_key_gmscore": "1",
            "app": "com.newwavecoding.carpool_kids",
            "check_email": "1",
            "Email": self.email,
            "has_permission": "1",
            "token_request_options": "CAA4AVADWhZaRmhGWV9LWTdaSHRka2RnZzhGQV9R",
            "service": "oauth2:email https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid profile",
            "client_sig": "6e677abde7869379c39c6d07dd8c2bbb0ed5eb13",
            "callerPkg": "com.google.android.gms",
            "Token": self.token,
            "request_visible_actions": "",
            "callerSig": "58e1c4133f7441ec3d2c270270a14802da47ba0e",
        }

        try:
            _LOGGER.debug("Attempting Google authentication...")
            response = requests.post(
                AUTH_URL, data=post_data, headers=self.auth_headers, timeout=30
            )

            if response.status_code == 200:
                response_text = response.text
                if "Auth=" in response_text:
                    for line in response_text.split("\n"):
                        if line.startswith("Auth="):
                            token = line.replace("Auth=", "").strip()
                            _LOGGER.debug("Google auth token extracted")
                            return token
                return response_text
            else:
                _LOGGER.error(
                    "Google auth failed with status %s", response.status_code
                )
                return None

        except requests.exceptions.RequestException as err:
            _LOGGER.error("Google auth request failed: %s", err)
            return None

    def _get_carpool_token(self, google_token: str) -> str | None:
        """Exchange Google token for carpool app token."""
        payload = {"accessToken": google_token}
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Dart/2.19 (dart:io)",
            "Accept": "application/json",
        }

        try:
            _LOGGER.debug("Attempting carpool authentication...")
            response = requests.post(
                CARPOOL_AUTH_URL, json=payload, headers=headers, timeout=30
            )

            if response.status_code == 200:
                carpool_data = response.json()
                # Try different possible token field names
                token_fields = ["token", "access_token", "jwt", "authToken"]
                for field in token_fields:
                    if field in carpool_data:
                        _LOGGER.debug("Found carpool token in field '%s'", field)
                        return carpool_data.get(field)

                _LOGGER.warning("No token found in carpool response")
                return None
            else:
                _LOGGER.error(
                    "Carpool auth failed with status %s", response.status_code
                )
                return None

        except requests.exceptions.RequestException as err:
            _LOGGER.error("Carpool auth request failed: %s", err)
            return None

    def _get_events(self, carpool_token: str) -> list[dict[str, Any]] | None:
        """Get events data from carpool API."""
        headers = {
            "x-auth-token": carpool_token,
            "Content-Type": "application/json",
            "User-Agent": "Dart/2.19 (dart:io)",
            "Accept": "application/json",
        }

        try:
            _LOGGER.debug("Fetching carpool events...")
            response = requests.get(EVENTS_URL, headers=headers, timeout=30)

            if response.status_code == 200:
                events_data = response.json()

                if isinstance(events_data, list):
                    _LOGGER.debug("Received %s events from API", len(events_data))
                    return events_data
                elif isinstance(events_data, dict):
                    # Check if dict contains events in a nested structure
                    if "events" in events_data:
                        return events_data["events"]
                    elif "data" in events_data:
                        return events_data["data"]
                    else:
                        _LOGGER.warning("Unexpected dict response structure")
                        return None
                else:
                    _LOGGER.warning("Unexpected response type: %s", type(events_data))
                    return None
            else:
                _LOGGER.error("Events API failed with status %s", response.status_code)
                return None

        except requests.exceptions.RequestException as err:
            _LOGGER.error("Events API request failed: %s", err)
            return None

    def _process_events(self, events_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Process events data and organize by date."""
        if not events_data:
            return {
                "today": [],
                "upcoming": [],
                "next_event": None,
                "all_events": [],
            }

        # Sort events by date
        try:
            sorted_events = sorted(events_data, key=lambda x: x["dateTime"])
        except KeyError:
            _LOGGER.error("Events missing dateTime field")
            return {
                "today": [],
                "upcoming": [],
                "next_event": None,
                "all_events": [],
            }

        today = datetime.now().date()
        today_events = []
        upcoming_events = []

        for event in sorted_events:
            try:
                processed_event = self._process_single_event(event)
                event_date = datetime.fromisoformat(
                    event["dateTime"].replace("Z", "").replace(".000", "")
                ).date()

                if event_date == today:
                    today_events.append(processed_event)
                elif event_date > today:
                    upcoming_events.append(processed_event)
            except Exception as err:
                _LOGGER.error("Error processing event: %s", err)
                continue

        next_event = None
        if today_events:
            next_event = today_events[0]
        elif upcoming_events:
            next_event = upcoming_events[0]

        return {
            "today": today_events,
            "upcoming": upcoming_events[:10],  # Limit to 10 upcoming events
            "next_event": next_event,
            "all_events": sorted_events[:5],  # Keep raw data for individual sensors
        }

    def _process_single_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Process a single event and return formatted data."""
        event_date = datetime.fromisoformat(
            event["dateTime"].replace("Z", "").replace(".000", "")
        )
        local_tz = self.timezone

        processed_legs = []
        carpool_drivers = event.get("carpool", {}).get("drivers", [])

        for leg in event.get("eventLegs", []):
            try:
                leg_time_utc = datetime.fromisoformat(
                    leg["dateTime"].replace("Z", "").replace(".000", "")
                ).replace(tzinfo=timezone.utc)
                leg_time_local = leg_time_utc.astimezone(local_tz)

                # Get driver info
                driver = leg.get("driver", {})
                if not driver:
                    driver_id = leg.get("driverId")
                    if driver_id:
                        driver = next(
                            (d for d in carpool_drivers if d.get("id") == driver_id),
                            {},
                        )

                driver_name = (
                    f"{driver.get('firstName', 'Unknown')} {driver.get('lastName', '')}"
                )

                riders = []
                for rider in leg.get("riders", []):
                    kid = rider.get("kid", {})
                    parent_name = self._find_parent_name(
                        kid.get("parentId", ""), carpool_drivers
                    )
                    riders.append({"name": kid.get("name", "Unknown"), "parent": parent_name})

                processed_legs.append(
                    {
                        "time": leg_time_local.strftime("%H:%M"),
                        "time_formatted": leg_time_local.strftime("%I:%M %p"),
                        "driver_name": driver_name,
                        "driver_seats": driver.get("seatCount", 0),
                        "riders": riders,
                        "rider_count": len(riders),
                    }
                )
            except Exception as err:
                _LOGGER.error("Error processing leg: %s", err)
                continue

        # Sort legs by time to ensure earliest time appears first
        processed_legs.sort(key=lambda x: x["time"])

        return {
            "date": event_date.strftime("%Y-%m-%d"),
            "day_name": event_date.strftime("%A"),
            "location": event.get("location", "Unknown"),
            "legs": processed_legs,
            "total_legs": len(processed_legs),
        }

    def _find_parent_name(self, parent_id: str, drivers: list[dict[str, Any]]) -> str:
        """Find parent name from driver list."""
        for driver in drivers:
            if driver.get("id") == parent_id:
                return f"{driver.get('firstName', 'Unknown')} {driver.get('lastName', '')}"
        return "Unknown"

    def update(self) -> dict[str, Any]:
        """Update data from API."""
        _LOGGER.debug("Starting carpool data update...")

        # Get Google token
        google_token = self._authenticate_google()
        if not google_token:
            _LOGGER.error("Google authentication failed")
            raise Exception("Failed to authenticate with Google")

        # Get carpool token
        carpool_token = self._get_carpool_token(google_token)
        if not carpool_token:
            _LOGGER.error("Carpool authentication failed")
            raise Exception("Failed to get carpool token")

        # Get events
        events_data = self._get_events(carpool_token)
        if events_data is None:
            _LOGGER.error("Failed to get events data")
            raise Exception("Failed to get events data")

        # Process events
        self.data = self._process_events(events_data)
        _LOGGER.debug("Carpool data update completed successfully")

        return self.data
