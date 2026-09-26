"""Tests for the JSONC rule writer ``permissions/persist.py`` (I3.3 step 4).

Every case is a plain ``tmp_path`` unit test over an inline JSONC fixture —
never an in-repo file, since the persist target is meant to be gitignored.
Round-trip cases go through :func:`_reload`, so the assertion is "the reloaded
``local`` rule decided" (``source == Layer("local")``), not merely "the policy
is ALWAYS" — the resolver answers ALWAYS by default when no rule matches, which
would make a policy-only assertion unfalsifiable.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_coder.icoder.permissions.loader import (
    LOCAL_SETTINGS_RELPATH,
    _strip_jsonc,
    load_permission_config,
)
from mcp_coder.icoder.permissions.model import Decision, Layer, Policy
from mcp_coder.icoder.permissions.persist import PersistError, write_rule
from mcp_coder.icoder.permissions.resolver import resolve

TOOL = "mcp__srv__tool"
OTHER = "mcp__srv__other"


def _target(tmp_path: Path) -> Path:
    return tmp_path / LOCAL_SETTINGS_RELPATH


def _seed(tmp_path: Path, body: str | bytes) -> Path:
    """Write ``body`` to the persist target under ``tmp_path`` and return it."""
    target = _target(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
    return target


def _text(target: Path) -> str:
    return target.read_bytes().decode("utf-8")


def _reload(tmp_path: Path, tool: str, monkeypatch: pytest.MonkeyPatch) -> Decision:
    """Load the layers under ``tmp_path`` and resolve ``tool`` (user layer isolated)."""
    user_root = tmp_path / "user"
    user_root.mkdir(exist_ok=True)
    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
        lambda _app: user_root,
    )
    return resolve(tool, {}, None, load_permission_config(tmp_path))


def _assert_local_always(decision: Decision) -> None:
    assert decision.policy is Policy.ALWAYS
    assert decision.source == Layer("local")


def _assert_persist_error_leaves_file_untouched(target: Path, matcher: str) -> None:
    before = target.read_bytes()
    with pytest.raises(PersistError) as exc_info:
        write_rule(target, matcher, "allow")
    assert exc_info.type is PersistError
    assert target.read_bytes() == before


# --- happy paths -----------------------------------------------------------


def test_creates_file_and_directory_when_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No ``.icoder/`` at all: the writer creates the dir + file with plain JSON."""
    target = _target(tmp_path)
    assert not target.parent.exists()

    write_rule(target, TOOL)

    assert target.parent.is_dir()
    assert target.is_file()
    # Plain json.loads, not _strip_jsonc: a scaffold must not need comment or
    # trailing-comma tolerance.
    assert json.loads(_text(target)) == {"allow": [TOOL]}
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


def test_inserts_into_an_empty_array(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _seed(tmp_path, '{"allow": []}\n')

    write_rule(target, TOOL)

    assert _text(target) == f'{{"allow": ["{TOOL}"]}}\n'
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


def test_inserts_into_a_non_empty_array_keeping_existing_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Existing items keep their order and their lines stay byte-identical."""
    before = '{\n  "allow": [\n    "mcp__a__x",\n    "mcp__b__y"\n  ]\n}\n'
    target = _seed(tmp_path, before)

    write_rule(target, TOOL)

    after = _text(target)
    assert json.loads(after)["allow"] == [TOOL, "mcp__a__x", "mcp__b__y"]
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    assert len(after_lines) == len(before_lines) + 1
    assert after_lines[2] == f'    "{TOOL}",'
    assert after_lines[:2] + after_lines[3:] == before_lines
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


def test_preserves_line_and_block_comments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _seed(
        tmp_path,
        "{\n"
        "  // line comment stays\n"
        '  "allow": [\n'
        '    /* block comment stays */ "mcp__a__x"\n'
        "  ]\n"
        "}\n",
    )

    write_rule(target, TOOL)

    after = _text(target)
    assert "  // line comment stays\n" in after
    assert '    /* block comment stays */ "mcp__a__x"\n' in after
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


def test_double_slash_inside_a_string_is_not_a_comment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _seed(tmp_path, '{"$schema": "https://example.com//x", "allow": []}\n')

    write_rule(target, TOOL)

    after = _text(target)
    assert '"https://example.com//x"' in after
    assert json.loads(after) == {"$schema": "https://example.com//x", "allow": [TOOL]}
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


def test_escaped_quote_inside_a_string(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ``\\"`` must not close the string: the brackets after it are not code.

    A scanner that desynchronises here counts ``] }`` as code, never sees the
    real ``"allow"`` key at depth 1, and scaffolds a second one.
    """
    target = _seed(tmp_path, '{"$schema": "a \\" ] }", "allow": []}\n')

    write_rule(target, TOOL)

    after = _text(target)
    assert after.count('"allow":') == 1
    assert json.loads(after) == {"$schema": 'a " ] }', "allow": [TOOL]}
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


def test_trailing_comma_is_tolerated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _seed(tmp_path, '{"allow": ["mcp__a__x",],}\n')

    write_rule(target, TOOL)

    assert f'"{TOOL}", "mcp__a__x",],}}' in _text(target)
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


def test_absent_key_gets_a_scaffold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ask_block = f'  "ask": [\n    "{OTHER}"\n  ]'
    target = _seed(tmp_path, "{\n" + ask_block + "\n}\n")

    write_rule(target, TOOL)

    after = _text(target)
    assert ask_block in after
    assert json.loads(after) == {"allow": [TOOL], "ask": [OTHER]}
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))
    other = _reload(tmp_path, OTHER, monkeypatch)
    assert other.policy is Policy.AFTER_APPROVAL
    assert other.source == Layer("local")


