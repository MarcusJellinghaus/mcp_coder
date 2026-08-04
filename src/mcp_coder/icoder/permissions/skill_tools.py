"""Pure parser for a skill's rich ``tools:`` frontmatter block.

The structural half of the ``skill -> PermissionFrame`` bridge. It records
**raw strings only** — no ``Matcher``/``PermissionFrame``, no token semantics
(those live in ``skill_frame.py``). This module imports nothing project-side
so ``permissions/`` stays a leaf and parsing is callable without ``load_skills``.

The frontmatter key is ``tools``. An **absent** key (not present in the
mapping) is the sole fail-open case and returns ``None``. A **present-but-null**
``tools:`` (YAML parses the empty value to ``None``) is *malformed*, not absent
— hence the membership test rather than ``Mapping.get``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

_VALID_BASES = ("inherit", "none")


@dataclass(frozen=True)
class SkillToolsBlock:
    """A skill's parsed ``tools:`` block — raw strings, no semantics.

    Attributes:
        base: ``"inherit"``/``"none"``, or ``None`` for a bare-``use:`` or
            malformed block.
        allow: Raw allow tokens, verbatim.
        deny: Raw deny tokens, verbatim (including ``@ref`` entries).
        use: A block-level ``use: name`` reference, else ``None``.
        errors: Fatal structural mistakes; a non-empty tuple blocks the skill.
        advisories: Lint notes for non-``mcp__`` tokens in a rich block; never
            affects runtime.
    """

    base: str | None
    allow: tuple[str, ...] = ()
    deny: tuple[str, ...] = ()
    use: str | None = None
    errors: tuple[str, ...] = ()
    advisories: tuple[str, ...] = ()


def _parse_token_list(
    raw: Mapping[str, object], key: str, errors: list[str]
) -> list[str]:
    """Return ``raw[key]`` as a list of strings, recording errors on mismatch.

    A scalar (non-list) value or any non-string item is a fatal mistake: the
    error is recorded and an **empty** list returned, so no non-string item is
    ever carried forward (keeping ``.startswith`` total downstream).

    Returns:
        The verbatim token list, or ``[]`` when the value is malformed/absent.
    """
    if key not in raw:
        return []
    value = raw[key]
    if not isinstance(value, list):
        errors.append(f"{key}: must be a list of tool tokens")
        return []
    if not all(isinstance(item, str) for item in value):
        errors.append(f"{key}: items must be strings")
        return []
    return list(value)


def parse_tools_block(meta: Mapping[str, object]) -> SkillToolsBlock | None:
    """Parse a skill's ``tools:`` frontmatter block into a ``SkillToolsBlock``.

    Args:
        meta: The skill's parsed frontmatter mapping.

    Returns:
        ``None`` when the ``tools`` key is absent (fail-open). Otherwise a
        ``SkillToolsBlock``: with non-empty ``errors`` for a malformed block,
        with ``use`` set for a bare-``use:`` block, or with ``base``/``allow``/
        ``deny`` populated for a valid rich block.
    """
    if "tools" not in meta:
        return None  # ABSENT — the only fail-open case (key not present)

    raw = meta["tools"]
    # Present-but-null / list / scalar / empty mapping are all MALFORMED.
    if raw is None or not isinstance(raw, Mapping) or not raw:
        return SkillToolsBlock(
            base=None, errors=("tools: must be a non-empty mapping",)
        )

    base: str | None = None
    allow: list[str] = []
    deny: list[str] = []
    use_val: str | None = None
    errors: list[str] = []

    use = raw.get("use")
    has_inline = any(key in raw for key in ("base", "allow", "deny"))
    if use is not None and has_inline:
        use_val = str(use)
        errors.append("use: cannot combine with base/allow/deny")
    elif use is not None:
        return SkillToolsBlock(base=None, use=str(use))  # bare use → blocked in Step 2
    else:
        base_raw = raw.get("base")
        if base_raw in _VALID_BASES:
            base = str(base_raw)
        else:
            errors.append("base: must be 'inherit' or 'none'")
        allow = _parse_token_list(raw, "allow", errors)
        deny = _parse_token_list(raw, "deny", errors)

    advisories = [
        token for token in allow + deny if not token.startswith(("mcp__", "@"))
    ]
    return SkillToolsBlock(
        base,
        tuple(allow),
        tuple(deny),
        use_val,
        tuple(errors),
        tuple(advisories),
    )
