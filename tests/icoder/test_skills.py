"""Tests for skill models and loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_coder.icoder.skills import ClaudeSkill, ICoderSkillCommand, load_skills


def _create_skill(tmp_path: Path, skill_name: str, frontmatter: str, body: str) -> Path:
    """Helper to create a .claude/skills/<name>/SKILL.md file."""
    skill_dir = tmp_path / ".claude" / "skills" / skill_name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\n{frontmatter}---\n\n{body}")
    return skill_dir


def test_load_skills_discovers_valid_skill(tmp_path: Path) -> None:
    """load_skills finds and parses a valid SKILL.md."""
    _create_skill(
        tmp_path,
        "my_skill",
        'description: "A test skill"\n',
        "Do something with $ARGUMENTS",
    )
    skills = load_skills(tmp_path)
    assert len(skills) == 1
    assert skills[0].name == "my_skill"
    assert skills[0].description == "A test skill"
    assert skills[0].prompt_template == "Do something with $ARGUMENTS"


def test_load_skills_parses_all_frontmatter_fields(tmp_path: Path) -> None:
    """All frontmatter attributes are parsed into ClaudeSkill fields."""
    fm = (
        'description: "Full skill"\n'
        'argument-hint: "<issue_number>"\n'
        "disable-model-invocation: true\n"
        "user-invocable: true\n"
        "allowed-tools:\n"
        "  - Read\n"
        "  - Write\n"
        'model: "claude-sonnet-4-20250514"\n'
        'effort: "high"\n'
        'context: "codebase"\n'
        'agent: "task"\n'
        "paths:\n"
        "  - src/\n"
        "  - tests/\n"
        'shell: "bash"\n'
    )
    _create_skill(tmp_path, "full_skill", fm, "template body")
    skills = load_skills(tmp_path)
    assert len(skills) == 1
    s = skills[0]
    assert s.description == "Full skill"
    assert s.argument_hint == "<issue_number>"
    assert s.disable_model_invocation is True
    assert s.user_invocable is True
    assert s.allowed_tools == ["Read", "Write"]
    assert s.model == "claude-sonnet-4-20250514"
    assert s.effort == "high"
    assert s.context == "codebase"
    assert s.agent == "task"
    assert s.paths == ["src/", "tests/"]
    assert s.shell == "bash"


def test_load_skills_defaults_for_missing_optional_fields(tmp_path: Path) -> None:
    """Missing optional fields get sensible defaults."""
    _create_skill(
        tmp_path,
        "minimal",
        'description: "Minimal"\n',
        "body",
    )
    skills = load_skills(tmp_path)
    s = skills[0]
    assert s.argument_hint is None
    assert s.disable_model_invocation is False
    assert s.user_invocable is True
    assert s.allowed_tools == []
    assert s.model is None
    assert s.effort is None
    assert s.context is None
    assert s.agent is None
    assert s.hooks is None
    assert s.paths is None
    assert s.shell is None


def test_load_skills_filters_user_invocable_false(tmp_path: Path) -> None:
    """Skills with user-invocable: false are excluded."""
    _create_skill(
        tmp_path,
        "hidden",
        'description: "Hidden"\nuser-invocable: false\n',
        "body",
    )
    skills = load_skills(tmp_path)
    assert len(skills) == 0


@pytest.mark.parametrize("scenario", ["empty_dir", "no_skill_md", "malformed_file"])
def test_load_skills_skip_cases(tmp_path: Path, scenario: str) -> None:
    """load_skills handles edge cases: empty dir, missing SKILL.md, malformed files."""
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True)

    if scenario == "empty_dir":
        # No subdirectories at all
        pass
    elif scenario == "no_skill_md":
        # Subdirectory exists but no SKILL.md
        (skills_dir / "broken_skill").mkdir()
    elif scenario == "malformed_file":
        # SKILL.md with invalid frontmatter
        bad_dir = skills_dir / "bad_skill"
        bad_dir.mkdir()
        (bad_dir / "SKILL.md").write_text("---\n: invalid: yaml: [[\n---\nbody")

    skills = load_skills(tmp_path)
    assert len(skills) == 0


def test_load_skills_multiple_skills(tmp_path: Path) -> None:
    """Multiple valid skills are all returned."""
    _create_skill(tmp_path, "skill_a", 'description: "A"\n', "body a")
    _create_skill(tmp_path, "skill_b", 'description: "B"\n', "body b")
    skills = load_skills(tmp_path)
    assert len(skills) == 2
    names = {s.name for s in skills}
    assert names == {"skill_a", "skill_b"}


def test_icoder_skill_command_creation() -> None:
    """ICoderSkillCommand wraps a ClaudeSkill with command_name."""
    skill = ClaudeSkill(
        name="test_skill",
        description="A test",
        prompt_template="template",
    )
    cmd = ICoderSkillCommand(skill=skill, command_name="/test_skill")
    assert cmd.skill is skill
    assert cmd.command_name == "/test_skill"


def test_claude_skill_name_from_directory(tmp_path: Path) -> None:
    """ClaudeSkill.name is derived from the directory name."""
    _create_skill(tmp_path, "issue_analyse", 'description: "Analyse"\n', "body")
    skills = load_skills(tmp_path)
    assert skills[0].name == "issue_analyse"


def test_load_skills_no_skills_directory(tmp_path: Path) -> None:
    """load_skills returns empty list when .claude/skills doesn't exist."""
    skills = load_skills(tmp_path)
    assert skills == []
