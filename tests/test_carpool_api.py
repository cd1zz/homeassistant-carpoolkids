"""Tests for event time handling in the Carpool Kids API client."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from carpool_kids import carpool_api
from carpool_kids.carpool_api import CarpoolAPI

DENVER = "America/Denver"


def leg(ts):
    return {"dateTime": ts, "riders": []}


def event(ts, *leg_times, location="School"):
    return {"dateTime": ts, "location": location, "eventLegs": [leg(t) for t in leg_times]}


@pytest.fixture
def api():
    return CarpoolAPI("user@example.com", "android", "token", DENVER)


@pytest.fixture
def frozen_now(monkeypatch):
    """Freeze "now" at 2026-11-09 18:00 Mountain (2026-11-10 01:00 UTC)."""

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            moment = cls(2026, 11, 10, 1, 0, tzinfo=ZoneInfo("UTC"))
            return moment.astimezone(tz) if tz else moment.replace(tzinfo=None)

    monkeypatch.setattr(carpool_api, "datetime", FrozenDatetime)


def test_leg_times_are_converted_to_local(api):
    processed = api._process_single_event(
        event("2026-11-09T15:25:00.000Z", "2026-11-09T15:25:00.000Z")
    )
    assert processed["legs"][0]["time_formatted"] == "08:25 AM"
    assert processed["date"] == "2026-11-09"
    assert processed["day_name"] == "Monday"


def test_legs_sorted_earliest_first(api):
    processed = api._process_single_event(
        event(
            "2026-11-12T15:25:00.000Z",
            "2026-11-12T22:45:00.000Z",
            "2026-11-12T15:25:00.000Z",
        )
    )
    assert [l["time_formatted"] for l in processed["legs"]] == ["08:25 AM", "03:45 PM"]


def test_evening_event_keeps_local_date(api):
    # 5:30 PM Mountain on the 9th is already the 10th in UTC.
    processed = api._process_single_event(
        event("2026-11-10T00:30:00.000Z", "2026-11-10T00:30:00.000Z")
    )
    assert processed["date"] == "2026-11-09"
    assert processed["legs"][0]["time_formatted"] == "05:30 PM"


def test_midnight_utc_event_without_legs_is_date_only(api):
    processed = api._process_single_event(event("2026-11-13T00:00:00.000Z"))
    assert processed["date"] == "2026-11-13"


def test_evening_event_is_bucketed_as_today(api, frozen_now):
    data = api._process_events(
        [
            event("2026-11-10T00:30:00.000Z", "2026-11-10T00:30:00.000Z"),
            event("2026-11-10T15:25:00.000Z", "2026-11-10T15:25:00.000Z"),
        ]
    )
    assert [e["date"] for e in data["today"]] == ["2026-11-09"]
    assert [e["date"] for e in data["upcoming"]] == ["2026-11-10"]
    assert data["next_event"]["date"] == "2026-11-09"


def test_event_list_skips_past_events(api, frozen_now):
    data = api._process_events(
        [
            event("2026-11-08T15:25:00.000Z", "2026-11-08T15:25:00.000Z"),
            event("2026-11-10T15:25:00.000Z", "2026-11-10T15:25:00.000Z"),
        ]
    )
    assert [e["date"] for e in data["event_list"]] == ["2026-11-10"]


def test_empty_payload(api):
    data = api._process_events([])
    assert data["today"] == [] and data["event_list"] == [] and data["next_event"] is None
