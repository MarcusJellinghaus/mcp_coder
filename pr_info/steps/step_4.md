# Step 4 — Workflow failure output names unavailable MCP servers

**Commit:** `feat: surface McpServersUnavailableError in workflow failure output`

Implements acceptance item 4. Independent of Steps 2 & 3. Detection-only — the
guard already raised the typed error in-band; **no re-probing** (Decision 6).
See `summary.md`.

## WHERE
- **Impl (formatter):** `src/mcp_coder/workflow_utils/failure_handling.py`
- **Wiring:**
  - `src/mcp_coder/workflows/implement/task_processing.py`
  - `src/mcp_coder/workflows/implement/core.py`
  - `src/mcp_coder/workflows/create_plan/core.py`
  - `src/mcp_coder/workflows/create_pr/helpers.py`
- **Tests:** `tests/workflow_utils/test_failure_handling.py`

## WHAT
```python
def format_mcp_unavailable_message(error: "McpServersUnavailableError") -> str:
    """Build a clear, server-naming failure message for the typed guard error.

    Example: "MCP servers unavailable: mcp-tools-py (failed), mcp-workspace
    (unknown). The Claude session started without its configured tools and was
    aborted; check the MCP server logs and .mcp.json."
    """
```
Import the typed error at module top (allowed downward dep — see summary):
```python
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
```

## HOW
The guard's own message already names servers, but it is lost where an inner
broad `except Exception` collapses it to a generic reason. Fix the one place
that happens and route the other workflows' boundaries through the formatter:

- **implement / task_processing.py** — in `process_single_task` (~line 394), the
  LLM call is wrapped by `except LLMTimeoutError` then a broad `except Exception ->
  return False, "error"` (~lines 501-505). Add, **above** that broad handler
  (~line 501):
  ```python
  except McpServersUnavailableError:
      raise   # don't mask as a generic "error"; let the orchestrator format it
  ```
  Note: the re-raise lives in `process_single_task`; `process_task_with_retry`
  (~line 561) has no broad catch — it merely loops over `process_single_task`, so
  the typed error propagates through it transitively.
- **implement / core.py** — at the orchestrator safety-net `except Exception`
  that builds the `FailureCategory.GENERAL` failure, detect the typed error and
  use the formatter for the message:
  ```python
  message = (format_mcp_unavailable_message(exc)
             if isinstance(exc, McpServersUnavailableError) else <existing message>)
  ```
- **create_plan / core.py** — the prompt functions only catch `LLMTimeoutError`,
  so the typed error already propagates to the orchestrator. At its failure
  boundary, when the caught exception is `McpServersUnavailableError`, build the
  `WorkflowFailure.message` via `format_mcp_unavailable_message`.
- **create_pr / helpers.py** — `handle_create_pr_failure` already takes a
  `message: str`. Callers that catch the typed error pass
  `format_mcp_unavailable_message(e)` as `message`; no signature change needed.

Reuse existing `FailureCategory` values (GENERAL / `pr_creating_failed`) — **no
new enum** (KISS). Only the message changes, and the existing comment formatters
already embed `failure.message`, so the GitHub comment names the servers.

## ALGORITHM (`format_mcp_unavailable_message`)
```
servers = error.unavailable_servers or {}
named = ", ".join(f"{n} ({s})" for n, s in sorted(servers.items())) or "unknown"
return (f"MCP servers unavailable: {named}. The Claude session started without "
        f"its configured tools and was aborted; check the MCP server logs and .mcp.json.")
```

## DATA
- **Returns:** `str` — used as `WorkflowFailure.message`; flows verbatim into the
  existing `**Error:** {message}` line of each workflow's failure comment.

## TESTS (write first)
`tests/workflow_utils/test_failure_handling.py`:
- `format_mcp_unavailable_message(McpServersUnavailableError("x",
  {"mcp-tools-py": "failed", "mcp-workspace": "unknown"}))` → string contains
  both server names and their statuses, deterministically ordered.
- empty `unavailable_servers` → contains `"unknown"`, no crash.
- (regression) a raised `McpServersUnavailableError` propagating through
  `process_task_with_retry` is **not** swallowed into `"error"` — assert it
  re-raises (mock `prompt_llm` to raise the typed error).

## LLM PROMPT
> Implement Step 4 from `pr_info/steps/step_4.md` (context in
> `pr_info/steps/summary.md`). TDD first: add tests to
> `tests/workflow_utils/test_failure_handling.py` for
> `format_mcp_unavailable_message` (named servers + statuses; empty→"unknown")
> and a regression test that `process_task_with_retry` re-raises a
> `McpServersUnavailableError` instead of returning `(False, "error")`. Then add
> the formatter + typed-error import to `failure_handling.py`; add
> `except McpServersUnavailableError: raise` above the broad handler in
> `task_processing.py`; and route the implement/create_plan/create_pr failure
> boundaries through the formatter (reuse existing FailureCategory values — no
> new enum). Do NOT add any re-probing. Run pylint/pytest (`-n auto`,
> integration-excluded)/mypy, fix all, format, single commit.
