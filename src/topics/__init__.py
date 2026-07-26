"""Topic layer (v3): open-ended, on-demand topic analysis.

Any free-text topic can be analysed on demand — the curated catalog
(config/topics.yaml) is just the browse/trending pool, not a hard limit.
All values are MEDIA + SOCIAL sentiment, never public opinion.
"""
from .catalog import Topic, load_catalog, resolve_topic, slugify  # noqa: F401
from .analyze import analyze_topic  # noqa: F401
from .trending import trending, global_snapshot  # noqa: F401