def test_crlf_newlines_are_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _seed(
        tmp_path, '{\r\n  "ask": [\r\n    "mcp__a__x"\r\n  ],\r\n  "allow": []\r\n}\r\n'
    )

    write_rule(target, TOOL)
    write_rule(target, OTHER, "deny")  # scaffold path builds its own newlines

    raw = target.read_bytes()
    assert b"\r\n" in raw
    assert b"\n" not in raw.replace(b"\r\n", b"")
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


def test_indentation_matches_existing_items(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _seed(tmp_path, '{\n    "allow": [\n        "mcp__a__x"\n    ]\n}\n')

    write_rule(target, TOOL)

    assert f'\n        "{TOOL}",\n        "mcp__a__x"\n' in _text(target)
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


def test_matcher_in_another_list_is_moved_not_duplicated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _seed(
        tmp_path,
        "{\n"
        '  "ask": [\n'
        f'    "{TOOL}",\n'
        '    "mcp__a__x"\n'
        "  ],\n"
        '  "allow": []\n'
        "}\n",
    )

    write_rule(target, TOOL, "allow")

    after = _text(target)
    assert after.count(TOOL) == 1
    assert json.loads(after) == {"ask": ["mcp__a__x"], "allow": [TOOL]}
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


@pytest.mark.parametrize(
    "ask_body",
    [f'"{TOOL}" /* c */, "mcp__a__x"', f'"{TOOL}" // c\n, "mcp__a__x"'],
    ids=["block-comment-before-comma", "line-comment-before-comma"],
)
def test_move_skips_a_comment_between_item_and_comma(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ask_body: str
) -> None:
    """The comma after a moved item is found across a comment, not left dangling."""
    target = _seed(tmp_path, f'{{"ask": [{ask_body}], "allow": []}}\n')

    write_rule(target, TOOL, "allow")

    after = _text(target)
    assert json.loads(_strip_jsonc(after)) == {
        "ask": ["mcp__a__x"],
        "allow": [TOOL],
    }
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


def test_move_of_last_item_keeps_previous_items_line_comment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Removing the last entry deletes only its comma; the neighbour's comment stays."""
    target = _seed(
        tmp_path,
        "{\n"
        '  "ask": [\n'
        '    "mcp__a__x", // keep me\n'
        f'    "{TOOL}"\n'
        "  ],\n"
        '  "allow": []\n'
        "}\n",
    )

    write_rule(target, TOOL, "allow")

    after = _text(target)
    assert '    "mcp__a__x" // keep me\n  ],\n' in after
    assert json.loads(_strip_jsonc(after)) == {
        "ask": ["mcp__a__x"],
        "allow": [TOOL],
    }
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


def test_already_present_is_a_no_op(tmp_path: Path) -> None:
    target = _seed(tmp_path, f'{{"allow": ["{TOOL}"]}}\n')
    before = target.read_bytes()
    mtime = target.stat().st_mtime_ns

    write_rule(target, TOOL)

    assert target.read_bytes() == before
    assert target.stat().st_mtime_ns == mtime


def test_no_temp_file_is_left_behind(tmp_path: Path) -> None:
    """After a write ``.icoder/`` holds exactly the target (mkstemp uses no suffix)."""
    target = _seed(tmp_path, '{"allow": []}\n')

    write_rule(target, TOOL)

    assert [p.name for p in target.parent.iterdir()] == [target.name]


@pytest.mark.parametrize(
    "body",
    [
        '{"defaultMode": "allow"}\n',
        '{"defaultMode": "allow", "allow": ["mcp__a__x"]}\n',
    ],
    ids=["value-only", "value-and-key"],
)
def test_default_mode_value_is_not_mistaken_for_the_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str
) -> None:
    """``"defaultMode": "allow"`` puts a depth-1 ``"allow"`` string that is a value."""
    target = _seed(tmp_path, body)

    write_rule(target, TOOL)

    after = _text(target)
    assert after.count('"allow":') == 1
    parsed = json.loads(after)
    assert parsed["defaultMode"] == "allow"
    assert TOOL in parsed["allow"]
    _assert_local_always(_reload(tmp_path, TOOL, monkeypatch))


# --- failure paths: PersistError, nothing written -------------------------


def test_invalid_utf8_raises_persist_error(tmp_path: Path) -> None:
    target = _seed(tmp_path, b'{"allow": ["\xff\xfe"]}')
    _assert_persist_error_leaves_file_untouched(target, TOOL)


def test_malformed_jsonc_raises_persist_error(tmp_path: Path) -> None:
    assert issubclass(PersistError, OSError)
    target = _seed(tmp_path, '{"allow": [')
    _assert_persist_error_leaves_file_untouched(target, TOOL)


def test_non_object_root_raises_persist_error(tmp_path: Path) -> None:
    target = _seed(tmp_path, '["mcp__srv__x"]\n')
    _assert_persist_error_leaves_file_untouched(target, TOOL)


def test_unlocatable_move_item_raises_persist_error(tmp_path: Path) -> None:
    """Duplicate key: json keeps the second ``ask``, the locator finds the first."""
    target = _seed(tmp_path, '{"ask": [], "ask": ["mcp__a__b"]}\n')
    _assert_persist_error_leaves_file_untouched(target, "mcp__a__b")


@pytest.mark.parametrize(
    "body",
    ['{"allow": "mcp__a__b"}\n', '{"ask": "mcp__a__b"}\n'],
    ids=["target-section", "move-source-section"],
)
def test_non_list_section_raises_persist_error(tmp_path: Path, body: str) -> None:
    target = _seed(tmp_path, body)
    _assert_persist_error_leaves_file_untouched(target, "mcp__a__b")
