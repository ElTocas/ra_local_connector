"""SQLite cache: stores events locally so the source is queried rarely."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Event

SCHEMA = """
CREATE TABLE IF NOT EXISTS venues (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    address TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS artists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT,
    venue_id TEXT NOT NULL REFERENCES venues(id),
    url TEXT NOT NULL DEFAULT '',
    price TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS event_genres (
    event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    genre TEXT NOT NULL,
    PRIMARY KEY (event_id, genre)
);
CREATE TABLE IF NOT EXISTS lineup (
    event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    artist_id TEXT NOT NULL REFERENCES artists(id),
    set_start TEXT,
    PRIMARY KEY (event_id, position)
);
CREATE INDEX IF NOT EXISTS idx_events_starts_at ON events(starts_at);
CREATE INDEX IF NOT EXISTS idx_lineup_artist ON lineup(artist_id);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def upsert_event(conn: sqlite3.Connection, ev: Event) -> None:
    v = ev.venue
    conn.execute(
        "INSERT INTO venues (id, name, city, country, address) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET name=excluded.name, city=excluded.city, "
        "country=excluded.country, address=excluded.address",
        (v.id, v.name, v.city, v.country, v.address),
    )
    conn.execute(
        "INSERT INTO events (id, title, starts_at, ends_at, venue_id, url, price) "
        "VALUES (?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET title=excluded.title, starts_at=excluded.starts_at, "
        "ends_at=excluded.ends_at, venue_id=excluded.venue_id, url=excluded.url, "
        "price=excluded.price",
        (ev.id, ev.title, ev.starts_at, ev.ends_at, v.id, ev.url, ev.price),
    )
    conn.execute("DELETE FROM event_genres WHERE event_id = ?", (ev.id,))
    conn.executemany(
        "INSERT INTO event_genres (event_id, genre) VALUES (?, ?)",
        [(ev.id, g) for g in ev.genres],
    )
    conn.execute("DELETE FROM lineup WHERE event_id = ?", (ev.id,))
    for slot in ev.lineup:
        conn.execute(
            "INSERT INTO artists (id, name) VALUES (?, ?) "
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name",
            (slot.artist.id, slot.artist.name),
        )
        conn.execute(
            "INSERT INTO lineup (event_id, position, artist_id, set_start) VALUES (?, ?, ?, ?)",
            (ev.id, slot.position, slot.artist.id, slot.set_start),
        )
    conn.commit()


def _hydrate(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    genres = [
        r["genre"]
        for r in conn.execute(
            "SELECT genre FROM event_genres WHERE event_id = ? ORDER BY genre", (row["id"],)
        )
    ]
    lineup = [
        {"position": r["position"], "artist": r["name"], "set_start": r["set_start"]}
        for r in conn.execute(
            "SELECT l.position, a.name, l.set_start FROM lineup l "
            "JOIN artists a ON a.id = l.artist_id WHERE l.event_id = ? ORDER BY l.position",
            (row["id"],),
        )
    ]
    return {
        "id": row["id"],
        "title": row["title"],
        "starts_at": row["starts_at"],
        "ends_at": row["ends_at"],
        "venue": {
            "name": row["venue_name"],
            "address": row["venue_address"],
            "city": row["venue_city"],
            "country": row["venue_country"],
        },
        "genres": genres,
        "lineup": lineup,
        "url": row["url"],
        "price": row["price"],
    }


_SELECT = (
    "SELECT e.id, e.title, e.starts_at, e.ends_at, e.url, e.price, "
    "v.name AS venue_name, v.address AS venue_address, v.city AS venue_city, "
    "v.country AS venue_country "
    "FROM events e JOIN venues v ON v.id = e.venue_id"
)


def search_events(
    conn: sqlite3.Connection,
    city: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    genre: str | None = None,
    artist: str | None = None,
    venue: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Filter events. Dates are YYYY-MM-DD (inclusive); text filters are case-insensitive."""
    where: list[str] = []
    params: list = []
    if city:
        where.append("LOWER(v.city) = LOWER(?)")
        params.append(city)
    if date_from:
        where.append("substr(e.starts_at, 1, 10) >= ?")
        params.append(date_from)
    if date_to:
        where.append("substr(e.starts_at, 1, 10) <= ?")
        params.append(date_to)
    if genre:
        where.append(
            "EXISTS (SELECT 1 FROM event_genres g WHERE g.event_id = e.id "
            "AND LOWER(g.genre) = LOWER(?))"
        )
        params.append(genre)
    if artist:
        where.append(
            "EXISTS (SELECT 1 FROM lineup l JOIN artists a ON a.id = l.artist_id "
            "WHERE l.event_id = e.id AND LOWER(a.name) LIKE LOWER(?))"
        )
        params.append(f"%{artist}%")
    if venue:
        where.append("LOWER(v.name) LIKE LOWER(?)")
        params.append(f"%{venue}%")
    sql = _SELECT + (" WHERE " + " AND ".join(where) if where else "")
    sql += " ORDER BY e.starts_at LIMIT ?"
    params.append(max(1, min(limit, 100)))
    return [_hydrate(conn, r) for r in conn.execute(sql, params)]


def get_event(conn: sqlite3.Connection, event_id: str) -> dict | None:
    row = conn.execute(_SELECT + " WHERE e.id = ?", (event_id,)).fetchone()
    return _hydrate(conn, row) if row else None


def list_cities(conn: sqlite3.Connection) -> list[dict]:
    return [
        {"city": r["city"], "country": r["country"], "events": r["n"]}
        for r in conn.execute(
            "SELECT v.city, v.country, COUNT(*) AS n FROM events e "
            "JOIN venues v ON v.id = e.venue_id GROUP BY v.city, v.country ORDER BY n DESC"
        )
    ]
