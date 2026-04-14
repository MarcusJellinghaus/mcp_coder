"""The /info command — runtime diagnostics."""

from __future__ import annotations

import importlib.metadata
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from mcp_coder.icoder.core.types import Response
from mcp_coder.llm.providers.claude.claude_executable_finder import (
    find_claude_executable,
)
from mcp_coder.prompts.prompt_loader import load_prompts
from mcp_coder.utils.mcp_verification import parse_claude_mcp_list

if TYPE_CHECKING:
    from mcp_coder.icoder.core.command_registry import CommandRegistry
    from mcp_coder.icoder.env_setup import RuntimeInfo
    from mcp_coder.llm.mcp_manager import MCPManager

_SENSITIVE = ("token", "key", "secret", "password", "credential")


def _redact_env_vars(env: dict[str, str]) -> dict[str, str]:
    """Redact env var values where key contains sensitive substrings.

    Matches case-insensitively: token, key, secret, password, credential.
    Redacted values replaced with '***'.

    Returns:
        Copy of the env dict with sensitive values replaced by '***'.
    """
    result: dict[str, str] = {}
    for k, v in env.items():
        if any(s in k.lower() for s in _SENSITIVE):
            result[k] = "***"
        else:
            result[k] = v
    return result


def _format_info(
    runtime_info: RuntimeInfo,
    mcp_manager: MCPManager | None,
) -> str:
    """Build the /info output string. All values re-read live.

    Returns:
        Formatted multi-line info string.
    """
    lines: list[str] = []
    lines.append("=== iCoder /info ===")
    lines.append(f"mcp-coder version: {importlib.metadata.version('mcp-coder')}")
    lines.append(f"Python:            {sys.version} ({sys.executable})")

    lines.append("")
    lines.append("Environments:")
    lines.append(f"  Tool env:    {runtime_info.tool_env_path}")
    lines.append(f"  Project env: {runtime_info.project_venv_path}")
    lines.append(f"  Project dir: {runtime_info.project_dir}")

    _sys_prompt, _proj_prompt, prompt_config = load_prompts(
        Path(runtime_info.project_dir) if runtime_info.project_dir else None
    )
    lines.append("")
    lines.append("Prompts:")
    lines.append(f"  System:  {prompt_config.system_prompt or '(shipped default)'}")
    lines.append(f"  Project: {prompt_config.project_prompt or '(shipped default)'}")
    lines.append(f"  Claude mode: {prompt_config.claude_system_prompt_mode}")

    if mcp_manager is not None:
        lines.append("")
        lines.append("MCP servers (langchain):")
        for s in mcp_manager.status():
            icon = "\u2713" if s.connected else "\u2717"
            state = "Connected" if s.connected else "Disconnected"
            lines.append(f"  {s.name}    {icon} {state}   ({s.tool_count} tools)")

    claude_exe = find_claude_executable(return_none_if_not_found=True)
    claude_mcp = parse_claude_mcp_list(
        runtime_info.env_vars, claude_executable=claude_exe
    )
    if claude_mcp is not None:
        lines.append("")
        lines.append("MCP servers (claude):")
        for status in claude_mcp:
            icon = "\u2713" if status.ok else "\u2717"
            lines.append(f"  {status.name}: {icon} {status.status_text}")

    # MCP_CODER_* env vars
    mcp_coder_vars = {
        k: v for k, v in sorted(os.environ.items()) if k.startswith("MCP_CODER_")
    }
    lines.append("")
    lines.append("MCP_CODER_* env vars:")
    if mcp_coder_vars:
        for k, v in mcp_coder_vars.items():
            lines.append(f"  {k}={v}")
    else:
        lines.append("  (none)")

    # Other env vars (redacted)
    other_vars = {
        k: v for k, v in sorted(os.environ.items()) if not k.startswith("MCP_CODER_")
    }
    redacted = _redact_env_vars(other_vars)
    lines.append("")
    lines.append("Other env vars (secrets redacted):")
    for k, v in redacted.items():
        lines.append(f"  {k}={v}")

    return "\n".join(lines)


def register_info(
    registry: CommandRegistry,
    runtime_info: RuntimeInfo,
    mcp_manager: MCPManager | None = None,
) -> None:
    """Register the /info command. Captures dependencies via closure."""

    @registry.register("/info", "Show runtime diagnostics")
    def handle_info(args: list[str]) -> Response:  # noqa: ARG001
        return Response(text=_format_info(runtime_info, mcp_manager))
