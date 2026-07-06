# Step 2 — Move the VSCodeClaude source family + repoint patch strings

**Commit:** one commit — source move + wiring + patch repointing + all checks green.

Read [`summary.md`](./summary.md) first and complete Step 1 first (all VSCodeClaude
command tests now live in `test_vscodeclaude_cli.py`). This step performs the actual
`move_symbol` and finishes wiring. After Step 1, every `…coordinator.commands.<dep>`
string literal that must move lives in one of **three VSCodeClaude-only test files**,
so repointing is a whole-file blanket replace with no per-`@patch` judgement.

## WHERE

- **New:** `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py`
- **Modified:** `src/mcp_coder/cli/commands/coordinator/commands.py`,
  `…/coordinator/__init__.py`, `.large-files-allowlist`,
  `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`,
  `tests/workflows/vscodeclaude/test_active_set_invariant.py`,
  `tests/workflows/vscodeclaude/test_explain.py`

## WHAT — symbols to move (verbatim; `move_symbol` carries imports and rewrites
`from … import …` project-wide)

| Symbol | Signature |
|---|---|
| `_get_repo_full_name_from_url` | `(repo_url: str) -> str` |
| `_build_cached_issues_by_repo` | `(repo_names: list[str], sessions: list[VSCodeClaudeSession] \| None = None) -> tuple[dict[str, dict[int, IssueData]], set[str]]` |
| `execute_coordinator_vscodeclaude` | `(args: argparse.Namespace) -> int` |
| `execute_coordinator_vscodeclaude_status` | `(args: argparse.Namespace) -> int` |
| `_handle_intervention_mode` | `(args: argparse.Namespace, vscodeclaude_config: VSCodeClaudeConfig) -> int` |

## HOW — integration points (manual; `move_symbol` does NOT touch these)

1. **`__all__` in both modules** (move_symbol ignores `__all__`):
   - `commands.py`: `__all__ = ["execute_coordinator_test",
     "execute_coordinator_run", "format_job_output"]`
   - `commands_vscodeclaude.py`: add `__all__ = ["execute_coordinator_vscodeclaude",
     "execute_coordinator_vscodeclaude_status"]` (the 3 `_`-prefixed helpers are
     private, not exported).
2. **`__init__.py`** — split the single `from .commands import (…)` into two blocks;
   leave the package `__all__` list unchanged (still exports all 5 names):
   ```python
   from .commands import (
       execute_coordinator_run,
       execute_coordinator_test,
       format_job_output,
   )
   from .commands_vscodeclaude import (
       execute_coordinator_vscodeclaude,
       execute_coordinator_vscodeclaude_status,
   )
   ```
   (`move_symbol` may do part of this automatically — verify and finish by hand.)
3. **`.large-files-allowlist`** — delete the line
   `src/mcp_coder/cli/commands/coordinator/commands.py`.
4. **Blanket patch-string repoint** — in **exactly these three files**, replace all
   occurrences of `mcp_coder.cli.commands.coordinator.commands.` with
   `mcp_coder.cli.commands.coordinator.commands_vscodeclaude.` (`replace_all`):
   - `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`
   - `tests/workflows/vscodeclaude/test_active_set_invariant.py`
   - `tests/workflows/vscodeclaude/test_explain.py`

   The trailing `.` matches only string-literal patch targets; `from …commands
   import (` lines (space after `commands`) are untouched — `move_symbol` already
   rewrote those. **`test_commands.py` and `test_integration.py` get no repoint**
   (they patch Jenkins deps that stay in `commands.py`).

## ALGORITHM

```
1. move_symbol(dry_run=True) for the 5 symbols -> preview
2. move_symbol(...) execute       # creates commands_vscodeclaude.py, rewrites imports
3. set __all__ in commands.py (3 Jenkins) and commands_vscodeclaude.py (2 public)
4. split __init__.py into two import blocks; keep package __all__ unchanged
5. remove commands.py line from .large-files-allowlist
6. replace_all the patch-string prefix in the 3 vscodeclaude-only test files
7. run full check + verification suite
```

## DATA / expected end state

- `commands.py` ≈ 370 lines (Jenkins only); `commands_vscodeclaude.py` ≈ 460 lines —
  both < 600.
- `commands.py` imports pruned by `move_symbol`: `IssueData`,
  `get_all_cached_issues`, and every `workflows.vscodeclaude` symbol (all
  VSCodeClaude-only) no longer imported there.
- Package facade unchanged from a caller's view (`cli/main.py` untouched, still
  green).
- `git-tool compact-diff` shows **only** import changes + the new/deleted file
  headers — no logic diff.

## Verify (full suite)

`run_format_code`, `run_pylint_check`, `run_pytest_check(extra_args=["-n","auto",
"-m","not git_integration and not claude_cli_integration and not
claude_api_integration and not formatter_integration and not github_integration and
not langchain_integration"])`, `run_mypy_check`, `run_lint_imports_check`,
`run_vulture_check`, `check_file_size(max_lines=750)` (no stale allowlist entry),
`tach check` (Bash), `git-tool compact-diff` (Bash — imports + headers only).

## LLM prompt

> Implement Step 2 of `pr_info/steps/summary.md` (see `pr_info/steps/step_2.md`).
> Step 1 must already be committed. Using the MCP refactoring tools, first run
> `move_symbol(dry_run=True)` then execute it to move `_get_repo_full_name_from_url`,
> `_build_cached_issues_by_repo`, `execute_coordinator_vscodeclaude`,
> `execute_coordinator_vscodeclaude_status`, and `_handle_intervention_mode` from
> `src/mcp_coder/cli/commands/coordinator/commands.py` to a new
> `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py`. Do not edit any
> moved function body. Then, manually: set `__all__` in `commands.py` to the 3
> Jenkins names and add `__all__` with the 2 public VSCodeClaude names to the new
> module; split `coordinator/__init__.py` into two import blocks (keep its `__all__`
> unchanged); remove the `commands.py` line from `.large-files-allowlist`; and in
> the three files `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`,
> `tests/workflows/vscodeclaude/test_active_set_invariant.py`, and
> `tests/workflows/vscodeclaude/test_explain.py` do a `replace_all` of
> `mcp_coder.cli.commands.coordinator.commands.` →
> `mcp_coder.cli.commands.coordinator.commands_vscodeclaude.`. Do **not** repoint
> `test_commands.py` or `test_integration.py`. Then run `run_format_code`,
> `run_pylint_check`, `run_pytest_check` (with the `-n auto` unit-test marker
> exclusions from the summary), `run_mypy_check`, `run_lint_imports_check`,
> `run_vulture_check`, `check_file_size(max_lines=750)`, and (via Bash) `tach check`
> and `mcp-coder git-tool compact-diff`. The compact diff must show only import
> changes and new/deleted file headers. Fix any failure until all are green, then
> commit as one commit.
