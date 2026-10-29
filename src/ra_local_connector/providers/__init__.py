"""Event providers: where the data comes from.

The server only talks to the `EventProvider` interface. Only the `sample`
provider (fictional data) is bundled. A provider that reads real listings from
Resident Advisor is deliberately NOT included: RA's Terms of Use forbid
automated access without prior written authorisation. If RA grants permission
(or offers an official API), add a new provider here and select it with the
RA_PROVIDER environment variable.
"""

from __future__ import annotations

from .base import EventProvider
from .sample import SampleProvider


def get_provider(name: str) -> EventProvider:
    if name == "sample":
        return SampleProvider()
    raise ValueError(
        f"Unknown provider '{name}'. Only 'sample' (fictional data) is bundled; "
        "see ra_local_connector/providers/__init__.py."
    )
