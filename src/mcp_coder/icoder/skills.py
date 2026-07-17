"""Skill models and loader for iCoder slash commands."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter

from mcp_coder.icoder.core.command_registry import CommandRegistry
from mcp_coder.icoder.core.types import Command, Response, SendToLLM

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClaudeSkill:
    """Full Claude Code skill spec parsed from SKILL.md."""

    name: str  # directory name (e.g. "issue_analyse")
    description: str  # frontmatter 'description'
    prompt_template: str  # markdown body
    argument_hint: str | None = None  # frontmatter 'argument-hint'
    # Parsed for Claude-format fidelity but intentionally UNREAD at runtime
    # (#1040). In the langchain/TUI path every slash command is user-initiated
    # (model output never reaches handle_input/dispatch — see AppCore module
    # docstring), so the flag's invariant "the LLM may not invoke this skill"
    # holds structurally for all commands. Do NOT add a runtime reader that
    # skips command registration: that would wrongly hide human-invocable
    # skills. Coupled to I1.1/M2, where skill frames can override `never`.
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


def _meta_str(meta: dict[str, object], key: str, skill_file: Path) -> str | None:
    """Return meta[key] as str or None; raise ValueError on type mismatch.

    Returns:
        The value as a string, or None when the key is absent or value is None.

    Raises:
        ValueError: If ``meta[key]`` exists but is not a string.
    """
    value = meta.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(
            f"{skill_file}: frontmatter field '{key}' must be a string, "
            f"got {type(value).__name__}"
        )
    return value


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

        try:
            description = _meta_str(meta, "description", skill_file) or ""
            argument_hint = _meta_str(meta, "argument-hint", skill_file)
            model = _meta_str(meta, "model", skill_file)
            effort = _meta_str(meta, "effort", skill_file)
            context = _meta_str(meta, "context", skill_file)
            agent = _meta_str(meta, "agent", skill_file)
            shell = _meta_str(meta, "shell", skill_file)
        except ValueError:
            logger.warning(
                "Invalid frontmatter in %s, skipping", skill_file, exc_info=True
            )
            continue

        skill = ClaudeSkill(
            name=subdir.name,
            description=description,
            prompt_template=post.content.strip(),
            argument_hint=argument_hint,
            disable_model_invocation=bool(meta.get("disable-model-invocation", False)),
            user_invocable=bool(user_invocable),
            allowed_tools=allowed_tools,
            model=model,
            effort=effort,
            context=context,
            agent=agent,
            hooks=hooks,
            paths=paths,
            shell=shell,
        )
        results.append(skill)

    return results


def _make_claude_handler(skill: ClaudeSkill) -> Callable[[list[str]], Response]:
    """Create handler for Claude Code provider (raw passthrough).

    Returns:
        Handler callable that produces a passthrough response.
    """

    def handler(args: list[str]) -> Response:
        # Empty text → AppCore resolves it to the original user input.
        return Response(actions=(SendToLLM(text=""),))

    return handler


def _make_langchain_handler(skill: ClaudeSkill) -> Callable[[list[str]], Response]:
    """Create handler for langchain provider (expand prompt template).

    Returns:
        Handler callable that expands the skill prompt template.
    """

    def handler(args: list[str]) -> Response:
        arguments = " ".join(args)
        expanded = skill.prompt_template.replace("$ARGUMENTS", arguments).strip()
        return Response(
            actions=(
                SendToLLM(
                    text=expanded,
                    allowed_tools=tuple(skill.allowed_tools) or None,
                ),
            )
        )

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
