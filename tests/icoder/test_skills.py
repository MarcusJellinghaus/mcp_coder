"""Tests for skill models and loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_coder.icoder.core.command_registry import (
    CommandRegistry,
    create_default_registry,
)
from mcp_coder.icoder.skills import (
    ClaudeSkill,
    ICoderSkillCommand,
    load_skills,
    register_skill_commands,
)


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


# --- register_skill_commands tests ---


def _make_skill(name: str = "my_skill", prompt: str = "Do $ARGUMENTS") -> ClaudeSkill:
    return ClaudeSkill(name=name, description=f"Skill {name}", prompt_template=prompt)


def test_register_skill_commands_claude_provider() -> None:
    """Claude provider: handler returns Response(send_to_llm=True) with no llm_text."""
    registry = CommandRegistry()
    skill = _make_skill()
    registered = register_skill_commands(registry, [skill], "claude")
    assert len(registered) == 1
    resp = registry.dispatch("/my_skill some args")
    assert resp is not None
    assert resp.send_to_llm is True
    assert resp.llm_text is None


def test_register_skill_commands_langchain_provider() -> None:
    """Langchain provider: handler returns Response(send_to_llm=True, llm_text=expanded)."""
    registry = CommandRegistry()
    skill = _make_skill(prompt="Analyse $ARGUMENTS please")
    register_skill_commands(registry, [skill], "langchain")
    resp = registry.dispatch("/my_skill issue 42")
    assert resp is not None
    assert resp.send_to_llm is True
    assert resp.llm_text == "Analyse issue 42 please"


def test_register_skill_commands_langchain_substitutes_arguments() -> None:
    """$ARGUMENTS in prompt template is replaced with user args."""
    registry = CommandRegistry()
    skill = _make_skill(prompt="Fix $ARGUMENTS now")
    register_skill_commands(registry, [skill], "langchain")
    resp = registry.dispatch("/my_skill bug 123")
    assert resp is not None
    assert resp.llm_text == "Fix bug 123 now"


def test_register_skill_commands_langchain_empty_arguments() -> None:
    """Empty args: $ARGUMENTS replaced with empty string, whitespace stripped."""
    registry = CommandRegistry()
    skill = _make_skill(prompt="Do $ARGUMENTS stuff")
    register_skill_commands(registry, [skill], "langchain")
    resp = registry.dispatch("/my_skill")
    assert resp is not None
    assert resp.llm_text == "Do  stuff"


def test_register_skill_commands_skips_builtin_collision(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Skill matching a built-in command name is skipped with warning."""
    registry = create_default_registry()
    skill = _make_skill(name="help")  # collides with /help
    registered = register_skill_commands(registry, [skill], "claude")
    assert len(registered) == 0
    assert (
        "already registered" in caplog.text.lower() or "skipping" in caplog.text.lower()
    )


def test_register_skill_commands_autocomplete() -> None:
    """Registered skills appear in filter_by_input (autocomplete)."""
    registry = CommandRegistry()
    skill = _make_skill(name="analyse")
    register_skill_commands(registry, [skill], "claude")
    matches = registry.filter_by_input("/ana")
    assert any(c.name == "/analyse" for c in matches)


def test_register_skill_commands_not_in_help() -> None:
    """Registered skills have show_in_help=False."""
    registry = CommandRegistry()
    skill = _make_skill()
    register_skill_commands(registry, [skill], "claude")
    all_cmds = registry.get_all()
    skill_cmd = [c for c in all_cmds if c.name == "/my_skill"][0]
    assert skill_cmd.show_in_help is False


def test_register_skill_commands_multiple_skills() -> None:
    """Multiple skills are all registered."""
    registry = CommandRegistry()
    skills = [_make_skill(name="skill_a"), _make_skill(name="skill_b")]
    registered = register_skill_commands(registry, skills, "claude")
    assert len(registered) == 2
    names = {r.command_name for r in registered}
    assert names == {"/skill_a", "/skill_b"}
