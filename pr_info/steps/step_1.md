# Step 1 — Move `TestCommandTemplates` → `test_command_templates.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then do `pr_info/steps/step_1.md`. This is a pure refactor:
> move the class with `mcp__mcp-tools-py__move_symbol` (dry run first). Edit only imports.
> Run every check listed. The step ends in exactly one commit.

## WHERE

- Source: `tests/cli/commands/coordinator/test_core.py`
- Destination (existing): `tests/cli/commands/coordinator/test_command_templates.py`

## WHAT

- Move the class `TestCommandTemplates` (1 test). No functions or signatures change.

## HOW

1. **Precondition:**
   - Run `list_symbols("tests/cli/commands/coordinator/test_core.py")`.
   - It must list exactly these 12 classes: `TestLoadRepoConfig`, `TestValidateRepoConfig`,
     `TestGetJenkinsCredentials`, `TestGetCacheRefreshMinutes`, `TestGetEligibleIssues`,
     `TestDispatchWorkflow`, `TestDispatchWorkflowSilentFallthroughGuard`, `TestCacheFilePath`,
     `TestCacheFileOperations`, `TestStalenessLogging`, `TestGetCachedEligibleIssues`,
     `TestCommandTemplates`.
   - If `TestBuildEligibleIssuesPrefetched` is listed, or the list differs: write one line to
     `pr_info/.blocked.txt` and stop.
2. **Baseline:** run `run_pytest_check(extra_args=["--collect-only", "-q", <path>])` for each
   path below and note the numbers:

   | Path | Expected |
   |---|---:|
   | `tests/cli/commands/coordinator/test_core.py` | 50 |
   | `tests/cli/commands/coordinator/test_command_templates.py` | 31 |
   | `tests/cli/commands/coordinator/` | 156 |
   | `tests/utils/` | 441 |
   | whole suite (no path) | 6587 |

   The directory and suite totals may have drifted; only the deltas must hold.
   Also run `-q tests/cli/commands/coordinator/test_core.py::TestCommandTemplates` and
   confirm it passes.
3. **Dry run:**
   - Call `move_symbol(source_file=test_core.py, symbol_names=["TestCommandTemplates"],
     dest_file=test_command_templates.py, dry_run=True)`.
   - If it lists files other than these two: write one line to `pr_info/.blocked.txt` and stop.
4. **Move:** run the same call without `dry_run`.
5. **Imports:**
   - `test_command_templates.py`: its import block must end up **unchanged**. It already
     imports all six constants from the package `mcp_coder.cli.commands.coordinator`. Delete
     any import the tool added, for example from `...coordinator.command_templates`.
     Never switch the existing import to the submodule path.
   - `test_core.py`: delete the whole `from mcp_coder.cli.commands.coordinator.command_templates
     import (...)` block, which is now unused.

## ALGORITHM

```
check symbols -> record counts
dry-run move -> only 2 files touched?
move -> drop tool-added duplicate imports in destination
drop now-unused template import block in test_core.py
format, ruff, pylint, mypy, pytest, collect counts
```

## DATA — expected collect counts after the step

| Path | Expected |
|---|---:|
| `test_core.py` | 49 |
| `test_command_templates.py` | 32 |
| `tests/cli/commands/coordinator/` | baseline (unchanged) |
| whole suite | baseline |

Also rerun `test_command_templates.py::TestCommandTemplates` → 1 passed.

## Checks

- `run_format_code`
- `run_ruff_check`: no `F401` / `F811`. An `F811` means a duplicate import: write one line
  to `pr_info/.blocked.txt` and stop.
- `run_pylint_check`
- `run_mypy_check`
- fast unit `run_pytest_check` with `-n auto`
- `check_file_size`

## Commit

`test(coordinator): move TestCommandTemplates to test_command_templates.py`
