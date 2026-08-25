"""Hints for unrecognised configuration keys.

Two helpers back the diagnostics that `mcp-coder verify` prints for config
keys it does not know:

- an explicit per-section rename table, for renames that edit distance cannot
  connect (`endpoint` -> `base_url`), and
- a generic near-miss suggestion built on difflib.

`suggest` is deliberately free of config-specific knowledge so other
near-miss checks (e.g. model names) can reuse it.
"""

import difflib
from collections.abc import Iterable

# Renames edit distance cannot find: (section, retired key) -> explanation.
_RENAME_HINTS: dict[tuple[str, str], str] = {
    ("llm.langchain", "endpoint"): "renamed to base_url",
}

# difflib similarity below which a candidate is not worth suggesting.
_CUTOFF = 0.6


def suggest(name: str, candidates: Iterable[str]) -> str | None:
    """Return the closest candidate to name, or None when nothing is close.

    Args:
        name: The name to find a near-miss for
        candidates: Known names to compare against

    Returns:
        The closest candidate, or None if none is similar enough
    """
    matches = difflib.get_close_matches(name, list(candidates), n=1, cutoff=_CUTOFF)
    return matches[0] if matches else None


def unknown_key_hint(section: str, key: str, known_keys: Iterable[str]) -> str | None:
    """Return an explanatory suffix for an unknown config key, or None.

    A retired key listed in the rename table gets its explicit explanation;
    anything else falls back to a near-miss suggestion.

    Args:
        section: Config section name (e.g. 'llm.langchain')
        key: The unknown key found in that section
        known_keys: Keys the section's schema defines

    Returns:
        Hint text to append to the warning, or None when there is nothing
        useful to say
    """
    rename = _RENAME_HINTS.get((section, key))
    if rename is not None:
        return rename

    match = suggest(key, known_keys)
    return f"did you mean {match}?" if match else None
