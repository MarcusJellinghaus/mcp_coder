"""Tests for the iCoder permission loader (Steps 2-3, TDD).

Step 2 covers only the JSONC preprocessor
``mcp_coder.icoder.permissions.loader._strip_jsonc`` — a stdlib,
string/escape-aware comment stripper that also tolerates trailing commas.
Comment-like sequences inside string literals (URLs, ``"a // b"``, escaped
quotes) must survive intact; the result must be valid JSON for ``json.loads``.

Step 3 covers the JSON-Schema builder, the ``_schema_errors`` validation
helper (structure + enums only), and the gated ``emit_schema`` writer.

Step 4 covers ``_discover_layers`` — locating the three settings files in
precedence order (user, project, local), skipping absent layers silently,
never touching ``.claude/*``, and returning absolute paths.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_coder.icoder.permissions.loader import (
    _discover_layers,
    _schema_errors,
    _strip_jsonc,
    build_settings_schema,
    emit_schema,
)

# --- comment removal ---


def test_line_comment_removed() -> None:
    """A ``//`` line comment is stripped and the JSON still parses."""
    text = '{"a": 1 // trailing note\n}'
    assert json.loads(_strip_jsonc(text)) == {"a": 1}


def test_block_comment_removed() -> None:
    """A ``/* */`` block comment is stripped and the JSON still parses."""
    text = '{/* header */ "a": 1}'
    assert json.loads(_strip_jsonc(text)) == {"a": 1}


# --- comment markers inside strings are preserved ---


def test_url_double_slash_preserved() -> None:
    """A ``//`` inside a string literal (URL) is left untouched."""
    text = '{"url": "https://example.com"}'
    assert json.loads(_strip_jsonc(text)) == {"url": "https://example.com"}


def test_line_marker_inside_string_preserved() -> None:
    """``"a // b"`` keeps its inner ``//``."""
    text = '{"v": "a // b"}'
    assert json.loads(_strip_jsonc(text)) == {"v": "a // b"}


def test_block_marker_inside_string_preserved() -> None:
    """``"a /* b */ c"`` keeps its inner block markers."""
    text = '{"v": "a /* b */ c"}'
    assert json.loads(_strip_jsonc(text)) == {"v": "a /* b */ c"}


def test_escaped_quote_then_comment() -> None:
    """An escaped quote survives; a ``//`` after the string closes is stripped."""
    text = '{"v": "he said \\"hi\\" //x"} // gone'
    assert json.loads(_strip_jsonc(text)) == {"v": 'he said "hi" //x'}


# --- trailing commas ---


def test_trailing_comma_before_brace_removed() -> None:
    """A trailing comma before ``}`` is dropped."""
    text = '{"a": 1,}'
    assert json.loads(_strip_jsonc(text)) == {"a": 1}


def test_trailing_comma_before_bracket_removed() -> None:
    """A trailing comma before ``]`` is dropped."""
    text = '{"a": [1, 2,]}'
    assert json.loads(_strip_jsonc(text)) == {"a": [1, 2]}


def test_comma_inside_string_preserved() -> None:
    """A comma-then-bracket inside a string (``"a,]"``) is preserved."""
    text = '{"v": "a,]"}'
    assert json.loads(_strip_jsonc(text)) == {"v": "a,]"}


# --- no-op round trip ---


def test_plain_json_roundtrips() -> None:
    """Comment-free input round-trips unchanged through json.loads."""
    obj = {"a": 1, "b": ["x", "y"], "c": {"d": True}}
    text = json.dumps(obj)
    assert json.loads(_strip_jsonc(text)) == obj


# --- Step 3: schema validation (structure + enums only) ---


def test_schema_accepts_full_valid_config() -> None:
    """A config using every section with a valid ``defaultMode`` passes."""
    data = {
        "$schema": "./settings.schema.json",
        "defaultMode": "ask",
        "allow": ["github:*"],
        "ask": ["fs:write"],
        "deny": ["shell:*"],
        "toolGroups": {"git": ["github:*", "shell:git"]},
        "toolScenarios": {"review": ["github:pr_view"]},
    }
    assert _schema_errors(data) == []


def test_schema_rejects_bad_default_mode() -> None:
    """``defaultMode: "maybe"`` is not in the enum and is rejected."""
    errors = _schema_errors({"defaultMode": "maybe"})
    assert errors
    assert any("defaultMode" in e for e in errors)


def test_schema_rejects_non_array_allow() -> None:
    """``allow`` must be an array; a string value is rejected."""
    errors = _schema_errors({"allow": "github:*"})
    assert errors
    assert any("allow" in e for e in errors)


def test_schema_rejects_unknown_top_level_key() -> None:
    """An unknown top-level key is rejected (additionalProperties false)."""
    errors = _schema_errors({"bogus": 1})
    assert errors


