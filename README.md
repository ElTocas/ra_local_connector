# ra_local_connector

A local [MCP](https://modelcontextprotocol.io) server that lets Claude search and organise electronic-music event data: events, venues (with address), cities, genres and ordered lineups (with set times when known).

It runs on your own machine over stdio, keeps everything in a local SQLite cache, and exposes a handful of tools:

| Tool | What it does |
| --- | --- |
| `refresh_events(city, date_from, date_to)` | Loads events from the configured provider into the local cache |
| `search_events(city, date_from, date_to, genre, artist, venue, limit)` | Filters cached events, results include venue, genres and lineup |
| `get_event(event_id)` | Full details of one event |
| `list_cities()` | Cities in the cache, with event counts |

## Status and data source

This project is an independent, unofficial prototype and is not affiliated with Resident Advisor.

The only bundled provider is `sample`, which serves a few **fictional** events so the connector can be developed and tried end to end. No provider that reads real listings from ra.co is included: [RA's Terms of Use](https://ra.co/terms) prohibit automated access to the site without prior written authorisation, so that part waits for explicit permission or an official API. The data source sits behind a small interface (`providers/base.py`), so adding one later does not touch the rest of the code.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Use with Claude

Claude Desktop and Claude Code can start local MCP servers. Add this to the MCP configuration, using the full path of the Python inside your virtual environment:

```json
{
  "mcpServers": {
    "ra-local-connector": {
      "command": "/path/to/ra_local_connector/.venv/bin/python",
      "args": ["-m", "ra_local_connector"],
      "env": { "RA_PROVIDER": "sample" }
    }
  }
}
```

Then ask Claude, for example: "refresh events for Rome from 2026-11-01 to 2026-11-30, then show me the techno nights with Example One in the lineup".

Environment variables: `RA_PROVIDER` (default `sample`) and `RA_CONNECTOR_DB` (default `~/.ra_local_connector/events.sqlite3`).

## Data model

An event has a title, start and end time, a venue (name, address, city, country), a list of genres, a price, a link and an ordered lineup. Each lineup slot is an artist with a position and an optional set start time. Venues and artists are stored once and referenced by id.

## License

MIT
