# Step 9 — Shared CI step re-raises auth; fix-ci catches it; review CI gate

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_9.md` only. Steps 1–8
> are done. Write the tests first, then the code. Run pylint, pytest (`-n auto`, fast unit
> markers), mypy; run `run_format_code`; run `check_file_size` — mandatory here because
> `workflow_steps/ci.py` is at 745/750 lines. Make one commit.

## WHERE

- `src/mcp_coder/workflow_steps/ci.py`: `_run_ci_analysis`, `_run_ci_fix`, and the
  `check_and_fix_ci` docstring.
- `src/mcp_coder/workflows/fix_ci/core.py`: `_LLM_FAILURE_CATEGORY_DISPLAY`, and the
  `except` around `check_and_fix_ci`.
- `src/mcp_coder/workflows/review/steps.py`: the `_after_steps` docstring only. Its broad
  `except` already maps through `llm_failure_reason`.
- `src/mcp_coder/workflows/review/core.py`: the reason comment near "Terminal after-steps
  failure", and the Returns docstring of the review workflow (add auth to "timeout, MCP down").
- Tests:
  - Create `tests/workflow_steps/test_ci_auth.py`. `tests/workflow_steps/test_ci.py` is at
    the size gate, so do not add to it. Copy its small `_make_config()` pattern and patch
    `mcp_coder.workflow_steps.ci.prompt_llm`.
  - fix-ci: add to `tests/workflows/fix_ci/test_core.py` if it stays ≤ 750 lines, else create
    `tests/workflows/fix_ci/test_core_auth.py`.
  - review CI gate: add a test next to the existing `_after_steps` CI-gate tests
    (`tests/workflows/review/test_steps.py`, using the shared `env` fixture in
    `tests/workflows/review/conftest.py`). If that exceeds 750 lines, create
    `tests/workflows/review/test_steps_ci_auth.py`.

## WHAT / ALGORITHM

```
# ci.py — import
from mcp_coder.llm.interface import LLMAuthError, LLMTimeoutError, prompt_llm

# _run_ci_analysis — extend the tuple; shorten the 4-line comment to 1–2 lines
except (LLMAuthError, LLMTimeoutError, McpServersUnavailableError):
    # Typed LLM failures propagate for the caller to categorize (Decision 9).
    raise

# _run_ci_fix — new narrow re-raise BEFORE the catch-all; shorten the 6-line Decision 10 comment
except LLMAuthError:
    raise  # Auth is never transient: the one exception to Decision 10
except Exception as e:
    # Decision 10: absorb every other failure (timeout/MCP included) into one
    # failed attempt; exhaustion becomes ci_fix_needed.
    logger.warning(f"LLM fix failed: {e}")
    return False

# fix_ci/core.py
_LLM_FAILURE_CATEGORY_DISPLAY = {"timeout": "Llm Timeout", "mcp_unavailable": "Mcp Unavailable", "auth": "Auth"}
except (LLMAuthError, LLMTimeoutError, McpServersUnavailableError) as exc:
    _refresh_if_pushed()
    reason = llm_failure_reason(exc) or "general"
    category = _LLM_FAILURE_CATEGORY_DISPLAY.get(reason, "General")
    message = exception_summary(exc) if reason == "auth" else str(exc)
    return _fail(project_dir, category, "CI pipeline analysis", message, ...)
```

## HOW

- Docstrings:
  - `_run_ci_analysis` Raises: add `LLMAuthError`.
  - `_run_ci_fix`: add a Raises section with `LLMAuthError` (fix phase).
  - `check_and_fix_ci` Raises: `LLMAuthError` from the analysis **or** fix phase.

  Keep the wording terse.
- Update the comment "two typed LLM failures" in `ci.py`, if present, to "the typed LLM failures".
- **File-size gate:** `ci.py` must stay ≤ 750 lines. Trim existing comments and docstrings to
  make room; the two comments above are the main candidates. Do **not** move helpers to a
  sibling module (tests patch `ci.time`, `ci.prompt_llm`, `ci.store_session`,
  `ci.commit_changes`), and do **not** add `ci.py` to `.large-files-allowlist`. If it still
  exceeds 750 lines after trimming, write one line to `pr_info/.blocked.txt` and stop.
- fix-ci applies `pr_ci_failed` through its existing `_fail`, not the crash-watchdog label.
  `refresh_pr_description` stays best-effort.
- The review CI gate now returns `"auth"` instead of a `"ci"` finding. This is intended;
  `_FAIL_REASONS["auth"]` exists since step 6.

## DATA

- `_run_ci_analysis` / `_run_ci_fix` raise `LLMAuthError` unchanged (same object).
- fix-ci comment: `Category: Auth`, `Stage: CI pipeline analysis`,
  ``Error: LLMAuthError: Run `claude`, then `/login`. …``; label `pr_ci_failed`; return 1.
- `_after_steps` → `("auth", outcome, comment_safe(exception_summary(exc)))`.

## Tests (first)

- `test_ci_auth.py`:
  - `_run_ci_analysis` with `prompt_llm` raising `LLMAuthError` → re-raised.
  - `_run_ci_fix` with `prompt_llm` raising `LLMAuthError` → re-raised (not `False`).
  - `_run_ci_fix` with `prompt_llm` raising `LLMTimeoutError` → still returns `False`
    (Decision 10 regression guard).
- fix-ci: `check_and_fix_ci` raising `LLMAuthError(AUTH_MESSAGE)` → returns 1;
  `handle_workflow_failure` gets `WorkflowFailure(category="pr_ci_failed", ...)`; the comment
  has `Category:** Auth` and the hint once. `run_guarded`'s crash path is not taken.
- fix-ci timeout regression: the error text is still `str(exc)` (existing tests stay green).
- review: `check_and_fix_ci` raising `LLMAuthError(AUTH_MESSAGE)` in `_after_steps` → reason
  `"auth"`, and the detail starts with ``"LLMAuthError: Run `claude`, then `/login`."``
- `check_file_size` passes for `ci.py` and every touched test file.
