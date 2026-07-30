# Step 1 — Adapter floor `>=0.3.0` + runtime capability check

**Reference:** read `pr_info/steps/summary.md` (Decision D3) before starting.

Pin the `langchain-mcp-adapters` floor to the version that exports the enforcement API, and add a
runtime check that fails fast with a clear message if the installed adapter lacks `tool_interceptors`.
Extract the check into a **reusable helper** so it can also be invoked at iCoder startup (Step 5)
**before** the first `convert_...(tool_interceptors=...)` call — otherwise a `<0.3.0` adapter raises a
raw `TypeError: unexpected keyword argument 'tool_interceptors'` when `MCPManager.tools()` builds
tools, beating the clear message. No gateway logic yet.

## WHERE
- `pyproject.toml` — `[project.optional-dependencies]` → `langchain-base`.
- `src/mcp_coder/llm/providers/langchain/agent.py` — new `_assert_tool_interceptors_supported()`
  helper, called from `_check_agent_dependencies()` (and reused at startup in Step 5).
- `tests/llm/providers/langchain/test_agent_dependencies.py` (new or extend the existing agent test module).

## WHAT
- `pyproject.toml`: change `"langchain-mcp-adapters>=0.1.0"` → `"langchain-mcp-adapters>=0.3.0"`.
- New reusable helper (importable by Step 5's startup block):
  ```python
  def _assert_tool_interceptors_supported() -> None:
      """Raise ImportError if the installed adapter lacks tool_interceptors."""
  ```
- Extend the existing function (signature unchanged) to call it after the current import checks for
  `langchain_mcp_adapters` and `langgraph` succeed:
  ```python
  def _check_agent_dependencies() -> None: ...
  ```

## HOW
- Keep the current `ImportError` behaviour for missing packages.
- `_assert_tool_interceptors_supported()`:
  ```python
  import inspect
  from langchain_mcp_adapters.tools import convert_mcp_tool_to_langchain_tool
  try:
      params = inspect.signature(convert_mcp_tool_to_langchain_tool).parameters
  except (TypeError, ValueError):
      # Not introspectable (e.g. the conftest MagicMock stand-in when the real
      # package is absent) — cannot determine capability, so do not block.
      return
  if "tool_interceptors" not in params:
      raise ImportError(
          "Permission enforcement requires langchain-mcp-adapters>=0.3.0 "
          "(the installed version does not support tool_interceptors). "
          "Upgrade with: pip install 'langchain-mcp-adapters>=0.3.0'"
      )
  ```
- **Introspection guard (conftest-mock collision):** the langchain conftest injects a `MagicMock`
  for `langchain_mcp_adapters.tools` when the real package is absent, so `inspect.signature(...)`
  on the mock misbehaves. The `try/except` above makes the check a no-op in that case; the
  real-install pass-test therefore runs on the `langchain_integration` marker path (real package),
  not under the mock.

## ALGORITHM
```
run existing missing-package checks -> raise ImportError if any missing
_assert_tool_interceptors_supported():
    import convert_mcp_tool_to_langchain_tool
    try: params = signature(convert).parameters
    except (TypeError, ValueError): return       # mock / non-introspectable -> skip
    if "tool_interceptors" not in params: raise ImportError(clear upgrade message)
```

## DATA
- Both helpers return `None`; raise `ImportError` with an actionable message on an unsupported
  adapter. Non-introspectable symbol (mock) → silently skips (test-only path).

## TDD tests (write first)
- `test_check_agent_dependencies_passes_with_supported_adapter` (**mark
  `@pytest.mark.langchain_integration`** — runs under the real install, not the conftest mock) —
  calls `_check_agent_dependencies()`; expects no raise.
- `test_assert_interceptors_rejects_missing_support` (unit) — monkeypatch
  `convert_mcp_tool_to_langchain_tool` with a stub whose **real** signature omits `tool_interceptors`;
  expect `ImportError` whose message names `langchain-mcp-adapters>=0.3.0`.
- `test_assert_interceptors_skips_non_introspectable` (unit) — monkeypatch with a `MagicMock` (as the
  conftest does); expect **no raise** (guard returns cleanly).

## Checks
Run `run_pylint_check`, `run_mypy_check`, `run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`, `run_ruff_check`, `run_lint_imports_check`. All green.

## Commit
`I2.3 step 1: raise langchain-mcp-adapters floor to >=0.3.0 with capability check`

## LLM prompt
> Implement Step 1 of the I2.3 enforcement-gateway plan. Read `pr_info/steps/summary.md` and
> `pr_info/steps/step_1.md`. Following TDD, first add the tests, then raise the
> `langchain-mcp-adapters` floor to `>=0.3.0` in `pyproject.toml` and add a reusable
> `_assert_tool_interceptors_supported()` helper in
> `src/mcp_coder/llm/providers/langchain/agent.py` that raises a clear `ImportError` when
> `convert_mcp_tool_to_langchain_tool` lacks a `tool_interceptors` parameter, guarding the
> `inspect.signature` call so the conftest `MagicMock` stand-in is skipped (no raise). Call it from
> `_check_agent_dependencies()`. Put the real-install pass-test on the `langchain_integration` marker.
> Use MCP tools only. Make pylint, mypy(strict), ruff, pytest (fast markers), and lint-imports all
> pass, then produce exactly one commit.
