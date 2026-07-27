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

Step 5 covers ``_parse_matchers`` (single-token matcher parsing with ``@ref``
pre-detection) and ``_load_layer`` — reading + JSONC-parsing + schema-validating
one file, then building rules/groups/scenarios/default. Any single error fails
the whole layer (grants nothing); errors always name the file + offending token.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from mcp_coder.icoder.permissions.loader import (
    _discover_layers,
    _load_layer,
    _parse_matchers,
    _schema_errors,
    _strip_jsonc,
    build_settings_schema,
    emit_schema,
    load_permission_config,
)
from mcp_coder.icoder.permissions.model import PermissionConfig, Policy
from mcp_coder.icoder.permissions.resolver import resolve

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


# --- Step 5: per-layer load ---


def _write_layer(tmp_path: Path, body: str) -> Path:
    """Write ``body`` to an absolute ``settings.json`` under ``tmp_path``."""
    path = (tmp_path / "settings.json").resolve()
    path.write_text(body, encoding="utf-8")
    return path


def test_parse_matchers_concrete_token(tmp_path: Path) -> None:
    """A concrete ``mcp__…`` token parses to one matcher, no errors."""
    path = _write_layer(tmp_path, "{}")
    matchers, errors = _parse_matchers("mcp__fs__write", path)
    assert errors == []
    assert len(matchers) == 1
    assert matchers[0].server == "fs"
    assert matchers[0].tool == "write"


def test_parse_matchers_ref_pre_detected(tmp_path: Path) -> None:
    """An ``@ref`` token is rejected with the I4.1 diagnostic, not the generic
    malformed-matcher message."""
    path = _write_layer(tmp_path, "{}")
    matchers, errors = _parse_matchers("@git", path)
    assert matchers == []
    assert len(errors) == 1
    assert "not supported until I4.1" in errors[0]
    assert "@git" in errors[0]
    assert str(path) in errors[0]


def test_parse_matchers_bad_token_names_file_and_token(tmp_path: Path) -> None:
    """A non-``mcp__`` token fails and the error names the file + token."""
    path = _write_layer(tmp_path, "{}")
    matchers, errors = _parse_matchers("github:*", path)
    assert matchers == []
    assert errors
    assert str(path) in errors[0]
    assert "github:*" in errors[0]


def test_load_layer_good_allow_ask_deny_policies(tmp_path: Path) -> None:
    """``allow``/``ask``/``deny`` map to the correct ``Rule.policy``."""
    path = _write_layer(
        tmp_path,
        json.dumps(
            {
                "allow": ["mcp__fs__read"],
                "ask": ["mcp__fs__write"],
                "deny": ["mcp__shell__exec"],
            }
        ),
    )
    result = _load_layer("project", path)
    assert result.errors == []
    by_policy = {r.matcher.tool: r.policy for r in result.rules}
    assert by_policy["read"] is Policy.ALWAYS
    assert by_policy["write"] is Policy.AFTER_APPROVAL
    assert by_policy["exec"] is Policy.NEVER


def test_load_layer_provenance_absolute_and_layer_tag(tmp_path: Path) -> None:
    """Each rule carries the absolute source path and the layer tag."""
    path = _write_layer(tmp_path, json.dumps({"allow": ["mcp__fs__read"]}))
    result = _load_layer("local", path)
    assert result.errors == []
    assert len(result.rules) == 1
    rule = result.rules[0]
    assert rule.source_path == path
    assert rule.source_path is not None and rule.source_path.is_absolute()
    assert rule.layer == "local"


def test_load_layer_value_set_expands_to_n_rules(tmp_path: Path) -> None:
    """A value-set matcher expands to N rules within the layer."""
    path = _write_layer(
        tmp_path,
        json.dumps({"allow": ["mcp__fs__write(path={a,b,c})"]}),
    )
    result = _load_layer("project", path)
    assert result.errors == []
    assert len(result.rules) == 3
    assert {r.matcher.arg.value for r in result.rules if r.matcher.arg} == {
        "a",
        "b",
        "c",
    }


def test_load_layer_populates_groups_and_scenarios(tmp_path: Path) -> None:
    """``toolGroups``/``toolScenarios`` are parsed into matcher tuples."""
    path = _write_layer(
        tmp_path,
        json.dumps(
            {
                "toolGroups": {"git": ["mcp__git__status", "mcp__git__log"]},
                "toolScenarios": {"review": ["mcp__github__pr_view"]},
            }
        ),
    )
    result = _load_layer("project", path)
    assert result.errors == []
    assert set(result.groups) == {"git"}
    assert len(result.groups["git"]) == 2
    assert set(result.scenarios) == {"review"}
    assert result.scenarios["review"][0].tool == "pr_view"


def test_load_layer_parses_default_mode(tmp_path: Path) -> None:
    """``defaultMode`` maps to the corresponding policy."""
    path = _write_layer(tmp_path, json.dumps({"defaultMode": "deny"}))
    result = _load_layer("project", path)
    assert result.errors == []
    assert result.default_policy is Policy.NEVER


