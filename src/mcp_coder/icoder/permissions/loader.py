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

Step 4 adds :func:`_discover_layers`, which locates the three ``.icoder/``
settings files in precedence order (``user``, ``project``, ``local``), skips
absent layers silently, resolves each to an absolute path (so ``Rule.source_path``
provenance is absolute), and never touches ``.claude/*``.

Step 5 adds :func:`_parse_matchers` and :func:`_load_layer`. The former parses a
single matcher token, pre-detecting ``@ref`` members (unsupported until I4.1)
before delegating to ``parse_matcher``. The latter reads + JSONC-parses +
schema-validates one file, then builds rules/groups/scenarios/default. Failure is
per-layer atomic: any single error (bad JSONC, schema reject, bad matcher, or an
``@ref``) fails the whole layer — it contributes nothing and every error string
names the source file plus the offending token/key.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

import jsonschema

from mcp_coder.icoder.permissions.matcher import parse_matcher
from mcp_coder.icoder.permissions.model import Matcher, Policy, Rule
from mcp_coder.utils.user_app_data import get_user_app_data_dir

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


def _discover_layers(project_dir: Path) -> list[tuple[str, Path]]:
    """Return (layer_tag, path) for each existing settings file, ordered
    lowest -> highest precedence: user, project, local. Absent files omitted.

    Each returned path is resolved to absolute so ``Rule.source_path``
    provenance stays absolute even when ``project_dir`` is relative
    (issue #1042 Decisions). ``.claude/*`` is never consulted.

    Args:
        project_dir: The project root whose ``.icoder/`` layers are located.

    Returns:
        A list of ``(layer_tag, absolute_path)`` tuples ordered lowest ->
        highest precedence; layers whose file is absent are omitted.
    """
    candidates: list[tuple[str, Path]] = [
        ("user", get_user_app_data_dir("mcp_coder") / ".icoder" / "settings.json"),
        ("project", project_dir / ".icoder" / "settings.json"),
        ("local", project_dir / ".icoder" / "settings.local.json"),
    ]
    return [(tag, p.resolve()) for tag, p in candidates if p.is_file()]


class _LayerResult(NamedTuple):
    """The outcome of loading one layer.

    On success: the parsed ``default_policy`` (or ``None`` when absent) plus the
    built ``rules``/``groups``/``scenarios`` and an empty ``errors`` list. On any
    failure: ``default_policy=None`` with empty collections and a non-empty
    ``errors`` list — the layer contributes nothing (per-layer atomic
    fail-closed).
    """

    default_policy: Policy | None
    rules: list[Rule]
    groups: dict[str, tuple[Matcher, ...]]
    scenarios: dict[str, tuple[Matcher, ...]]
    errors: list[str]


def _parse_matchers(token: str, path: Path) -> tuple[list[Matcher], list[str]]:
    """Parse one matcher token, pre-detecting ``@ref`` members.

    ``@ref`` is checked *before* delegating to ``parse_matcher`` (which would
    otherwise emit a generic "malformed matcher"): group references are not
    supported until I4.1. Every returned error names the source file and the
    offending token.

    Args:
        token: The single matcher token to parse.
        path: The source file the token came from (for error provenance).

    Returns:
        A ``(matchers, errors)`` tuple. Success yields ``(>=1 matchers, [])``;
        failure yields ``([], [reason, ...])``.
    """
    if token.startswith("@"):
        return [], [
            f"{path}: group references (@…) not supported until I4.1: {token!r}"
        ]
    matchers, errs = parse_matcher(token)
    if errs:
        return [], [f"{path}: {e} (token {token!r})" for e in errs]
    return matchers, []


def _load_layer(layer: str, path: Path) -> _LayerResult:
    """Read + JSONC-parse + schema-validate one file, then build its rules.

    Failure is per-layer atomic: on any error (unreadable/unparseable file,
    schema rejection, bad matcher, or an ``@ref`` token) the layer contributes
    nothing and ``errors`` is populated, each entry naming the file plus the
    offending token/key.

    Args:
        layer: The layer tag (``"user"`` | ``"project"`` | ``"local"``) stamped
            onto each built :class:`~mcp_coder.icoder.permissions.model.Rule`.
        path: The absolute settings-file path to load.

    Returns:
        A :class:`_LayerResult`; on failure its collections are empty and
        ``errors`` is non-empty.
    """
    try:
        data = json.loads(_strip_jsonc(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        return _LayerResult(None, [], {}, {}, [f"{path}: {exc}"])

    # Validate the whole structure before walking it: a non-dict root or a
    # wrong-typed section would otherwise raise below (breaking fail-closed).
    schema_errors = [f"{path}: {m}" for m in _schema_errors(data)]
    if schema_errors:
        return _LayerResult(None, [], {}, {}, schema_errors)

    errors: list[str] = []
    rules: list[Rule] = []
    groups: dict[str, tuple[Matcher, ...]] = {}
    scenarios: dict[str, tuple[Matcher, ...]] = {}

    # All keys optional -> default-safe access. An omitted section yields an
    # empty iterable (never ``None``), so the common "absent section" case is
    # not an error.
    for section, policy in (
        ("allow", Policy.ALWAYS),
        ("ask", Policy.AFTER_APPROVAL),
        ("deny", Policy.NEVER),
    ):
        for token in data.get(section, []):
            matchers, errs = _parse_matchers(token, path)
            errors += errs
            rules += [Rule(m, policy, layer, path) for m in matchers]

    for named, store in (("toolGroups", groups), ("toolScenarios", scenarios)):
        for name, members in data.get(named, {}).items():
            collected: list[Matcher] = []
            for token in members:
                matchers, errs = _parse_matchers(token, path)
                errors += errs
                collected += matchers
            store[name] = tuple(collected)

    default = (
        _POLICY_BY_TOKEN.get(data["defaultMode"]) if "defaultMode" in data else None
    )

    if errors:
        return _LayerResult(None, [], {}, {}, errors)
    return _LayerResult(default, rules, groups, scenarios, [])
