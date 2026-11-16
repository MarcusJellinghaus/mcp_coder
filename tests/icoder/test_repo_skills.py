"""Tests for the repository's own ``.claude/skills`` frontmatter."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_coder.icoder.skills import ClaudeSkill, load_skills

REPO_ROOT = Path(__file__).resolve().parents[2]

SET_STATUS_TOOL = "mcp__mcp-workspace__github_issue_set_status"

STATUS_SKILLS = [
    "issue_approve",
    "plan_approve",
    "implementation_needs_rework",
    "implementation_approve",
    "implement_direct",
    "pr_comment_triage",
]


@pytest.fixture(name="repo_skills", scope="module")
def fixture_repo_skills() -> dict[str, ClaudeSkill]:
    """Load the repository's skills, keyed by directory name."""
    return {skill.name: skill for skill in load_skills(REPO_ROOT)}


def test_all_repo_skills_load(repo_skills: dict[str, ClaudeSkill]) -> None:
    """Every ``.claude/skills/*/SKILL.md`` parses (none skipped by the loader)."""
    skill_files = sorted((REPO_ROOT / ".claude" / "skills").glob("*/SKILL.md"))
    assert skill_files
    assert sorted(repo_skills) == sorted(f.parent.name for f in skill_files)


def test_pr_comment_triage_is_user_only(repo_skills: dict[str, ClaudeSkill]) -> None:
    """``pr_comment_triage`` carries write grants, so it must be user-only."""
    assert repo_skills["pr_comment_triage"].disable_model_invocation is True


@pytest.mark.parametrize("forbidden", ["set-status", "remote get-url"])
def test_no_obsolete_bash_grants(
    repo_skills: dict[str, ClaudeSkill], forbidden: str
) -> None:
    """No skill pre-approves the replaced ``set-status`` or dead ``get-url`` Bash."""
    offenders = [
        f"{name}: {entry}"
        for name, skill in repo_skills.items()
        for entry in skill.allowed_tools
        if forbidden in str(entry)
    ]
    assert not offenders


@pytest.mark.parametrize("skill_name", STATUS_SKILLS)
def test_status_skills_grant_set_status_tool(
    repo_skills: dict[str, ClaudeSkill], skill_name: str
) -> None:
    """Each skill that changes a workflow status pre-approves the MCP status tool."""
    assert SET_STATUS_TOOL in repo_skills[skill_name].allowed_tools
