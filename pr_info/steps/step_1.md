# Step 1 — Adapter floor `>=0.3.0` + runtime capability check

**Reference:** read `pr_info/steps/summary.md` (Decision D3) before starting.

Pin the `langchain-mcp-adapters` floor to the version that exports the enforcement API, and add a
runtime check that fails fast with a clear message if the installed adapter lacks `tool_interceptors`.
No gateway logic yet.

## WHERE
- `pyproject.toml` — `[project.optional-dependencies]` → `langchain-base`.
- `src/mcp_coder/llm/providers/langchain/agent.py` — `_check_agent_dependencies()`.
- `tests/llm/providers/langchain/test_agent_dependencies.py` (new or extend the existing agent test module).

## WHAT
- `pyproject.toml`: change `"langchain-mcp-adapters>=0.1.0"` → `"langchain-mcp-adapters>=0.3.0"`.
- Extend the existing function (signature unchanged):
  ```python
  def _check_agent_dependencies() -> None: ...
  ```
  After the current import checks for `langchain_mcp_adapters` and `langgraph` succeed, assert the
  interceptor capability.

## HOW
- Keep the current `ImportError` behaviour for missing packages.
- Add, at the end of the function:
  ```python
  import inspect
  from langchain_mcp_adapters.tools import convert_mcp_tool_to_langchain_tool
  if "tool_interceptors" not in inspect.signature(
      convert_mcp_tool_to_langchain_tool
  ).parameters:
      raise ImportError(
          "Permission enforcement requires langchain-mcp-adapters>=0.3.0 "
          "(the installed version does not support tool_interceptors). "
          "Upgrade with: pip install 'langchain-mcp-adapters>=0.3.0'"
      )
  ```

## ALGORITHM
```
run existing missing-package checks -> raise ImportError if any missing
import convert_mcp_tool_to_langchain_tool
if "tool_interceptors" not in signature(convert).parameters:
    raise ImportError(clear upgrade message)
```

## DATA
- Returns `None`; raises `ImportError` with an actionable message on unsupported/missing adapter.

## TDD tests (write first)
- `test_check_agent_dependencies_passes_with_supported_adapter` — calls `_check_agent_dependencies()`
  with the real install; expects no raise.
- `test_check_agent_dependencies_rejects_missing_interceptor_support` — monkeypatch
  `convert_mcp_tool_to_langchain_tool` with a stub whose signature omits `tool_interceptors`; expect
  `ImportError` whose message names `langchain-mcp-adapters>=0.3.0`.

## Checks
Run `run_pylint_check`, `run_mypy_check`, `run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`, `run_ruff_check`, `run_lint_imports_check`. All green.

## Commit
`I2.3 step 1: raise langchain-mcp-adapters floor to >=0.3.0 with capability check`

## LLM prompt
> Implement Step 1 of the I2.3 enforcement-gateway plan. Read `pr_info/steps/summary.md` and
> `pr_info/steps/step_1.md`. Following TDD, first add the two tests, then raise the
> `langchain-mcp-adapters` floor to `>=0.3.0` in `pyproject.toml` and extend
> `_check_agent_dependencies()` in `src/mcp_coder/llm/providers/langchain/agent.py` to raise a clear
> `ImportError` when `convert_mcp_tool_to_langchain_tool` lacks a `tool_interceptors` parameter. Use
> MCP tools only. Make pylint, mypy(strict), ruff, pytest (fast markers), and lint-imports all pass,
> then produce exactly one commit.
