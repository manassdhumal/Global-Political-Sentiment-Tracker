"""Load and validate the watchlist configuration.

The watchlist (config/watchlist.yaml) is the single source of truth for
what the system tracks. Pipeline code must go through this module rather
than hardcoding any country/entity/theme name.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

# Project root = two levels up from this file (src/config.py -> project/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "watchlist.yaml"
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "config" / "events.csv"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "sentiment.db"


@dataclass(frozen=True)
class Country:
    name: str
    gdelt: str   # code used in GDELT `sourcecountry:` filter (FIPS 10-4 style)
    iso3: str    # ISO-3166 alpha-3, for the Phase 2 choropleth


@dataclass(frozen=True)
class Entity:
    id: str
    name: str
    type: str                       # figure | party | theme
    query: str                      # GDELT DOC 2.0 query fragment
    home_country: Optional[str] = None
    aliases: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Watchlist:
    meta: dict
    countries: list[Country]
    entities: list[Entity]

    # -- convenience lookups -------------------------------------------
    def country_by_gdelt(self, code: str) -> Optional[Country]:
        return next((c for c in self.countries if c.gdelt == code), None)

    def entity_by_id(self, entity_id: str) -> Optional[Entity]:
        return next((e for e in self.entities if e.id == entity_id), None)

    @property
    def entity_ids(self) -> list[str]:
        return [e.id for e in self.entities]

    @property
    def gdelt_country_codes(self) -> list[str]:
        return [c.gdelt for c in self.countries]

    @property
    def name_by_gdelt(self) -> dict[str, str]:
        return {c.gdelt: c.name for c in self.countries}

    @property
    def iso3_by_gdelt(self) -> dict[str, str]:
        return {c.gdelt: c.iso3 for c in self.countries}

    @property
    def name_by_entity(self) -> dict[str, str]:
        return {e.id: e.name for e in self.entities}


_VALID_ENTITY_TYPES = {"figure", "party", "theme"}


def load_watchlist(path: str | Path = DEFAULT_CONFIG_PATH) -> Watchlist:
    """Parse and validate the watchlist YAML into typed objects.

    Raises ValueError with an actionable message on malformed config so a
    typo in the watchlist fails loudly rather than silently mis-tracking.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Watchlist config not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    meta = raw.get("meta", {})

    # --- countries ---
    countries: list[Country] = []
    for i, c in enumerate(raw.get("countries", [])):
        for key in ("name", "gdelt", "iso3"):
            if not c.get(key):
                raise ValueError(f"countries[{i}] missing required key '{key}'")
        countries.append(Country(name=c["name"], gdelt=c["gdelt"], iso3=c["iso3"]))
    if not countries:
        raise ValueError("Watchlist must define at least one country.")

    # --- entities ---
    entities: list[Entity] = []
    seen_ids: set[str] = set()
    for i, e in enumerate(raw.get("entities", [])):
        for key in ("id", "name", "type", "query"):
            if not e.get(key):
                raise ValueError(f"entities[{i}] missing required key '{key}'")
        if e["type"] not in _VALID_ENTITY_TYPES:
            raise ValueError(
                f"entities[{i}] ('{e['id']}') has invalid type '{e['type']}'. "
                f"Must be one of {sorted(_VALID_ENTITY_TYPES)}."
            )
        if e["id"] in seen_ids:
            raise ValueError(f"Duplicate entity id '{e['id']}' in watchlist.")
        seen_ids.add(e["id"])
        entities.append(
            Entity(
                id=e["id"],
                name=e["name"],
                type=e["type"],
                query=e["query"],
                home_country=e.get("home_country"),
                aliases=list(e.get("aliases") or []),
            )
        )
    if not entities:
        raise ValueError("Watchlist must define at least one entity.")

    return Watchlist(meta=meta, countries=countries, entities=entities)


@dataclass(frozen=True)
class Event:
    """A known event rendered as a marker on timeline charts."""
    date: str          # YYYY-MM-DD
    scope_type: str    # entity | country | global
    scope_id: str      # entity id / GDELT country code / "" for global
    label: str

    def applies_to(self, *, entity_id: str | None = None,
                   country: str | None = None) -> bool:
        """Does this event belong on a chart scoped to entity/country?"""
        if self.scope_type == "global":
            return True
        if self.scope_type == "entity":
            return entity_id is not None and self.scope_id == entity_id
        if self.scope_type == "country":
            return country is not None and self.scope_id == country
        return False


def load_events(path: str | Path = DEFAULT_EVENTS_PATH) -> list[Event]:
    """Load the event annotation layer from CSV (skips '#' comment lines)."""
    path = Path(path)
    if not path.exists():
        return []
    events: list[Event] = []
    with path.open("r", encoding="utf-8") as fh:
        rows = (line for line in fh if not line.lstrip().startswith("#"))
        for r in csv.DictReader(rows):
            if not r.get("date"):
                continue
            try:
                datetime.strptime(r["date"].strip(), "%Y-%m-%d")
            except ValueError:
                continue  # skip malformed dates rather than crash
            events.append(Event(
                date=r["date"].strip(),
                scope_type=(r.get("scope_type") or "global").strip(),
                scope_id=(r.get("scope_id") or "").strip(),
                label=(r.get("label") or "").strip(),
            ))
    return events


if __name__ == "__main__":  # quick manual sanity check
    wl = load_watchlist()
    print(f"Loaded {len(wl.countries)} countries, {len(wl.entities)} entities.")
    print("Countries:", ", ".join(c.name for c in wl.countries))
    print("Entities :", ", ".join(f"{e.id}({e.type})" for e in wl.entities))
    print(f"Events   : {len(load_events())} loaded")