def test_load_layer_ref_in_rule_list_grants_nothing(tmp_path: Path) -> None:
    """An ``@ref`` in a rule list degrades the whole layer."""
    path = _write_layer(
        tmp_path,
        json.dumps({"allow": ["mcp__fs__read", "@git"]}),
    )
    result = _load_layer("project", path)
    assert result.rules == []
    assert result.default_policy is None
    assert result.errors
    joined = " ".join(result.errors)
    assert "not supported until I4.1" in joined
    assert "@git" in joined


def test_load_layer_ref_in_group_member_grants_nothing(tmp_path: Path) -> None:
    """An ``@ref`` nested in a ``toolGroups`` member gives the same diagnostic
    and degrades the layer."""
    path = _write_layer(
        tmp_path,
        json.dumps({"toolGroups": {"git": ["mcp__git__status", "@other"]}}),
    )
    result = _load_layer("project", path)
    assert result.groups == {}
    assert result.errors
    joined = " ".join(result.errors)
    assert "not supported until I4.1" in joined
    assert "@other" in joined


def test_load_layer_bad_matcher_names_file_and_token(tmp_path: Path) -> None:
    """A non-``mcp__`` matcher degrades the layer; error names file + token."""
    path = _write_layer(tmp_path, json.dumps({"allow": ["github:*"]}))
    result = _load_layer("project", path)
    assert result.rules == []
    assert result.errors
    joined = " ".join(result.errors)
    assert str(path) in joined
    assert "github:*" in joined


def test_load_layer_schema_invalid_names_file(tmp_path: Path) -> None:
    """A schema-invalid ``defaultMode`` degrades the layer and names the file."""
    path = _write_layer(tmp_path, json.dumps({"defaultMode": "maybe"}))
    result = _load_layer("project", path)
    assert result.rules == []
    assert result.default_policy is None
    assert result.errors
    assert all(str(path) in e for e in result.errors)


@pytest.mark.parametrize("root", ["[]", "42", '"x"'])
def test_load_layer_non_dict_root_degrades(tmp_path: Path, root: str) -> None:
    """A non-dict root degrades (does not raise); errors name the file."""
    path = _write_layer(tmp_path, root)
    result = _load_layer("project", path)
    assert result.rules == []
    assert result.errors
    assert all(str(path) in e for e in result.errors)


def test_load_layer_wrong_typed_section_degrades(tmp_path: Path) -> None:
    """A wrong-typed section (``"allow": 5``) degrades without raising."""
    path = _write_layer(tmp_path, '{"allow": 5}')
    result = _load_layer("project", path)
    assert result.rules == []
    assert result.errors
    assert all(str(path) in e for e in result.errors)


def test_load_layer_bad_jsonc_degrades(tmp_path: Path) -> None:
    """Unparseable JSON degrades the layer and names the file."""
    path = _write_layer(tmp_path, "{not valid json")
    result = _load_layer("project", path)
    assert result.rules == []
    assert result.errors
    assert all(str(path) in e for e in result.errors)


def test_load_layer_jsonc_comment_in_string_value(tmp_path: Path) -> None:
    """JSONC comments outside strings are stripped while ``//`` inside a string
    value survives, yielding the correct rule."""
    body = '{\n  // grant read\n  "allow": ["mcp__fs__read"]\n}'
    path = _write_layer(tmp_path, body)
    result = _load_layer("project", path)
    assert result.errors == []
    assert len(result.rules) == 1
    assert result.rules[0].matcher.tool == "read"


def test_load_layer_empty_object_loads_cleanly(tmp_path: Path) -> None:
    """A layer with no sections loads with no rules and no error/degrade."""
    path = _write_layer(tmp_path, "{}")
    result = _load_layer("project", path)
    assert result.errors == []
    assert result.rules == []
    assert result.groups == {}
    assert result.scenarios == {}
    assert result.default_policy is None


def test_load_layer_only_default_mode_loads_cleanly(tmp_path: Path) -> None:
    """A layer with only ``defaultMode`` loads cleanly (guards ``.get`` access)."""
    path = _write_layer(tmp_path, json.dumps({"defaultMode": "allow"}))
    result = _load_layer("project", path)
    assert result.errors == []
    assert result.rules == []
    assert result.groups == {}
    assert result.scenarios == {}
    assert result.default_policy is Policy.ALWAYS


# --- Step 6: public load_permission_config (merge + degrade + provenance) ---


