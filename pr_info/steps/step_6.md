# Step 6: Integration Tests and Final Validation

> **Context:** Read `pr_info/steps/summary.md` first. Depends on Steps 1–5.

## Goal

Add integration-level tests that validate the full `mcp-coder verify` flow
end-to-end, verify exit code logic across scenarios, and ensure existing
tests still pass.

## Tests

### WHERE: `tests/cli/commands/test_verify_integration.py` (new)

These tests exercise the full CLI path from `main()` through `execute_verify()`.

```python
class TestVerifyEndToEnd:
    """Integration tests for mcp-coder verify command."""

    @patch("mcp_coder.cli.commands.verify.verify_mlflow")
    @patch("mcp_coder.cli.commands.verify.verify_langchain")
    @patch("mcp_coder.cli.commands.verify.verify_claude")
    @patch("mcp_coder.cli.commands.verify._resolve_active_provider")
    @patch("sys.argv", ["mcp-coder", "verify"])
    def test_full_verify_output_format(self, mock_provider, mock_claude, mock_lc, mock_mlflow, capsys) -> None:
        """Output contains all three section headers."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _make_claude_result(ok=True)
        mock_lc.return_value = _make_langchain_result(ok=True)
        mock_mlflow.return_value = _make_mlflow_result(installed=False)
        exit_code = main()
        output = capsys.readouterr().out
        assert "=== BASIC VERIFICATION ===" in output
        assert "=== LLM PROVIDER ===" in output
        assert "=== MLFLOW ===" in output
        assert exit_code == 0

    @patch("sys.argv", ["mcp-coder", "verify", "--check-models"])
    def test_check_models_flag_parsed(self, ...) -> None:
        """--check-models flag reaches verify_langchain."""
        ...


class TestExitCodeMatrix:
    """Exhaustive exit code scenarios."""

    # Helper to build mock results
    ...

    def test_claude_active_claude_ok(self) -> None:
        """provider=claude, Claude works → exit 0."""
        ...

    def test_claude_active_claude_broken(self) -> None:
        """provider=claude, Claude broken → exit 1."""
        ...

    def test_langchain_active_langchain_ok_claude_broken(self) -> None:
        """provider=langchain, LangChain works, Claude broken → exit 0 (informational)."""
        ...

    def test_langchain_active_langchain_broken(self) -> None:
        """provider=langchain, LangChain broken → exit 1."""
        ...

    def test_mlflow_enabled_and_broken(self) -> None:
        """MLflow enabled but misconfigured → exit 1 regardless of provider."""
        ...

    def test_mlflow_not_installed(self) -> None:
        """MLflow not installed → exit 0 (informational)."""
        ...

    def test_mlflow_disabled(self) -> None:
        """MLflow installed but disabled → exit 0 (informational)."""
        ...

    def test_mlflow_enabled_and_healthy(self) -> None:
        """MLflow enabled and all checks pass → exit 0."""
        ...
```

### WHERE: Update `tests/cli/commands/test_verify.py` and `test_verify_command.py`

Update existing tests to work with the new function signatures:
- `verify_claude_cli_installation()` → `verify_claude()` (no args)
- `execute_verify(args)` now calls all 3 domain functions

**WHAT:** Update import paths and mock targets.

```python
# Old
@patch("mcp_coder.cli.main.execute_verify")
def test_verify_command_calls_verification_function(self, mock_verify):
    ...
    # This test still works — it mocks at the CLI level
```

## Implementation

No new production code in this step. Only tests and any small fixes discovered
during integration testing.

### Potential fixups

If integration tests reveal issues:
- Fix import paths
- Fix dict key naming mismatches between domain and formatter
- Fix edge cases in exit code logic
- Ensure `--check-models` defaults to `False` when not provided

### Run full test suite

```bash
# Run all verify-related tests
pytest tests/cli/commands/test_verify*.py tests/llm/test_mlflow_verify.py tests/llm/providers/langchain/test_langchain_verification.py -v

# Run full suite to check no regressions
pytest tests/ -v --timeout=60
```

## Checklist

- [ ] Integration tests cover full CLI path
- [ ] Exit code matrix: 8 scenarios all tested
- [ ] Existing `test_verify.py` and `test_verify_command.py` updated and passing
- [ ] `--check-models` flag parsed and forwarded correctly
- [ ] Full test suite passes with no regressions
- [ ] Output format matches issue's example
