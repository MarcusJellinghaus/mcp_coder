# Step 1: Add `github_result` to `_compute_exit_code()` + exit code tests

**See:** `pr_info/steps/summary.md` for full context.

## LLM Prompt

> Add a `github_result: dict[str, Any] | None = None` parameter to `_compute_exit_code()`
> in `src/mcp_coder/cli/commands/verify.py`. When `github_result` is provided and
> `github_result["overall_ok"]` is False, return exit code 1. This check must be
> **provider-independent** — place it after the config/test-prompt checks but before
> the active-provider check. Then add tests in `test_verify_exit_codes.py`.
> See `pr_info/steps/summary.md` for full context.

## WHERE

- `src/mcp_coder/cli/commands/verify.py` — `_compute_exit_code()` function (line ~363)
- `tests/cli/commands/test_verify_exit_codes.py` — `TestComputeExitCode` class

## WHAT

Modify existing function signature:

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
    github_result: dict[str, Any] | None = None,  # NEW
) -> int:
```

## HOW

- Add parameter at the end (keyword-only by convention, default `None`)
- Insert check after `test_prompt_ok` check, before active-provider check
- No import changes needed in this step

## ALGORITHM

```
if github_result is not None and not github_result.get("overall_ok"):
    return 1
```

## DATA

- Input: `github_result` — same shape as other verify results: `{"overall_ok": bool, "key": {"ok": bool, "value": str, ...}, ...}`
- Output: unchanged — `int` (0 or 1)

## TESTS (write first)

Add to `TestComputeExitCode` in `test_verify_exit_codes.py`:

1. `test_github_failure_returns_exit_1` — `github_result={"overall_ok": False}` → exit 1
2. `test_github_ok_does_not_affect_exit` — `github_result={"overall_ok": True}` → exit 0
3. `test_github_none_does_not_affect_exit` — `github_result=None` → exit 0 (default)
4. `test_github_failure_exit_1_regardless_of_provider` — both `"claude"` and `"langchain"` return 1

Use existing helpers `_claude_ok()`, `_langchain_ok()`, `_mlflow_not_installed()`.