def test_schema_rejects_tool_groups_value_not_string_array() -> None:
    """A ``toolGroups`` value that is not an array of strings is rejected."""
    errors = _schema_errors({"toolGroups": {"git": [1, 2]}})
    assert errors
    assert any("toolGroups" in e or "git" in e for e in errors)


# --- Step 3: gated schema emit ---


def test_emit_schema_absent_dir_writes_nothing(tmp_path: Path) -> None:
    """When ``.icoder/`` does not exist, nothing is written and it returns False."""
    assert emit_schema(tmp_path) is False
    assert not (tmp_path / ".icoder").exists()


def test_emit_schema_writes_when_missing(tmp_path: Path) -> None:
    """With ``.icoder/`` present but the file missing, it writes and returns True."""
    (tmp_path / ".icoder").mkdir()
    assert emit_schema(tmp_path) is True
    target = tmp_path / ".icoder" / "settings.schema.json"
    assert target.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == build_settings_schema()


def test_emit_schema_no_rewrite_on_identical_content(tmp_path: Path) -> None:
    """A second call with identical content returns False (no rewrite)."""
    (tmp_path / ".icoder").mkdir()
    assert emit_schema(tmp_path) is True
    assert emit_schema(tmp_path) is False


def test_emit_schema_rewrites_when_content_differs(tmp_path: Path) -> None:
    """When existing content differs, the file is rewritten and returns True."""
    (tmp_path / ".icoder").mkdir()
    target = tmp_path / ".icoder" / "settings.schema.json"
    target.write_text("{}\n", encoding="utf-8")
    assert emit_schema(tmp_path) is True
    assert json.loads(target.read_text(encoding="utf-8")) == build_settings_schema()


# --- Step 4: layer discovery ---


def _make_settings(directory: Path, name: str) -> Path:
    """Create ``<directory>/.icoder/<name>`` with a minimal body."""
    icoder = directory / ".icoder"
    icoder.mkdir(exist_ok=True)
    path = icoder / name
    path.write_text("{}\n", encoding="utf-8")
    return path


def test_discover_all_three_layers_in_precedence_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """All three present → tuples ordered exactly user, project, local."""
    user_root = tmp_path / "user"
    user_root.mkdir()
    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
        lambda _app: user_root,
    )
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    _make_settings(user_root, "settings.json")
    _make_settings(project_dir, "settings.json")
    _make_settings(project_dir, "settings.local.json")

    layers = _discover_layers(project_dir)

    assert [tag for tag, _ in layers] == ["user", "project", "local"]


def test_discover_only_project_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only ``project`` present → a single ``("project", ...)`` tuple."""
    user_root = tmp_path / "user"
    user_root.mkdir()
    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
        lambda _app: user_root,
    )
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    _make_settings(project_dir, "settings.json")

    layers = _discover_layers(project_dir)

    assert len(layers) == 1
    tag, path = layers[0]
    assert tag == "project"
    assert path == (project_dir / ".icoder" / "settings.json").resolve()


def test_discover_none_present_returns_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """None present → empty list (no error)."""
    user_root = tmp_path / "user"
    user_root.mkdir()
    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
        lambda _app: user_root,
    )
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    assert _discover_layers(project_dir) == []


def test_discover_user_layer_under_app_data_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The user layer resolves under ``get_user_app_data_dir``."""
    user_root = tmp_path / "user"
    user_root.mkdir()
    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
        lambda _app: user_root,
    )
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    _make_settings(user_root, "settings.json")

    layers = _discover_layers(project_dir)

    assert len(layers) == 1
    tag, path = layers[0]
    assert tag == "user"
    assert str(user_root.resolve()) in str(path)


def test_discover_never_reads_dot_claude(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ``.claude/settings.json`` in the project dir is never returned."""
    user_root = tmp_path / "user"
    user_root.mkdir()
    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
        lambda _app: user_root,
    )
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    claude = project_dir / ".claude"
    claude.mkdir()
    (claude / "settings.json").write_text("{}\n", encoding="utf-8")
    _make_settings(project_dir, "settings.json")

    layers = _discover_layers(project_dir)

    assert all(".claude" not in str(path) for _, path in layers)


def test_discover_relative_project_dir_yields_absolute_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative ``project_dir`` still yields absolute discovered paths."""
    user_root = tmp_path / "user"
    user_root.mkdir()
    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
        lambda _app: user_root,
    )
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    _make_settings(project_dir, "settings.json")
    _make_settings(project_dir, "settings.local.json")

    monkeypatch.chdir(tmp_path)
    layers = _discover_layers(Path("project"))

    assert layers
    assert all(path.is_absolute() for _, path in layers)
