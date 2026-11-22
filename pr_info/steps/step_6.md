# Step 6 — `llm_failure_reason` → `auth`; create-plan `.get`; review "Auth" category

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md` only. Steps 1–5
> are done. Write the tests first, then the code. Run pylint, pytest (`-n auto`, fast unit
> markers), mypy; run `run_format_code`; run `check_file_size`. Make one commit.

## WHERE

- `src/mcp_coder/workflow_utils/failure_handling.py`: `llm_failure_reason`, and the
  `run_guarded` docstring.
- `src/mcp_coder/workflows/create_plan/core.py`: `_prompt_failure`, and the comment above
  `FAILURE_LABELS`.
- `src/mcp_coder/workflows/review/handoff.py`: `_FAIL_REASONS`.
- Tests:
  - Create `tests/workflow_utils/test_failure_reason_auth.py`.
  - Create `tests/workflows/create_plan/test_prompt_failure_auth.py`.
  - Add one test to `tests/workflows/review/test_handoff_route.py`, reusing
    `_capture_fail_comment`. If that file would exceed 750 lines, create
    `tests/workflows/review/test_handoff_auth.py` and copy the small helper instead.

## WHAT

```python
# failure_handling.py
from mcp_coder.llm.interface import LLMAuthError, LLMTimeoutError

def llm_failure_reason(exc: BaseException) -> str | None:
    if isinstance(exc, LLMTimeoutError): return "timeout"
    if isinstance(exc, McpServersUnavailableError): return "mcp_unavailable"
    if isinstance(exc, LLMAuthError): return "auth"
    return None

# create_plan/core.py, _prompt_failure
category=FAILURE_LABELS.get(reason, FAILURE_LABELS["general"]),

# review/handoff.py, _FAIL_REASONS
"auth": ("Auth", "An LLM call failed to authenticate"),
```

- No new `FAILURE_LABELS` key in create-plan: auth uses the general `planning_failed` label
  through `.get`. Its message stays `str(exc)`, which already carries the hint and the CLI text.
- Docstrings and comments:
  - `llm_failure_reason` Returns: add `"auth"` for `LLMAuthError` (Claude login or
    langchain API key).
  - `run_guarded`: "precise `timeout`/`mcp_unavailable`/`auth` labels come only from the
    deliberate in-body paths". Phrase it so it doesn't need editing when reasons are added,
    e.g. "precise reasons (see `llm_failure_reason`)".
  - create-plan's `_prompt_failure` docstring and the `FAILURE_LABELS` comment: other reasons
    (e.g. `auth`) fall back to `planning_failed`.

## DATA

- `llm_failure_reason` returns `"timeout" | "mcp_unavailable" | "auth" | None`.

## Tests (first)

- `llm_failure_reason(LLMAuthError("x")) == "auth"`, for both the Claude-style import
  (`mcp_coder.llm.interface.LLMAuthError`) and the langchain-style one
  (`mcp_coder.llm.providers.langchain._exceptions.LLMAuthError`, raised via `raise_auth_error`).
- The hint survives `comment_safe`:
  - `comment_safe(exception_summary(LLMAuthError(AUTH_MESSAGE)))` starts with
    ``"LLMAuthError: Run `claude`, then `/login`."``
  - For #148's long text (hint + `API Error: 401 {...authentication_error...OAuth token has expired...} · Please run /login`)
    the result is ≤ 300 characters and still starts with the hint.
  - Import `AUTH_MESSAGE`/`AUTH_HINT` from `tests.logged_out_capture`.
- create-plan: `_prompt_failure(1, LLMAuthError(AUTH_MESSAGE))` → `category == "planning_failed"`,
  `stage == "Prompt 1 (auth)"`, and the message contains the hint; no `KeyError`.
- review: `_capture_fail_comment(..., "auth", exc=LLMAuthError(AUTH_MESSAGE))` → the body
  contains `**Category:** Auth`, and the `**Error:**` line contains the hint exactly once.
