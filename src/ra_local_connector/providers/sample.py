"""Provider backed by a small bundled file of FICTIONAL events (for development)."""

from __future__ import annotations

import json
from pathlib import Path

from ..models import Event, event_from_dict

_DATA = Path(__file__).with_name("sample_events.json")


class SampleProvider:
    name = "sample"

    def fetch_events(self, city: str, date_from: str, date_to: str) -> list[Event]:
        raw = json.loads(_DATA.read_text(encoding="utf-8"))
        events = [event_from_dict(d) for d in raw]
        return [
            e
            for e in events
            if e.venue.city.lower() == city.lower()
            and date_from <= e.starts_at[:10] <= date_to
        ]
