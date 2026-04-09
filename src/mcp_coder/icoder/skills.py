"""Skill models and loader for iCoder slash commands."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClaudeSkill:
    """Full Claude Code skill spec parsed from SKILL.md."""

    name: str  # directory name (e.g. "issue_analyse")
    description: str  # frontmatter 'description'
    prompt_template: str  # markdown body
    argument_hint: str | None = None  # frontmatter 'argument-hint'
    disable_model_invocation: bool = False
    user_invocable: bool = True
    allowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    effort: str | None = None
    context: str | None = None
    agent: str | None = None
    hooks: dict[str, object] | None = None
    paths: list[str] | None = None
    shell: str | None = None


@dataclass(frozen=True)
class ICoderSkillCommand:
    """Thin wrapper for iCoder runtime. Holds skill + command name."""

    skill: ClaudeSkill
    command_name: str  # e.g. "/issue_analyse"


def load_skills(project_dir: Path) -> list[ClaudeSkill]:
    """Discover and parse skills from <project_dir>/.claude/skills/*/SKILL.md."""
    skills_dir = project_dir / ".claude" / "skills"
    if not skills_dir.is_dir():
        return []

    results: list[ClaudeSkill] = []
    for subdir in sorted(skills_dir.iterdir()):
        if not subdir.is_dir():
            continue
        skill_file = subdir / "SKILL.md"
        if not skill_file.is_file():
            logger.warning("No SKILL.md in %s, skipping", subdir.name)
            continue
        try:
            post = frontmatter.load(str(skill_file))
        except Exception:
            logger.warning("Failed to parse %s, skipping", skill_file, exc_info=True)
            continue

        meta = post.metadata
        user_invocable = meta.get("user-invocable", True)
        if user_invocable is False:
            continue

        allowed_tools_raw = meta.get("allowed-tools", [])
        allowed_tools = allowed_tools_raw if isinstance(allowed_tools_raw, list) else []

        paths_raw = meta.get("paths")
        paths = paths_raw if isinstance(paths_raw, list) else None

        hooks_raw = meta.get("hooks")
        hooks = hooks_raw if isinstance(hooks_raw, dict) else None

        skill = ClaudeSkill(
            name=subdir.name,
            description=meta.get("description", ""),
            prompt_template=post.content.strip(),
            argument_hint=meta.get("argument-hint"),
            disable_model_invocation=bool(meta.get("disable-model-invocation", False)),
            user_invocable=bool(user_invocable),
            allowed_tools=allowed_tools,
            model=meta.get("model"),
            effort=meta.get("effort"),
            context=meta.get("context"),
            agent=meta.get("agent"),
            hooks=hooks,
            paths=paths,
            shell=meta.get("shell"),
        )
        results.append(skill)

    return results
