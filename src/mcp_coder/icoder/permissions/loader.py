"""I/O loader for iCoder ``.icoder/`` permission settings (JSONC → model).

This module is the only member of the permissions package permitted to touch
``json``/``jsonschema`` and the filesystem; ``model``/``matcher``/``resolver``
stay pure. It reads the layered ``settings.json`` files, validates them, and
builds the in-memory :class:`~mcp_coder.icoder.permissions.model.PermissionConfig`
the resolver consumes.

Step 2 provides only :func:`_strip_jsonc`, the string/escape-aware JSONC
preprocessor. It is a security surface: comment-like sequences inside string
literals (URLs, ``"a // b"``, escaped quotes) must survive intact.

Step 3 adds the schema surface: one static :func:`build_settings_schema` dict
that serves both :func:`_schema_errors` validation (structure + enums only —
matcher grammar stays with ``parse_matcher``) and the editor-hint file written
by the gated :func:`emit_schema`. ``_POLICY_BY_TOKEN`` is the single source for
the Claude-style token vocabulary shared by rules, ``defaultMode``, and the
schema enum.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from mcp_coder.icoder.permissions.model import Policy

_POLICY_BY_TOKEN: dict[str, Policy] = {
    "allow": Policy.ALWAYS,
    "ask": Policy.AFTER_APPROVAL,
    "deny": Policy.NEVER,
}


def _strip_jsonc(text: str) -> str:
    """Strip // and /* */ comments and trailing commas from JSONC text.

    String/escape-aware: comment markers and commas inside string literals
    are preserved.

    Args:
        text: The JSONC source to preprocess.

    Returns:
        A comment-free, trailing-comma-free JSON string suitable for
        ``json.loads``.
    """
    out: list[str] = []
    i = 0
    n = len(text)
    in_str = False
    esc = False
    while i < n:
        c = text[i]
        peek = text[i + 1] if i + 1 < n else ""
        if in_str:
            # Inside "...": copy verbatim, tracking backslash escapes so an
            # escaped quote (\") does not close the string.
            out.append(c)
            esc = c == "\\" and not esc
            in_str = c != '"' or esc
        elif c == '"':
            in_str = True
            out.append(c)
        elif c == "/" and peek == "/":
            # Line comment: skip to (but keep) the newline.
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif c == "/" and peek == "*":
            # Block comment: skip through the closing */.
            i += 2
            while i < n and not (text[i] == "*" and i + 1 < n and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        elif c in "}]":
            # Drop a trailing comma sitting before this closing bracket,
            # skipping any whitespace already emitted between them.
            j = len(out) - 1
            while j >= 0 and out[j].isspace():
                j -= 1
            if j >= 0 and out[j] == ",":
                del out[j]
            out.append(c)
        else:
            out.append(c)
        i += 1
    return "".join(out)


def build_settings_schema() -> dict[str, object]:
    """Return the JSON Schema for the on-disk ``settings.json`` format.

    One static dict serves both :func:`_schema_errors` validation and the
    emitted editor-hint file. Depth is structure + enums only: matcher-string
    grammar is delegated to ``parse_matcher`` (single source of truth).

    Returns:
        A Draft-7 JSON-Schema dict.
    """
    string_array: dict[str, object] = {"type": "array", "items": {"type": "string"}}
    name_to_string_array: dict[str, object] = {
        "type": "object",
        "additionalProperties": string_array,
    }
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "$schema": {"type": "string"},
            "defaultMode": {"enum": list(_POLICY_BY_TOKEN)},
            "allow": string_array,
            "ask": string_array,
            "deny": string_array,
            "toolGroups": name_to_string_array,
            "toolScenarios": name_to_string_array,
        },
    }


def _schema_errors(data: object) -> list[str]:
    """Return human-readable schema-violation messages (``[]`` if valid).

    Wraps ``jsonschema`` validation and returns messages as data (no raise);
    each message names the offending key/value via its JSON path.

    Args:
        data: The parsed settings object to validate.

    Returns:
        A list of ``"<json_path>: <message>"`` strings; empty when valid.
    """
    validator = jsonschema.Draft7Validator(build_settings_schema())
    return [f"{e.json_path}: {e.message}" for e in validator.iter_errors(data)]


def emit_schema(project_dir: Path) -> bool:
    """Write ``settings.schema.json`` into ``<project_dir>/.icoder/``.

    Gated: writes only when ``.icoder/`` already exists (no dir creation) and
    only when the content would change (no git churn).

    Args:
        project_dir: The project root whose ``.icoder/`` directory receives
            the emitted schema.

    Returns:
        ``True`` if a file was written, ``False`` otherwise.
    """
    icoder = project_dir / ".icoder"
    if not icoder.is_dir():
        return False
    target = icoder / "settings.schema.json"
    new = json.dumps(build_settings_schema(), indent=2) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") == new:
        return False
    target.write_text(new, encoding="utf-8")
    return True
