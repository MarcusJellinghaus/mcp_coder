# Step 5: Rewrite `verify.py` as Orchestrator + Formatter

> **Context:** Read `pr_info/steps/summary.md` first. Depends on Steps 1–4.

## Goal

Rewrite `cli/commands/verify.py` to orchestrate the three domain verification
functions and format their output. This is the main user-facing change.

## Tests First

### WHERE: `tests/cli/commands/test_verify_orchestration.py` (new)

```python
class TestVerifyOrchestration:
    """Tests for the verify CLI orchestrator."""

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    def test_all_sections_printed(self, mock_provider, mock_claude, mock_lc, mock_mlflow, capsys) -> None:
        """All three sections appear in output."""
        mock_provider.return_value = ("claude", "config.toml")
        mock_claude.return_value = {"overall_ok": True, "cli_found": {"ok": True, "value": "YES"}, ...}
        mock_lc.return_value = {"overall_ok": True, ...}
        mock_mlflow.return_value = {"overall_ok": True, "installed": {"ok": False, "value": "not installed"}}
        result = execute_verify(_make_args())
        output = capsys.readouterr().out
        assert "BASIC VERIFICATION" in output
        assert "LLM PROVIDER" in output
        assert "MLFLOW" in output

    def test_exit_0_when_active_provider_works(self, ...) -> None:
        """Exit 0 when active provider succeeds."""
        ...

    def test_exit_1_when_active_provider_fails(self, ...) -> None:
        """Exit 1 when active provider (langchain) fails."""
        ...

    def test_exit_1_when_mlflow_enabled_but_misconfigured(self, ...) -> None:
        """Exit 1 when MLflow is enabled and has errors."""
        ...

    def test_exit_0_when_mlflow_not_installed(self, ...) -> None:
        """Exit 0 when MLflow not installed (informational)."""
        ...

    def test_claude_informational_when_langchain_active(self, ...) -> None:
        """Claude CLI section is informational (doesn't affect exit) when provider=langchain."""
        ...

    def test_check_models_passed_to_langchain(self, ...) -> None:
        """--check-models flag forwarded to verify_langchain."""
        ...


class TestResolveActiveProvider:
    """Tests for _resolve_active_provider helper."""

    @patch("mcp_coder.cli.commands.verify.get_config_values")
    def test_config_langchain(self, mock_config) -> None:
        mock_config.return_value = {("llm", "provider"): "langchain"}
        provider, source = _resolve_active_provider()
        assert provider == "langchain"
        assert source == "config.toml"

    @patch.dict(os.environ, {"MCP_CODER_LLM_PROVIDER": "langchain"})
    def test_env_var_override(self, ...) -> None:
        provider, source = _resolve_active_provider()
        assert provider == "langchain"
        assert "env var" in source

    def test_default_is_claude(self, ...) -> None:
        provider, source = _resolve_active_provider()
        assert provider == "claude"
        assert "default" in source
```

## Implementation

### WHERE: `src/mcp_coder/cli/commands/verify.py` (rewrite)

**WHAT:**
```python
def execute_verify(args: argparse.Namespace) -> int:
def _resolve_active_provider() -> tuple[str, str]:
def _format_section(title: str, result: dict, symbols: dict) -> str:
def _compute_exit_code(active_provider: str, claude_result: dict, langchain_result: dict, mlflow_result: dict) -> int:
```

**ALGORITHM for `execute_verify`:**
```
1. Get active provider via _resolve_active_provider()
2. Call verify_claude()
3. Call verify_langchain(check_models=args.check_models) if provider is langchain
4. Call verify_mlflow()
5. Print formatted output for each section
6. Return _compute_exit_code(...)
```

**ALGORITHM for `_compute_exit_code`:**
```
1. If active_provider == "claude": exit 1 if claude.overall_ok is False
2. If active_provider == "langchain": exit 1 if langchain.overall_ok is False
3. If mlflow result has "enabled" entry with ok=True AND mlflow.overall_ok is False: exit 1
4. Otherwise: exit 0
```

**ALGORITHM for `_format_section`:**
```
1. Print "=== {title} ===" header
2. For each key in result (skip "overall_ok"):
3.   Get ok, value from entry dict
4.   Pick success/failure symbol based on ok
5.   Print formatted line: "Label:  {symbol} {value}"
```

**HOW — Provider resolution:**
```python
def _resolve_active_provider() -> tuple[str, str]:
    """Returns (provider_name, source_description)."""
    env_val = os.environ.get("MCP_CODER_LLM_PROVIDER")
    if env_val:
        return env_val, "MCP_CODER_LLM_PROVIDER env var"

    config = get_config_values([("llm", "provider", None)])
    provider = config[("llm", "provider")]
    if provider:
        return provider, "config.toml"

    return "claude", "default"
```

**HOW — Output formatting (matches issue's example):**
```python
_LABEL_MAP = {
    # Claude section
    "cli_found": "Claude CLI Found",
    "cli_version": "Version",
    "cli_works": "Executable Works",
    "api_integration": "API Integration",
    # LangChain section
    "backend": "Backend",
    "model": "Model",
    "api_key": "API key",
    "langchain_core": "LangChain core",
    "backend_package": "Backend package",
    "test_prompt": "Test prompt",
    "available_models": "Available models",
    # MLflow section
    "installed": "MLflow installed",
    "enabled": "MLflow enabled",
    "tracking_uri": "Tracking URI",
    "connection": "Connection",
    "experiment": "Experiment",
    "artifact_location": "Artifact location",
}
```

**HOW — Section output for LLM Provider:**

The LLM Provider section always shows the active provider line first,
then delegates to either Claude or LangChain details:

```python
print(f"\n=== LLM PROVIDER ===")
print(f"Active provider:   {symbols['success']} {active_provider} (from {source})")
if active_provider == "langchain":
    _print_entries(langchain_result, symbols)
else:
    print(f"  (uses Claude CLI — see Basic Verification above)")
```

**DATA — `args` namespace expected fields:**
```python
args.check_models: bool  # from --check-models flag (Step 1)
```

## Checklist

- [ ] `execute_verify()` calls all 3 domain functions
- [ ] Output matches issue's example format (3 sections with `[OK]`/`[NO]`)
- [ ] `_resolve_active_provider()` checks env var > config > default
- [ ] Exit code: active provider determines pass/fail
- [ ] Exit code: MLflow enabled + broken = exit 1
- [ ] Exit code: MLflow not installed = exit 0
- [ ] `--check-models` forwarded to `verify_langchain()`
- [ ] Claude section is informational when `provider=langchain`
- [ ] All tests pass
