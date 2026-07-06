"""Compute the CLI exit code from provider and verification results."""

from typing import Any


def _compute_exit_code(
    active_provider: str,
    claude_result: dict[str, Any],
    langchain_result: dict[str, Any] | None,
    mlflow_result: dict[str, Any],
    test_prompt_ok: bool = True,
    mcp_result: dict[str, Any] | None = None,
    config_has_error: bool = False,
    claude_mcp_ok: bool | None = None,
    github_result: dict[str, Any] | None = None,
    git_result: dict[str, Any] | None = None,
    tools_exposed_ok: bool | None = None,
    mcp_config_ok: bool | None = None,
) -> int:
    """Compute CLI exit code from verification results.

    Exit 1 when the config has errors, the active provider fails, when MLflow
    is enabled but broken, when the test prompt failed, when GitHub verification
    failed, when git verification failed, when MCP servers failed (langchain
    only), or when Claude MCP servers failed (claude only).

    Args:
        active_provider: The active LLM provider name.
        claude_result: Claude verification result dict.
        langchain_result: LangChain verification result dict, or None.
        mlflow_result: MLflow verification result dict.
        test_prompt_ok: Whether the test prompt succeeded.
        mcp_result: MCP server health check result dict, or None.
        config_has_error: Whether config verification found errors (invalid TOML).
        claude_mcp_ok: Claude MCP server status. None=not checked (no effect),
            True=all ok, False=failure (exit 1 when claude active).
        github_result: GitHub verification result dict, or None.
        git_result: Git verification result dict, or None.
        tools_exposed_ok: Claude tools-exposed status. None=neutral (no effect),
            True=connected with tools, False=fatal/0-tools (exit 1 when claude
            active).
        mcp_config_ok: `.mcp.json` validity. None=not checked / neutral (no
            effect), True=well-formed or empty (no effect), False=malformed
            (exit 1, provider-independent).

    Returns:
        Exit code (0 if all checks pass, 1 if any critical check failed).
    """
    # Config error (invalid TOML) always means exit 1
    if config_has_error:
        return 1

    # Malformed .mcp.json is provider-independent hard failure (exit 1).
    if mcp_config_ok is False:
        return 1

    # Test prompt failure always means exit 1
    if not test_prompt_ok:
        return 1

    # GitHub failure always means exit 1 (provider-independent)
    if github_result is not None and not github_result.get("overall_ok"):
        return 1

    # Git failure always means exit 1 (provider-independent)
    if git_result is not None and not git_result.get("overall_ok"):
        return 1

    # Active provider determines primary pass/fail
    if active_provider == "claude" and not claude_result.get("overall_ok"):
        return 1
    if active_provider == "langchain":
        if langchain_result is None or not langchain_result.get("overall_ok"):
            return 1

    # MCP server failures affect exit code when langchain is active
    if (
        active_provider == "langchain"
        and mcp_result
        and not mcp_result.get("overall_ok")
    ):
        return 1

    # Claude MCP failures affect exit code when claude is active
    if active_provider == "claude" and claude_mcp_ok is False:
        return 1

    # Claude tools-exposed failure affects exit code when claude is active
    # (fatal server or connected-but-0-tools). pending -> None (no effect).
    if active_provider == "claude" and tools_exposed_ok is False:
        return 1

    # MLflow: only fail if enabled AND broken
    mlflow_enabled = mlflow_result.get("enabled", {})
    if isinstance(mlflow_enabled, dict) and mlflow_enabled.get("ok") is True:
        if not mlflow_result.get("overall_ok"):
            return 1

    return 0


def _collect_install_hints(result: dict[str, Any]) -> list[str]:
    """Collect install_hint values from failed entries in a verification result.

    Args:
        result: Verification result dict from a domain verify function.

    Returns:
        List of install hint strings from failed entries.
    """
    hints: list[str] = []
    for _key, entry in result.items():
        if isinstance(entry, dict) and not entry.get("ok") and "install_hint" in entry:
            hints.append(entry["install_hint"])
    return hints
