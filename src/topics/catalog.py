"""Topic catalog + open-ended query resolution."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from ..config import PROJECT_ROOT

DEFAULT_TOPICS_PATH = PROJECT_ROOT / "config" / "topics.yaml"


@dataclass(frozen=True)
class Topic:
    id: str          # slug
    label: str
    query: str
    category: str
    custom: bool = False


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")
    return s or "topic"


@lru_cache(maxsize=1)
def load_catalog(path: str | Path = DEFAULT_TOPICS_PATH) -> list[Topic]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    out: list[Topic] = []
    for t in raw.get("topics", []):
        out.append(Topic(id=t["id"], label=t["label"], query=t["query"],
                         category=t.get("category", "issue")))
    return out


@lru_cache(maxsize=1)
def _by_id() -> dict[str, Topic]:
    return {t.id: t for t in load_catalog()}


def categories() -> list[str]:
    raw = yaml.safe_load(DEFAULT_TOPICS_PATH.read_text(encoding="utf-8")) or {}
    return raw.get("categories", sorted({t.category for t in load_catalog()}))


def resolve_topic(q: str) -> Topic:
    """Resolve a slug or free-text query to a Topic.

    Matches a catalog topic by id or (case-insensitive) label; otherwise
    returns a CUSTOM topic so any query can be analysed on demand.
    """
    q = (q or "").strip()
    if not q:
        raise ValueError("empty topic query")
    if q in _by_id():
        return _by_id()[q]
    ql = q.lower()
    for t in load_catalog():
        if t.label.lower() == ql or t.id == slugify(q):
            return t
    return Topic(id=slugify(q), label=q, query=q, category="custom", custom=True)
