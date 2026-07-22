# Step 4 — Move CI check/fix into `workflow_steps` (loop-ready)

**Goal:** Relocate the CI monitor/analyse/fix step (the richest reused step) and its
tuning constants, and make its signature **re-enterable per review round** for #1072 —
while keeping `implement`'s behavior byte-identical. Must land **after** Step 2 (CI
imports `commit_changes` / `push_changes`).

## WHERE

Create:
- `src/mcp_coder/workflow_steps/ci.py`
- `tests/workflow_steps/test_ci.py`

Modify:
- `src/mcp_coder/workflow_steps/constants.py` (add the 7 CI/timeout constants)
- `src/mcp_coder/workflows/implement/constants.py` (remove those 7; re-export `LLM_INACTIVITY_TIMEOUT_SECONDS`)
- `src/mcp_coder/workflows/implement/core.py` (import `check_and_fix_ci` from `workflow_steps`)
- `src/mcp_coder/cli/commands/check_branch_status.py` (repoint its production import — see below)
- `src/mcp_coder/workflows/implement/ci_operations.py` → reactive re-export shim only (see below)
- `src/mcp_coder/workflows/implement/task_processing.py` (its `LLM_INACTIVITY_TIMEOUT_SECONDS` import still resolves via the re-export)

**Production consumers of `check_and_fix_ci` (both repointed here — this is a production
import migration, not a test-only courtesy):**
- `implement/core.py:383` — `from .ci_operations import check_and_fix_ci` → `from mcp_coder.workflow_steps.ci import check_and_fix_ci`.
- `cli/commands/check_branch_status.py:32` — `from ...workflows.implement.ci_operations import check_and_fix_ci` → `from mcp_coder.workflow_steps.ci import check_and_fix_ci`. This is the **only cross-package** production consumer; it is easy to miss because it lives in `cli`, not `implement`.

Because these two repoints remove the only production importers of `check_and_fix_ci`
from `implement/ci_operations.py`, that module needs **NO permanent production shim**.
Keep `implement/ci_operations.py` only as a **reactive** re-export shim if (and only if)
a red test reveals a broken `patch("…implement.ci_operations.check_and_fix_ci")` target
— consistent with the issue's reactive-shim decision. Otherwise it can be removed.

Move `tests/workflows/implement/test_ci_operations.py` + `test_ci_check.py` →
`tests/workflow_steps/test_ci.py`.

## WHAT (signatures)

