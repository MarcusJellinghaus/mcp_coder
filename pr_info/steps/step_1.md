# Step 1 — Reorganize VSCodeClaude command tests (no production code change)

**Commit:** one commit — test relocation + all checks green.

Read [`summary.md`](./summary.md) first. This step moves the two VSCodeClaude
command-test classes into `test_vscodeclaude_cli.py` **before** any source moves,
so that Step 2's patch-string repointing becomes a clean whole-file blanket
replace. **No `src/` file is touched in this step.** Patch strings stay pointing at
`…coordinator.commands.<dep>` and remain valid because the source has not moved yet
— the suite stays green throughout.

## WHERE

- **From:** `tests/cli/commands/coordinator/test_commands.py`
- **To:** `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`

## WHAT — symbols to relocate (move verbatim, do not edit their bodies)

1. `class TestSkipGithubInstallWiring` (currently `test_commands.py:268`)
2. `class TestAtCapacityDiagnosticLog` (currently `test_commands.py:393`) — three
   methods, all move with the class: `test_at_capacity_log_includes_folder_basenames`,
   `test_below_capacity_message_unchanged`, and
   `test_process_eligible_issues_at_capacity_log_is_debug`. The third imports
   `process_eligible_issues` **directly from
   `mcp_coder.workflows.vscodeclaude.session_launch`** and patches **nothing** on
   `coordinator.commands`, so it relocates cleanly and needs **no** Step 2 repoint.
3. `def _assessment_stub(active: bool) -> SimpleNamespace` (currently
   `test_commands.py:27`) — module-level helper used **only** by
   `TestAtCapacityDiagnosticLog`; move it too (no duplication, nothing stale left).

Append all three to the end of `test_vscodeclaude_cli.py` (helper first, then the
two classes). Leave their `@patch("mcp_coder.cli.commands.coordinator.commands.…")`
strings and their in-function `from mcp_coder.cli.commands.coordinator.commands
import …` statements **exactly as-is** — they still resolve.

## HOW — import reconciliation

**`test_vscodeclaude_cli.py`** — current top imports are `argparse, json, logging,
Path, pytest`. Add what the moved code needs:

```python
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeConfig
```

**`test_commands.py`** — after removal, delete now-unused imports:

- `from types import SimpleNamespace` (only `_assessment_stub` used it)
- `from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeConfig` (only the
  moved intervention test used it)

Keep `MagicMock`, `patch`, `IssueData`, `JobStatus` — the remaining Jenkins tests
(`TestFormatJobOutput`, `TestExecuteCoordinatorTest`, `TestExecuteCoordinatorRun`)
still use them.

## ALGORITHM

```
1. cut _assessment_stub + the two classes from test_commands.py
2. paste them at the end of test_vscodeclaude_cli.py (helper before classes)
3. add the 3 import lines to test_vscodeclaude_cli.py
4. remove the 2 now-dead import lines from test_commands.py
5. run checks; both files import cleanly, patches still resolve (source unmoved)
```

## DATA / expected end state

- `test_commands.py` symbols: `TestFormatJobOutput`, `TestExecuteCoordinatorTest`,
  `TestExecuteCoordinatorRun` (Jenkins-only).
- `test_vscodeclaude_cli.py` symbols: `_assessment_stub`, `TestTemplates`,
  `TestCLI`, `TestCommandHandlers`, `TestSkipGithubInstallWiring`,
  `TestAtCapacityDiagnosticLog`.
- No `src/` changes. `git-tool compact-diff` shows only test files.

## Verify

Run: `run_format_code`, `run_pylint_check`, `run_pytest_check(extra_args=["-n",
"auto","-m","not git_integration and not claude_cli_integration and not
claude_api_integration and not formatter_integration and not github_integration and
not langchain_integration"])`, `run_mypy_check`, `run_vulture_check`. All green,
same test count as before (pure relocation).

## LLM prompt

> Implement Step 1 of `pr_info/steps/summary.md` (see `pr_info/steps/step_1.md`).
> This is a **test-only** reorganization — do **not** modify any file under `src/`.
> Using the MCP workspace file tools, move `_assessment_stub`,
> `TestSkipGithubInstallWiring`, and `TestAtCapacityDiagnosticLog` verbatim from
> `tests/cli/commands/coordinator/test_commands.py` to the end of
> `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`. Do **not** change any
> `@patch`/`from … import` string inside the moved code — they must stay pointing at
> `…coordinator.commands`. Add `from types import SimpleNamespace`, `from
> unittest.mock import MagicMock, patch`, and `from
> mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeConfig` to
> `test_vscodeclaude_cli.py`; remove the now-unused `SimpleNamespace` and
> `VSCodeClaudeConfig` imports from `test_commands.py`. Then run
> `run_format_code`, `run_pylint_check`, `run_pytest_check` (with the `-n auto`
> unit-test marker exclusions from the summary), `run_mypy_check`, and
> `run_vulture_check`; fix any issue until all are green. Commit as one commit.
