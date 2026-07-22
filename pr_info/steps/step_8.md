# Step 8 — After-steps: base-branch injection + rebase + CI-as-finding (`review-implementation`)

> References `pr_info/steps/summary.md` §4, §6. Fills the `_after_steps` hook and the
> base-branch injection, realizing **`review-implementation`** (`run_after_steps=True`). Reuses
> `implement`'s CI headers (overrides only `session_dir_name`). Tests mock the CI/rebase steps.

## WHERE
- `src/mcp_coder/workflows/review/core.py` (modify — implement `_after_steps`, `_resolve_context`)
- `tests/workflows/review/test_core_after_steps.py` (new)

## WHAT
```python
def _resolve_context(config, project_dir) -> tuple[int | None, str | None]:
    # issue_no from branch; base_branch = detect_base_branch(...) only if config.inject_base_branch

def _after_steps(config, project_dir, provider, mcp_config, settings_file,
                 execution_dir, is_dismiss: bool) -> str | None:
    # run_after_steps=False -> return None
    # else: rebase; then check_and_fix_ci(session_dir_name=config.session_dir_name)
    # returns a failure reason ("ci") or None; sets self.pending_ci_note when red mid-loop
```

## HOW
- **Base branch:** `_resolve_context` calls
  `mcp_coder.workflow_utils.base_branch.detect_base_branch(project_dir)` **only** when
  `config.inject_base_branch` (impl); plan passes `None`. Injected into the reviewer prompt's
  `{base_branch}` slot.
- **Rebase gate (mandated — never success on unresolved rebase):**
  `mcp_coder.workflow_steps.rebase._attempt_rebase_and_push(project_dir)`. If the branch needs
  a rebase and `_attempt_rebase_and_push` cannot complete cleanly (e.g. a merge conflict),
  route to **needs-human `07:code-review`** — **never success**. The issue mandates this gate
  ("rebase-needed … never success").
  - **`#1066` integration slot (do NOT implement here):** a *conflict-resolving automatic*
    rebase is the deliverable of a **separate issue #1066** (`mcp-coder git-tool rebase`, not
    yet implemented). Add an explicit **rebase-status check** followed by a
    `NotYetImplemented`-style marker/comment referencing **#1066** at the point where an
    automatic rebase attempt will later slot in. Until #1066 lands, a "needs rebase /
    unresolvable conflict" outcome simply routes to needs-human (`07:code-review`). This step
    only specifies the check + the needs-human fallback + the #1066 reference — it does **not**
    implement any automatic conflict-resolving rebase.
- **CI:** `mcp_coder.workflow_steps.ci.check_and_fix_ci(..., session_dir_name=
  config.session_dir_name)` — reuses the default `"CI Failure Analysis Prompt"` /
  `"CI Fix Prompt"` headers. Wrap its `LLMTimeoutError`/`McpServersUnavailableError` →
  `timeout`/`mcp` reasons (mirrors `implement/core.py`).
- **CI as a supervisor finding (mid-loop):** when a `tasks`-round CI check returns red, do
  **not** fail immediately — carry a `pending_ci_note` string into the **next** reviewer
  prompt (appended to its input) so the reviewer surfaces it and the supervisor triages within
  the rounds cap.
- **Terminal CI:** on the **dismiss final gate** (`is_dismiss=True`) a red CI returns reason
  `"ci"` → `_fail(config, "ci", ...)` → `17f-ci` (cause wins over `17f-rounds`). If the rounds
  cap is hit while `pending_ci_note` is set, `run_review_workflow` uses reason `"ci"` instead
  of `"rounds"`.

## ALGORITHM (`_after_steps`)
```
if not config.run_after_steps: return None
# --- rebase gate (mandated: never success on unresolved rebase) ---
rebase_ok = _attempt_rebase_and_push(project_dir)
if not rebase_ok:
    # NotYetImplemented(#1066): a conflict-resolving automatic `mcp-coder git-tool rebase`
    # attempt slots in HERE once #1066 ships (before the needs-human fallback). Until then:
    return "rebase"          # -> needs-human 07:code-review, never success
# --- CI ---
try: ci_ok = check_and_fix_ci(project_dir, branch, provider, ..., session_dir_name=config.session_dir_name)
except LLMTimeoutError: return "timeout"
except McpServersUnavailableError: return "mcp"
if ci_ok: return None
return "ci" if is_dismiss else None    # mid-loop: set pending_ci_note, keep looping
```

## HOW — integrate into Step 7 loop (minimal edits)
- Pass `is_dismiss=True` on the dismiss branch, `False` on the tasks branch.
- Track `pending_ci_note`; append to the next `_run_reviewer` input; at cap choose reason
  `"ci"` if set else `"rounds"`.
- **Rebase reason routes to needs-human, not error:** a `"rebase"` reason from `_after_steps`
  is a **needs-human handoff** (escalate lane) → `update_workflow_label(from=busy,
  to=escalate)` = `07:code-review`, exit `0` — it is **not** an `handle_workflow_failure`
  error/`_fail`. (Contrast `"ci"`, which is a `17f-ci` failure.) Handle it like the `escalate`
  verdict: log the reason, set the escalate label, return `0` — never success.

## DATA
- `_after_steps` returns `str | None` (failure reason). `pending_ci_note: str | None` local.

## TDD / checks (mock `check_and_fix_ci`, `_attempt_rebase_and_push`, `detect_base_branch`, `prompt_llm`)
- `REVIEW_IMPLEMENTATION`: `_resolve_context` injects a base branch into the reviewer prompt;
  `REVIEW_PLAN`: base is `None`, `detect_base_branch` not called.
- dismiss + rebase clean + CI green → success (`ready_pr`).
- dismiss + rebase fails (conflict) → routes to needs-human `07:code-review`, exit `0`,
  **never success** (no `17f-*` failure); `NotYetImplemented`/#1066 marker present at the slot.
- dismiss + CI red → returns 1 with `code_review_ci` (`17f-ci`).
- tasks round CI red → loop continues, note reaches next reviewer prompt; cap → `17f-ci`.
- tasks round CI green → normal loop.
- Run: `run_pytest_check(extra_args=["-n","auto","-k","review and after_steps"])`, pylint, mypy.

## LLM prompt for this step
> Implement Step 8 of `pr_info/steps/summary.md`: in
> `src/mcp_coder/workflows/review/core.py`, implement `_resolve_context` to inject
> `detect_base_branch(...)` only when `config.inject_base_branch`, and fill `_after_steps` to run
> `_attempt_rebase_and_push` then `check_and_fix_ci(session_dir_name=config.session_dir_name)`
> (reusing implement's CI headers). **Rebase gate:** if `_attempt_rebase_and_push` cannot complete
> cleanly (conflict), route to needs-human `07:code-review` (escalate lane, exit 0) — never
> success and never a failure label; add a `NotYetImplemented`-style marker/comment referencing
> **#1066** at the slot where a future conflict-resolving `mcp-coder git-tool rebase` attempt will
> go (do NOT implement automatic rebase here). Wire CI-as-finding: a mid-loop red CI carries a
> `pending_ci_note` into the next reviewer prompt and does not fail; a red CI on the dismiss
> final gate returns reason `"ci"` (→ `17f-ci`); at the rounds cap prefer reason `"ci"` when the
> note is set. Map CI-phase `LLMTimeoutError`/`McpServersUnavailableError` to `timeout`/`mcp`.
> Write `tests/workflows/review/test_core_after_steps.py` first (mock CI/rebase/detect_base_branch/
> prompt_llm) covering the Step 8 cases for both configs. Run the tests, pylint, mypy.