def _empty_user_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point ``get_user_app_data_dir`` at an empty dir (no user layer)."""
    user_root = tmp_path / "user"
    user_root.mkdir()
    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
        lambda _app: user_root,
    )


def _write_project_layers(
    project_dir: Path, project_body: str | None, local_body: str | None
) -> None:
    """Write project/local ``.icoder`` settings bodies (skip ``None``)."""
    icoder = project_dir / ".icoder"
    icoder.mkdir(exist_ok=True)
    if project_body is not None:
        (icoder / "settings.json").write_text(project_body, encoding="utf-8")
    if local_body is not None:
        (icoder / "settings.local.json").write_text(local_body, encoding="utf-8")


def test_load_two_good_layers_concatenates_rules_last_default_wins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two good layers → rules concatenated with per-rule provenance; the higher
    layer's ``defaultMode`` wins."""
    _empty_user_dir(tmp_path, monkeypatch)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    _write_project_layers(
        project_dir,
        json.dumps({"defaultMode": "allow", "allow": ["mcp__fs__read"]}),
        json.dumps({"defaultMode": "ask", "allow": ["mcp__git__status"]}),
    )

    config = load_permission_config(project_dir)

    assert config.degraded is False
    assert config.errors == ()
    by_layer = {r.layer: r for r in config.rules}
    assert set(by_layer) == {"project", "local"}
    assert by_layer["project"].matcher.tool == "read"
    assert by_layer["local"].matcher.tool == "status"
    icoder = (project_dir / ".icoder").resolve()
    assert by_layer["project"].source_path == icoder / "settings.json"
    assert by_layer["local"].source_path == icoder / "settings.local.json"
    # Higher (local) layer's defaultMode wins.
    assert config.default_policy is Policy.AFTER_APPROVAL


def test_load_fail_closed_config_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One good + one broken layer → degraded True, errors non-empty, the good
    layer's rules present, the broken layer's rules absent."""
    _empty_user_dir(tmp_path, monkeypatch)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    _write_project_layers(
        project_dir,
        json.dumps({"defaultMode": "allow", "allow": ["mcp__x__y"]}),
        json.dumps({"allow": ["github:*"]}),  # bad matcher -> broken layer
    )

    config = load_permission_config(project_dir)

    assert config.degraded is True
    assert config.errors
    # Good (project) layer's rule survives; broken (local) layer grants nothing.
    assert [r.matcher.tool for r in config.rules] == ["y"]
    assert all(r.layer == "project" for r in config.rules)


def test_load_fail_closed_resolve_never_silent_allow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Even with a good ``allow`` rule / ``defaultMode: allow``, a degraded
    config forces ``resolve()`` to ASK (never a silent allow)."""
    _empty_user_dir(tmp_path, monkeypatch)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    _write_project_layers(
        project_dir,
        json.dumps({"defaultMode": "allow", "allow": ["mcp__x__y"]}),
        json.dumps({"allow": ["github:*"]}),  # bad matcher -> broken layer
    )

    config = load_permission_config(project_dir)

    decision = resolve("mcp__x__y", None, None, config)
    assert decision.policy is Policy.AFTER_APPROVAL


def test_load_fail_closed_diagnostic_logged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The broken-layer error is emitted to the logger at ERROR (not only in
    ``PermissionConfig.errors``)."""
    _empty_user_dir(tmp_path, monkeypatch)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    _write_project_layers(
        project_dir,
        json.dumps({"allow": ["mcp__x__y"]}),
        json.dumps({"allow": ["github:*"]}),  # bad matcher -> broken layer
    )

    with caplog.at_level(logging.ERROR):
        load_permission_config(project_dir)

    error_logs = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert error_logs
    assert any("github:*" in r.getMessage() for r in error_logs)


def test_load_all_layers_absent_backward_compat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """All three layers absent → not degraded, no default, resolve ALWAYS."""
    _empty_user_dir(tmp_path, monkeypatch)
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    config = load_permission_config(project_dir)

    assert config.degraded is False
    assert config.default_policy is None
    assert config.errors == ()
    assert resolve("mcp__any__tool", None, None, config).policy is Policy.ALWAYS


def test_load_shadowed_group_warns_and_higher_layer_wins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A group name redefined by a higher layer logs a warning; the higher
    layer's definition wins."""
    _empty_user_dir(tmp_path, monkeypatch)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    _write_project_layers(
        project_dir,
        json.dumps({"toolGroups": {"git": ["mcp__git__status"]}}),
        json.dumps({"toolGroups": {"git": ["mcp__git__log"]}}),
    )

    with caplog.at_level(logging.WARNING):
        config = load_permission_config(project_dir)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("git" in r.getMessage() for r in warnings)
    assert [m.tool for m in config.groups["git"]] == ["log"]


def test_load_emits_schema_when_icoder_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``load_permission_config`` writes ``settings.schema.json`` when
    ``.icoder/`` exists."""
    _empty_user_dir(tmp_path, monkeypatch)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    _write_project_layers(project_dir, "{}", None)

    load_permission_config(project_dir)

    schema = project_dir / ".icoder" / "settings.schema.json"
    assert schema.is_file()
    assert json.loads(schema.read_text(encoding="utf-8")) == build_settings_schema()


def test_init_exports_load_permission_config() -> None:
    """The package re-exports ``load_permission_config``."""
    import mcp_coder.icoder.permissions as pkg

    assert hasattr(pkg, "load_permission_config")
    assert pkg.load_permission_config is load_permission_config
    assert "load_permission_config" in pkg.__all__


def test_load_returns_permission_config_instance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The return value is a ``PermissionConfig``."""
    _empty_user_dir(tmp_path, monkeypatch)
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    assert isinstance(load_permission_config(project_dir), PermissionConfig)
