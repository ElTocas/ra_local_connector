import pytest

from ra_local_connector import db
from ra_local_connector.providers import get_provider


@pytest.fixture()
def conn(tmp_path):
    c = db.connect(tmp_path / "test.sqlite3")
    provider = get_provider("sample")
    for city in ("Rome", "Berlin"):
        for ev in provider.fetch_events(city, "2026-01-01", "2026-12-31"):
            db.upsert_event(c, ev)
    yield c
    c.close()


def test_filter_by_city_and_dates(conn):
    rome = db.search_events(conn, city="rome")
    assert [e["id"] for e in rome] == ["sample-001", "sample-002", "sample-004"]
    week = db.search_events(conn, city="Rome", date_from="2026-11-06", date_to="2026-11-08")
    assert [e["id"] for e in week] == ["sample-001", "sample-002"]


def test_filter_by_genre_artist_venue(conn):
    assert [e["id"] for e in db.search_events(conn, genre="House")] == ["sample-002"]
    by_artist = db.search_events(conn, artist="example one")
    assert [e["id"] for e in by_artist] == ["sample-001", "sample-003"]
    assert len(db.search_events(conn, venue="warehouse")) == 2


def test_lineup_order_and_set_times(conn):
    ev = db.get_event(conn, "sample-001")
    assert [s["artist"] for s in ev["lineup"]] == ["Example One", "Example Two", "Example Three"]
    assert [s["set_start"] for s in ev["lineup"]] == ["23:00", "01:00", "03:30"]
    assert ev["venue"]["address"] == "Via Esempio 1"
    assert ev["genres"] == ["industrial", "techno"]


def test_upsert_is_idempotent(conn):
    provider = get_provider("sample")
    for ev in provider.fetch_events("Rome", "2026-01-01", "2026-12-31"):
        db.upsert_event(conn, ev)
    assert len(db.search_events(conn, city="Rome")) == 3
    cities = {c["city"]: c["events"] for c in db.list_cities(conn)}
    assert cities == {"Rome": 3, "Berlin": 1}


def test_unknown_event_and_provider(conn):
    assert db.get_event(conn, "nope") is None
    with pytest.raises(ValueError):
        get_provider("ra")