In `workflow_steps/ci.py` — extend `CIFixConfig` and `check_and_fix_ci` with the
parameterized bits (defaults = implement's current literals):

```python
@dataclass
class CIFixConfig:
    project_dir: Path
    provider: str
    env_vars: dict[str, str]
    cwd: str
    mcp_config: Optional[str]
    settings_file: str | None = None
    analysis_prompt_header: str = "CI Failure Analysis Prompt"
    fix_prompt_header: str = "CI Fix Prompt"
    session_dir_name: str = "implement_sessions"

def check_and_fix_ci(
    project_dir: Path, branch: str, provider: str,
    mcp_config: Optional[str] = None, settings_file: str | None = None,
    execution_dir: Optional[Path] = None,
    *,
    analysis_prompt_header: str = "CI Failure Analysis Prompt",
    fix_prompt_header: str = "CI Fix Prompt",
    session_dir_name: str = "implement_sessions",
) -> bool
```

Private helpers move too: `_short_sha`, `_run_ci_analysis`, `_run_ci_fix`,
`_poll_for_ci_completion`, `_wait_for_new_ci_run`, `_run_ci_analysis_and_fix`,
`_read_problem_description`.

New constants in `workflow_steps/constants.py`:
`LLM_INACTIVITY_TIMEOUT_SECONDS`, `LLM_CI_ANALYSIS_TIMEOUT_SECONDS`,
`CI_POLL_INTERVAL_SECONDS`, `CI_MAX_POLL_ATTEMPTS`, `CI_MAX_FIX_ATTEMPTS`,
`CI_NEW_RUN_POLL_INTERVAL_SECONDS`, `CI_NEW_RUN_MAX_POLL_ATTEMPTS`.

Note: `PR_INFO_DIR` (used at `ci_operations.py:157` for the `.ci_problem_description.md`
temp file) is **intentionally absent** from this list — it was already relocated to
`workflow_steps/constants.py` in Step 2, so `ci.py` imports it from `.constants`. It is
not missing.

## HOW (integration points)

- `ci.py` imports `get_failed_jobs_summary` (checks.branch_status),
  `CIResultsManager` / `CIStatusData` (mcp_workspace_github),
  `get_latest_commit_sha` (mcp_workspace_git),
  `prompt_llm` / `LLMTimeoutError` (llm.interface),
  `McpServersUnavailableError` (llm.providers.claude.claude_code_cli),
  `store_session` (llm.storage.session_storage),
  `get_prompt_with_substitutions` (prompt_manager),
  `commit_changes` / `push_changes` / `run_formatters` (workflow_steps.commit),
  and the CI constants from `.constants`.
- Thread the three parameters through: `check_and_fix_ci` copies them into
  `CIFixConfig`; `_run_ci_analysis` uses `config.analysis_prompt_header` +
  `config.session_dir_name`; `_run_ci_fix` uses `config.fix_prompt_header` +
  `config.session_dir_name`. Replace the hardcoded `"CI Failure Analysis Prompt"` /
  `"CI Fix Prompt"` and every `.mcp-coder / "implement_sessions"` literal with the
  config fields.
- `implement/core.py` calls `check_and_fix_ci(...)` **without** the new kwargs → byte-identical.
- `implement/constants.py` adds
  `from mcp_coder.workflow_steps.constants import LLM_INACTIVITY_TIMEOUT_SECONDS`
  (still imported by `task_processing.check_and_fix_mypy` / `process_single_task`).

## ALGORITHM

Verbatim move; the only edits are (1) replace 2 hardcoded prompt-header strings and
the `"implement_sessions"` dir literal with `config.*` fields, (2) repoint imports.
Control flow (poll → analyse → fix → wait-for-new-run loop, Decision-9 propagate /
Decision-10 absorb error handling) unchanged.

## DATA

`check_and_fix_ci` → `bool` (True = CI passed / graceful exit; False = fix attempts
exhausted). `CIFixConfig` gains 3 `str` fields.

## TDD

Move the CI tests into `tests/workflow_steps/test_ci.py`, updating patch targets to
`mcp_coder.workflow_steps.ci.*`. Add two small characterization tests before the move:
(1) default headers reach `get_prompt_with_substitutions` as
`"CI Failure Analysis Prompt"` / `"CI Fix Prompt"`; (2) sessions are stored under
`.mcp-coder/implement_sessions`. Then perform the move and make green.

## Checks / commit

All enforcers + pylint / pytest / mypy green. One commit:
`refactor(workflow_steps): move CI step with loop-ready params + CI constants`.

## LLM prompt

> Read `pr_info/steps/summary.md` (sections "What moves", "Loop-ready CI signature",
> "Constants relocated by re-export") and `pr_info/steps/step_4.md`. Move
> `check_and_fix_ci`, its private helpers, and `CIFixConfig` verbatim from
> `implement/ci_operations.py` into `workflow_steps/ci.py`, importing commit/push/format
> from `mcp_coder.workflow_steps.commit`. Add the three keyword parameters
> (`analysis_prompt_header`, `fix_prompt_header`, `session_dir_name`) with defaults equal
> to implement's current literals, thread them through `CIFixConfig`, and replace the
> hardcoded prompt headers and `implement_sessions` dir with the config fields. Move the
> 7 CI/timeout constants into `workflow_steps/constants.py` and re-export
> `LLM_INACTIVITY_TIMEOUT_SECONDS` from `implement/constants.py`. Repoint
> `implement/core.py` (calling `check_and_fix_ci` with no new kwargs). Move the CI tests
> into `tests/workflow_steps/test_ci.py` with updated patch targets plus the two
> characterization tests. Keep `implement/ci_operations.py` as a shim only if a test
> requires it. Verify all enforcers and the pylint/pytest/mypy trio are green, then
> produce one commit.
