# Step 1 — Add `mcp_config_ok` exit-code plumbing

**Read first:** `pr_info/steps/summary.md`.

This step is a small, self-contained, additive change to the exit-code logic. It adds the
new hard-fail signal to `_compute_exit_code` *before* anything computes or passes it, so it
can be tested in isolation. No parsing / rendering is touched here.

## WHERE
- Implementation: `src/mcp_coder/cli/commands/verify.py` — function `_compute_exit_code`.
- Tests: `tests/cli/commands/test_verify_exit_codes.py` — class `TestToolsExposedExitCode`
  is the pattern to follow (direct `_compute_exit_code(...)` calls). Add a sibling class
  `TestMcpConfigExitCode`.

## WHAT
Extend the signature (keep all existing params; add the new one **with a default** so
existing callers/tests are unaffected):

```python
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
    mcp_config_ok: bool | None = None,   # NEW
) -> int:
```

## HOW
- Add the new hard-fail branch near the top-level, provider-independent failures (next to
  `config_has_error`), because a broken `.mcp.json` breaks all providers:

```python
    # Malformed .mcp.json is provider-independent hard failure (exit 1).
    if mcp_config_ok is False:
        return 1
```
- Update the docstring `Args:` block to document `mcp_config_ok`:
  `None`=not checked / neutral (no effect), `True`=well-formed or empty (no effect),
  `False`=malformed → exit 1.

## ALGORITHM
No new algorithm — one guard clause:
```
if mcp_config_ok is False: return 1   # tri-state: None/True are no-ops
```

## DATA
- Input: `mcp_config_ok: bool | None` (tri-state, mirrors `claude_mcp_ok`).
- Output: `int` exit code (unchanged type/semantics).

## TDD — write tests first
Add `TestMcpConfigExitCode` to `test_verify_exit_codes.py` using the existing
`_make_claude_result()` / `_make_mlflow_result(installed=False)` helpers:
- `mcp_config_ok=False` → exit `1` (provider-independent — assert for both
  `"claude"` and `"langchain"` active providers).
- `mcp_config_ok=None` → exit `0` (neutral).
- `mcp_config_ok=True` → exit `0` (well-formed / empty is not a failure).

## Commit
One commit: signature + guard + docstring + the three exit-code tests, all checks green.

## LLM prompt
> Implement Step 1 as described in `pr_info/steps/step_1.md` (context in
> `pr_info/steps/summary.md`). Use TDD: first add `TestMcpConfigExitCode` to
> `tests/cli/commands/test_verify_exit_codes.py` covering `mcp_config_ok` values
> `False` (exit 1, both providers), `None` (exit 0), `True` (exit 0). Then add the
> `mcp_config_ok: bool | None = None` parameter to `_compute_exit_code` in
> `src/mcp_coder/cli/commands/verify.py`, wire a `if mcp_config_ok is False: return 1`
> guard next to the `config_has_error` check, and document the parameter. Use MCP
> filesystem tools only. After editing, run `mcp__mcp-tools-py__run_pylint_check`,
> `mcp__mcp-tools-py__run_pytest_check` (with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`),
> and `mcp__mcp-tools-py__run_mypy_check`; fix everything until all pass. Produce exactly one commit.
