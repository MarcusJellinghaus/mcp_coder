"""Tests for the pure skill ``tools:`` block parser (Step 1, TDD).

Exercises ``mcp_coder.icoder.permissions.skill_tools`` — a dependency-free
parser that records **raw strings only** (no ``Matcher``/``PermissionFrame``,
no token semantics). Plus a ``load_skills`` test proving the parsed block is
stored on ``ClaudeSkill.tools_block``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_coder.icoder.permissions.skill_tools import (
    SkillToolsBlock,
    parse_tools_block,
)
from mcp_coder.icoder.skills import load_skills

# --- Absent vs present-but-null (the fail-open boundary) ---


def test_absent_tools_key_returns_none() -> None:
    """A missing ``tools`` key is ABSENT (fail-open) → None, not a block."""
    assert parse_tools_block({}) is None


def test_absent_with_other_keys_returns_none() -> None:
    """Only the ``tools`` key matters; other frontmatter keys don't create one."""
    assert parse_tools_block({"description": "x", "allowed-tools": ["Read"]}) is None


def test_present_but_null_is_malformed_not_absent() -> None:
    """``tools:`` written with no value is MALFORMED, not absent.

    ``meta.get("tools")`` returns None for both an absent key and a
    present-but-null block, so the parser must membership-test the key. This
    is the fail-open/fail-closed boundary: present-but-null must yield a
    ``SkillToolsBlock`` with errors, NOT ``None``.
    """
    result = parse_tools_block({"tools": None})
    assert result is not None
    assert isinstance(result, SkillToolsBlock)
    assert result.errors
    assert result.base is None


# --- Malformed set (each spelled out; assert non-empty errors) ---


@pytest.mark.parametrize(
    "meta",
    [
        pytest.param({"tools": ["mcp__s__t"]}, id="yaml_list"),
        pytest.param({"tools": None}, id="present_but_null"),
        pytest.param({"tools": {}}, id="empty_mapping"),
        pytest.param({"tools": "x"}, id="scalar"),
        pytest.param({"tools": {"allow": ["mcp__s__t"]}}, id="missing_base"),
        pytest.param({"tools": {"base": "foo"}}, id="invalid_base"),
        pytest.param(
            {"tools": {"base": "inherit", "allow": "mcp__s__t"}}, id="scalar_allow"
        ),
        pytest.param(
            {"tools": {"base": "inherit", "allow": [123]}}, id="non_string_item"
        ),
        pytest.param(
            {"tools": {"use": "name", "allow": ["mcp__s__t"]}}, id="use_plus_inline"
        ),
    ],
)
def test_malformed_blocks_record_errors(meta: dict[str, object]) -> None:
    """Every malformed shape yields a block with non-empty ``errors``."""
    result = parse_tools_block(meta)
    assert result is not None
    assert result.errors


def test_non_string_item_never_carried_forward() -> None:
    """A non-string ``allow`` item is dropped wholesale, leaving allow empty."""
    result = parse_tools_block({"tools": {"base": "inherit", "allow": [123]}})
    assert result is not None
    assert result.errors
    assert result.allow == ()


# --- Valid rich blocks ---


def test_valid_inherit_block_round_trips_verbatim() -> None:
    """``base: inherit`` with allow/deny round-trips the raw tokens verbatim."""
    result = parse_tools_block(
        {
            "tools": {
                "base": "inherit",
                "allow": ["mcp__srv__tool", "mcp__srv__*"],
                "deny": ["mcp__srv__danger", "@group_ref"],
            }
        }
    )
    assert result is not None
    assert result.base == "inherit"
    assert result.allow == ("mcp__srv__tool", "mcp__srv__*")
    assert result.deny == ("mcp__srv__danger", "@group_ref")
    assert result.use is None
    assert result.errors == ()


def test_base_none_empty_allow_is_valid_sandbox() -> None:
    """``base: none, allow: []`` is a valid zero-tool sandbox — no errors."""
    result = parse_tools_block({"tools": {"base": "none", "allow": []}})
    assert result is not None
    assert result.base == "none"
    assert result.allow == ()
    assert result.deny == ()
    assert result.errors == ()


# --- Bare use: block ---


def test_bare_use_block_is_valid_no_errors() -> None:
    """A bare ``use: name`` block sets ``use`` and records no errors."""
    result = parse_tools_block({"tools": {"use": "team_defaults"}})
    assert result is not None
    assert result.use == "team_defaults"
    assert result.base is None
    assert result.errors == ()


# --- Advisories (rich-block lint only, never blocks) ---


def test_non_mcp_tokens_recorded_as_advisories() -> None:
    """Non-``mcp__``/non-``@`` tokens in a rich block are advisories, not errors."""
    result = parse_tools_block(
        {
            "tools": {
                "base": "inherit",
                "allow": ["mcp__srv__tool", "Bash(git status)", "gh"],
            }
        }
    )
    assert result is not None
    assert result.errors == ()
    assert "Bash(git status)" in result.advisories
    assert "gh" in result.advisories
    assert "mcp__srv__tool" not in result.advisories


def test_at_ref_in_deny_is_not_an_advisory() -> None:
    """A ``@ref`` deny token is not flagged as a non-mcp advisory."""
    result = parse_tools_block({"tools": {"base": "inherit", "deny": ["@group_ref"]}})
    assert result is not None
    assert result.advisories == ()


# --- load_skills populates ClaudeSkill.tools_block ---


def _create_skill(tmp_path: Path, skill_name: str, frontmatter: str, body: str) -> Path:
    """Create a ``.claude/skills/<name>/SKILL.md`` file.

    Returns:
        The created skill directory path.
    """
    skill_dir = tmp_path / ".claude" / "skills" / skill_name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\n{frontmatter}---\n\n{body}")
    return skill_dir


def test_load_skills_populates_tools_block(tmp_path: Path) -> None:
    """A SKILL.md carrying a rich ``tools:`` block populates ``tools_block``."""
    fm = (
        'description: "Rich skill"\n'
        "tools:\n"
        '  base: "inherit"\n'
        "  allow:\n"
        "    - mcp__srv__tool\n"
    )
    _create_skill(tmp_path, "rich", fm, "body")
    skills = load_skills(tmp_path)
    assert len(skills) == 1
    block = skills[0].tools_block
    assert block is not None
    assert block.base == "inherit"
    assert block.allow == ("mcp__srv__tool",)


def test_load_skills_tools_block_none_when_absent(tmp_path: Path) -> None:
    """When no ``tools:`` block is present, ``tools_block`` stays None.

    The legacy ``allowed-tools`` list is still parsed as before, untouched.
    """
    fm = 'description: "Legacy skill"\nallowed-tools:\n  - Read\n'
    _create_skill(tmp_path, "legacy", fm, "body")
    skills = load_skills(tmp_path)
    assert len(skills) == 1
    assert skills[0].tools_block is None
    assert skills[0].allowed_tools == ["Read"]
