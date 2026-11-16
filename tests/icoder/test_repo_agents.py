"""Tests for the repository's own ``.claude/agents`` frontmatter."""

from __future__ import annotations

import json
from pathlib import Path

import frontmatter
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
SETTINGS_LOCAL = REPO_ROOT / ".claude" / "settings.local.json"

ALLOW_DECISION = '"permissionDecision":"allow"'

# Existing agents: their extra (not allow-listed) tools, granted by an allow hook.
HOOKED_AGENTS: dict[str, set[str]] = {
    "commit-pusher": {
        "mcp__mcp-workspace__git_commit",
        "mcp__mcp-workspace__git_push",
    },
    "issue-updater": {"mcp__mcp-workspace__github_issue_edit"},
    "issue-approver": {"mcp__mcp-workspace__github_issue_set_status"},
}

# New agents: every tool allow-listed, no hook.
ENGINEER_AGENTS = ["issue-analyst", "plan-engineer", "code-engineer"]

AgentMeta = dict[str, object]


def _str_list(meta: AgentMeta, key: str) -> list[str]:
    """Return a frontmatter list field as strings (missing -> empty)."""
    value = meta.get(key, [])
    assert isinstance(value, list), f"'{key}' must be a list"
    return [str(item) for item in value]


def _skill_meta(name: str) -> AgentMeta:
    """Load the frontmatter of ``.claude/skills/<name>/SKILL.md``."""
    return dict(frontmatter.load(str(SKILLS_DIR / name / "SKILL.md")).metadata)


@pytest.fixture(name="repo_agents", scope="module")
def fixture_repo_agents() -> dict[str, AgentMeta]:
    """Load every agent's frontmatter, keyed by file stem."""
    return {
        path.stem: dict(frontmatter.load(str(path)).metadata)
        for path in sorted(AGENTS_DIR.glob("*.md"))
    }


@pytest.fixture(name="allow_list", scope="module")
def fixture_allow_list() -> set[str]:
    """The ``permissions.allow`` entries of ``.claude/settings.local.json``."""
    settings = json.loads(SETTINGS_LOCAL.read_text(encoding="utf-8"))
    return set(settings["permissions"]["allow"])


def test_every_agent_is_classified(repo_agents: dict[str, AgentMeta]) -> None:
    """Each agent file is either a hooked agent or an engineer agent."""
    assert sorted(repo_agents) == sorted([*HOOKED_AGENTS, *ENGINEER_AGENTS])


def test_no_permission_mode(repo_agents: dict[str, AgentMeta]) -> None:
    """No agent sets ``permissionMode`` (ignored under ``acceptEdits``)."""
    offenders = [name for name, meta in repo_agents.items() if "permissionMode" in meta]
    assert not offenders


@pytest.mark.parametrize("agent", ENGINEER_AGENTS)
def test_engineer_agents_have_no_skill_or_bash(
    repo_agents: dict[str, AgentMeta], agent: str
) -> None:
    """Engineer agents get neither the Skill tool nor Bash."""
    tools = _str_list(repo_agents[agent], "tools")
    assert tools
    assert not [t for t in tools if t == "Skill" or t.startswith("Bash")]


@pytest.mark.parametrize("agent", ENGINEER_AGENTS)
def test_engineer_agent_tools_are_allow_listed(
    repo_agents: dict[str, AgentMeta], allow_list: set[str], agent: str
) -> None:
    """Every non-Bash tool of an engineer agent is in the allow-list (no hook)."""
    meta = repo_agents[agent]
    assert "hooks" not in meta
    tools = _str_list(meta, "tools")
    missing = [t for t in tools if not t.startswith("Bash") and t not in allow_list]
    assert not missing


@pytest.mark.parametrize("agent", sorted(HOOKED_AGENTS))
def test_hooked_agent_allow_hook(
    repo_agents: dict[str, AgentMeta], allow_list: set[str], agent: str
) -> None:
    """One PreToolUse hook; its matcher is exactly the agent's extra tools."""
    meta = repo_agents[agent]
    extra = HOOKED_AGENTS[agent]
    assert set(_str_list(meta, "tools")) - allow_list == extra

    hooks = meta.get("hooks")
    assert isinstance(hooks, dict)
    entries = hooks["PreToolUse"]
    assert isinstance(entries, list) and len(entries) == 1
    entry = entries[0]
    assert set(str(entry["matcher"]).split("|")) == extra
    commands = entry["hooks"]
    assert isinstance(commands, list) and commands
    for command in commands:
        assert command["type"] == "command"
        assert ALLOW_DECISION in command["command"]


def test_preloaded_skills_are_model_invocable(
    repo_agents: dict[str, AgentMeta],
) -> None:
    """Every ``skills:`` entry exists and is not user-only (else not preloaded)."""
    preloaded = {
        skill for meta in repo_agents.values() for skill in _str_list(meta, "skills")
    }
    assert preloaded
    for skill in sorted(preloaded):
        assert (SKILLS_DIR / skill / "SKILL.md").is_file(), skill
        assert not _skill_meta(skill).get("disable-model-invocation"), skill


def test_preloaded_skill_tools_in_agent_tools(
    repo_agents: dict[str, AgentMeta],
) -> None:
    """``skills:`` injects text, not tools: ``tools:`` lists each skill tool."""
    missing = [
        f"{agent}: {skill}: {tool}"
        for agent, meta in repo_agents.items()
        for skill in _str_list(meta, "skills")
        for tool in _str_list(_skill_meta(skill), "allowed-tools")
        if tool not in _str_list(meta, "tools")
    ]
    assert not missing
