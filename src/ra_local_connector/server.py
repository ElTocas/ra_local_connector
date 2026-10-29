"""MCP server (stdio). Claude starts this process locally and calls its tools."""

from __future__ import annotations

import os
from contextlib import closing
from pathlib import Path

try:  # mcp >= 2: FastMCP was renamed MCPServer
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server

from . import db
from .providers import get_provider

mcp = _Server("ra-local-connector")


def _db_path() -> Path:
    default = Path.home() / ".ra_local_connector" / "events.sqlite3"
    path = Path(os.environ.get("RA_CONNECTOR_DB", default))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@mcp.tool()
def refresh_events(city: str, date_from: str, date_to: str) -> dict:
    """Load events for a city and date range (YYYY-MM-DD) from the configured
    provider into the local cache. Call this before searching a new city or period."""
    provider = get_provider(os.environ.get("RA_PROVIDER", "sample"))
    events = provider.fetch_events(city, date_from, date_to)
    with closing(db.connect(_db_path())) as conn:
        for ev in events:
            db.upsert_event(conn, ev)
    return {"provider": provider.name, "city": city, "events_cached": len(events)}


@mcp.tool()
def search_events(
    city: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    genre: str | None = None,
    artist: str | None = None,
    venue: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search cached events. Dates are YYYY-MM-DD (inclusive). Each result has the
    venue with address, genres and the ordered lineup with set times when known."""
    with closing(db.connect(_db_path())) as conn:
        return db.search_events(conn, city, date_from, date_to, genre, artist, venue, limit)


@mcp.tool()
def get_event(event_id: str) -> dict:
    """Full details of one cached event by id."""
    with closing(db.connect(_db_path())) as conn:
        ev = db.get_event(conn, event_id)
    return ev if ev else {"error": f"No cached event with id '{event_id}'"}


@mcp.tool()
def list_cities() -> list[dict]:
    """Cities currently in the local cache, with how many events each has."""
    with closing(db.connect(_db_path())) as conn:
        return db.list_cities(conn)


def main() -> None:
    mcp.run()  # stdio transport


if __name__ == "__main__":
    main()
