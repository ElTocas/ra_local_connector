"""Data model: events, venues, artists and ordered lineups."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Artist:
    id: str
    name: str


@dataclass(frozen=True)
class Venue:
    id: str
    name: str
    city: str
    country: str
    address: str = ""


@dataclass(frozen=True)
class LineupSlot:
    """One artist in an event lineup. `position` is the running order (0-based)."""

    artist: Artist
    position: int
    set_start: str | None = None  # "HH:MM" when the set time is known


@dataclass(frozen=True)
class Event:
    id: str
    title: str
    starts_at: str  # ISO 8601 local datetime, e.g. "2026-11-06T23:00"
    ends_at: str | None
    venue: Venue
    genres: tuple[str, ...] = ()
    lineup: tuple[LineupSlot, ...] = ()
    url: str = ""
    price: str = ""  # free text as published, e.g. "EUR 15"


def event_from_dict(d: dict) -> Event:
    """Build an Event from a plain dict (used by providers and fixtures)."""
    v = d["venue"]
    venue = Venue(
        id=v["id"],
        name=v["name"],
        city=v["city"],
        country=v["country"],
        address=v.get("address", ""),
    )
    lineup = tuple(
        LineupSlot(
            artist=Artist(id=s["artist"]["id"], name=s["artist"]["name"]),
            position=i,
            set_start=s.get("set_start"),
        )
        for i, s in enumerate(d.get("lineup", []))
    )
    return Event(
        id=d["id"],
        title=d["title"],
        starts_at=d["starts_at"],
        ends_at=d.get("ends_at"),
        venue=venue,
        genres=tuple(d.get("genres", [])),
        lineup=lineup,
        url=d.get("url", ""),
        price=d.get("price", ""),
    )
