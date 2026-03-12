"""Agent utilities for MCP tool-use support in the LangChain provider.

Provides environment variable substitution and MCP server configuration loading
for the LangChain agent mode (issue #517).
"""

import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

AGENT_MAX_STEPS: int = 50

_KNOWN_FIELDS = {"command", "args", "env", "transport"}


def _resolve_env_vars(value: str, env: dict[str, str]) -> str:
    """Replace ``${VAR}`` placeholders in *value* with values from *env*.

    Unknown variables are left as-is (``${UNKNOWN}`` stays unchanged).
    Uses a single-pass ``re.sub`` so replacement values that themselves
    contain ``${…}`` patterns are **not** re-substituted.
    """
    pattern = r"\$\{([^}]+)\}"

    def _replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return env.get(var_name, match.group(0))

    return re.sub(pattern, _replacer, value)


def _load_mcp_server_config(
    mcp_config_path: str,
    env_vars: dict[str, str] | None = None,
) -> dict[str, dict[str, object]]:
    """Load an ``.mcp.json`` file and resolve ``${VAR}`` placeholders.

    Parameters
    ----------
    mcp_config_path:
        Absolute path to the ``.mcp.json`` configuration file.
        (Callers should use ``resolve_mcp_config_path()`` from ``cli/utils.py``.)
    env_vars:
        Optional extra environment variables.  These are merged on top of
        ``os.environ`` (i.e. *env_vars* wins on conflicts).

    Returns
    -------
    dict
        Mapping of server names to their resolved configuration, suitable for
        ``MultiServerMCPClient``.
    """
    path = Path(mcp_config_path)
    with open(path, encoding="utf-8") as fh:
        raw_config: dict[str, object] = json.load(fh)

    # Build merged environment: os.environ as base, env_vars overrides
    merged_env: dict[str, str] = {**os.environ, **(env_vars or {})}

    servers_raw = raw_config.get("mcpServers")
    if not isinstance(servers_raw, dict):
        raise ValueError(
            f"Expected 'mcpServers' dict in {mcp_config_path}, "
            f"got {type(servers_raw).__name__}"
        )

    result: dict[str, dict[str, object]] = {}

    for server_name, server_cfg in servers_raw.items():
        if not isinstance(server_cfg, dict):
            logger.warning(
                "Skipping non-dict server entry %r in %s",
                server_name,
                mcp_config_path,
            )
            continue

        resolved: dict[str, object] = {}

        for key, value in server_cfg.items():
            if key not in _KNOWN_FIELDS:
                logger.warning(
                    "Unknown field %r (value: %r) in server %r — ignoring",
                    key,
                    value,
                    server_name,
                )
                continue

            if key == "command" and isinstance(value, str):
                resolved["command"] = _resolve_env_vars(value, merged_env)
            elif key == "args" and isinstance(value, list):
                resolved["args"] = [
                    (
                        _resolve_env_vars(item, merged_env)
                        if isinstance(item, str)
                        else item
                    )
                    for item in value
                ]
            elif key == "env" and isinstance(value, dict):
                resolved["env"] = {
                    k: _resolve_env_vars(v, merged_env) if isinstance(v, str) else v
                    for k, v in value.items()
                }
            elif key == "transport":
                resolved["transport"] = value
            else:
                resolved[key] = value

        # Always set transport to stdio
        resolved["transport"] = "stdio"

        result[server_name] = resolved

    return result
