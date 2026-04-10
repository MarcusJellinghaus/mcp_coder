"""Skill models and loader for iCoder slash commands."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter

from mcp_coder.icoder.core.command_registry import CommandRegistry
from mcp_coder.icoder.core.types import Command, Response

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
    """Discover and parse skills from <project_dir>/.claude/skills/*/SKILL.md.

    Returns:
        Parsed skill definitions found under the project skills directory.
    """
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


def _make_claude_handler(skill: ClaudeSkill) -> Callable[[list[str]], Response]:
    """Create handler for Claude Code provider (raw passthrough).

    Returns:
        Handler callable that produces a passthrough response.
    """

    def handler(args: list[str]) -> Response:
        return Response(send_to_llm=True)

    return handler


def _make_langchain_handler(skill: ClaudeSkill) -> Callable[[list[str]], Response]:
    """Create handler for langchain provider (expand prompt template).

    Returns:
        Handler callable that expands the skill prompt template.
    """

    def handler(args: list[str]) -> Response:
        arguments = " ".join(args)
        expanded = skill.prompt_template.replace("$ARGUMENTS", arguments).strip()
        return Response(send_to_llm=True, llm_text=expanded)

    return handler


def register_skill_commands(
    registry: CommandRegistry,
    skills: list[ClaudeSkill],
    provider: str,
) -> list[ICoderSkillCommand]:
    """Register skills as slash commands in the registry.

    Returns:
        List of ICoderSkillCommand for the successfully registered skills.
    """
    registered: list[ICoderSkillCommand] = []
    for skill in skills:
        command_name = "/" + skill.name.lower()
        # Check for collision with existing commands
        if registry.has_command(command_name):
            logger.warning(
                "Skill '%s' skipped: command %s already registered",
                skill.name,
                command_name,
            )
            continue

        if provider == "claude":
            handler = _make_claude_handler(skill)
        else:
            handler = _make_langchain_handler(skill)

        registry.add_command(
            Command(
                name=command_name,
                description=skill.description,
                handler=handler,
                show_in_help=False,
            )
        )
        registered.append(ICoderSkillCommand(skill=skill, command_name=command_name))

    return registered
