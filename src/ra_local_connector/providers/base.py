from __future__ import annotations

from typing import Protocol

from ..models import Event


class EventProvider(Protocol):
    """A source of event listings."""

    name: str

    def fetch_events(self, city: str, date_from: str, date_to: str) -> list[Event]:
        """Return events in `city` between two YYYY-MM-DD dates (inclusive)."""
        ...
