# Step 3: Fix `prompt_llm()` kwargs + add MCP edit smoke test

## LLM Prompt

> Implement Step 3 from `pr_info/steps/summary.md` (Issue #550).
> Fix the existing `prompt_llm()` call to pass `mcp_config` and `execution_dir`.
> Add `_run_mcp_edit_smoke_test()` function and call it from `execute_verify()`.
> Follow TDD: write tests first, then implement. Run all three code quality checks after changes.

## WHERE

| File | Action |
|------|--------|
| `tests/cli/commands/test_verify_orchestration.py` | Add test for `prompt_llm` kwargs |
| `tests/cli/commands/test_verify_exit_codes.py` | Add tests for smoke test pass/fail |
| `src/mcp_coder/cli/commands/verify.py` | Fix `prompt_llm()` kwargs, add `_run_mcp_edit_smoke_test()`, call from `execute_verify()` |

## WHAT

### Fix existing `prompt_llm()` call

```python
# BEFORE (line ~226 in execute_verify):
response = prompt_llm("Reply with OK", provider=active_provider, timeout=30)

# AFTER:
response = prompt_llm(
    "Reply with OK",
    provider=active_provider,
    timeout=30,
    mcp_config=mcp_config_resolved,
    execution_dir=str(project_dir),
)
```

### New function

```python
def _run_mcp_edit_smoke_test(
    project_dir: Path,
    provider: str,
    mcp_config: str,
    execution_dir: str,
    symbols: dict[str, str],
) -> str:
    """Run MCP edit smoke test. Returns formatted output line."""
```

## HOW

- `_run_mcp_edit_smoke_test()` is called from `execute_verify()` after MCP server health check, only when `mcp_config_resolved` is set
- Returns a string that `execute_verify()` prints
- Does NOT affect `_compute_exit_code` (informational only)

## ALGORITHM

```python
def _run_mcp_edit_smoke_test(project_dir, provider, mcp_config, execution_dir, symbols):
    label = "MCP edit smoke test"
    test_file = project_dir / ".mcp_coder_verify.md"
    try:
        test_file.write_text("A\n\nC\n", encoding="utf-8")
        prompt_llm(
            "Edit the file .mcp_coder_verify.md to insert a line 'B' between 'A' and 'C'",
            provider=provider, timeout=60,
            mcp_config=mcp_config, execution_dir=execution_dir,
        )
        content = test_file.read_text(encoding="utf-8")
        pos_a, pos_b, pos_c = content.find("A"), content.find("B"), content.find("C")
        if pos_a < pos_b < pos_c:
            return f"  {label:<20s} {symbols['success']} edit verified"
        else:
            return f"  {label:<20s} {symbols['warning']} edit not verified (B not found between A and C)"
    except Exception as exc:
        return f"  {label:<20s} {symbols['warning']} edit not verified ({exc})"
    finally:
        test_file.unlink(missing_ok=True)
```

### Integration in `execute_verify()`

```python
# After MCP server health check block (step 3a), before test prompt (step 3b):
if mcp_config_resolved:
    smoke_line = _run_mcp_edit_smoke_test(
        project_dir, active_provider, mcp_config_resolved,
        str(project_dir), symbols,
    )
    print(smoke_line)
```

## DATA

### Pass output
```
  MCP edit smoke test  [OK] edit verified
```

### Fail output
```
  MCP edit smoke test  [!!] edit not verified (B not found between A and C)
```

### Error output
```
  MCP edit smoke test  [!!] edit not verified (TimeoutError: ...)
```

## TESTS

### In `test_verify_orchestration.py`

1. **`test_prompt_llm_receives_mcp_config_and_execution_dir`** — Assert `prompt_llm` is called with `mcp_config=` and `execution_dir=` kwargs for the test prompt
   Note: Must also patch `mcp_coder.cli.commands.verify.verify_config` (see `test_verify_exit_codes.py` for pattern).

### In `test_verify_exit_codes.py`

2. **`test_smoke_test_pass_displays_ok`** — Mock `prompt_llm` to write "B" into the file, verify output contains `[OK] edit verified`
   Note: The `prompt_llm` mock needs a `side_effect` that writes the expected content to the test file, e.g.: `side_effect=lambda *a, **kw: test_file.write_text("A\nB\nC\n")`.
3. **`test_smoke_test_fail_displays_warning`** — Mock `prompt_llm` to do nothing (file unchanged), verify output contains `[!!] edit not verified`
4. **`test_smoke_test_error_displays_warning`** — Mock `prompt_llm` to raise, verify output contains `[!!] edit not verified`
5. **`test_smoke_test_does_not_affect_exit_code`** — Smoke test fails but exit code is still 0 (when provider ok)
6. **`test_smoke_test_cleans_up_file`** — After smoke test (pass or fail), `.mcp_coder_verify.md` does not exist
7. **`test_smoke_test_skipped_when_no_mcp_config`** — When `mcp_config_resolved` is None, smoke test line not in output

## COMMIT

```
feat(verify): add MCP edit smoke test and fix prompt_llm kwargs

- Pass mcp_config and execution_dir to prompt_llm() calls for
  consistency with LangChain MCP tool discovery
- Add _run_mcp_edit_smoke_test() that validates the LLM can edit a
  file via MCP tools. Informational only (does not affect exit code).

Refs #550
```
