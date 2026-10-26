# Step 1 — Split `src/mcp_coder/cli/parsers.py` into three modules

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement **only** this step
> (`pr_info/steps/step_1.md`). It is a pure move: use `move_symbol` (dry run first),
> edit only import lines plus the docstring / `__future__` lines listed below, and don't
> touch any test file. Finish with every check under **Verification** green and
> exactly one commit.

## WHERE
- `src/mcp_coder/cli/parsers.py` (source, shrinks to ~386 lines)
- `src/mcp_coder/cli/workflow_parsers.py` (**new**)
- `src/mcp_coder/cli/interactive_parsers.py` (**new**)
- `src/mcp_coder/cli/main.py` (import block, lines 42–63, only)
- `src/mcp_coder/cli/command_catalog.py` (docstring lines 5–7)
- `.large-files-allowlist` (remove the line `src/mcp_coder/cli/parsers.py`)

## WHAT (symbols moved verbatim; all signatures `(subparsers: Any) -> None`)
- → `workflow_parsers.py`: `add_implement_parser`, `add_review_plan_parser`,
  `add_review_implementation_parser`, `add_create_plan_parser`, `add_rebase_parser`,
  `add_create_pr_parser`, `add_fix_conflict_parser`, `add_fix_ci_parser`,
  `add_coordinator_parsers`
- → `interactive_parsers.py`: `add_vscodeclaude_parsers`, `add_icoder_parser`
- These stay in `parsers.py`: `HelpHintArgumentParser`, `WideHelpFormatter`,
  `add_prompt_parser`, `add_commit_parsers`, `_validate_ci_timeout`,
  `_validate_pr_timeout`, `add_check_parsers`, `add_verify_parser`, `add_init_parser`,
  `add_install_parser`

## HOW (expected end state of imports)
`workflow_parsers.py` header:
```python
"""Argument parser definitions for background-development workflow CLI commands."""

from __future__ import annotations

import argparse
from typing import Any

from .command_catalog import COMMAND_DESCRIPTIONS
from .parsers import WideHelpFormatter
from .shared_args import (
    add_llm_method_arg,
    add_mcp_config_arg,
    add_project_dir_arg,
    add_settings_arg,
)
```
`interactive_parsers.py` header: same, but with the docstring
`"""Argument parser definitions for interactive-development CLI commands."""` and **no**
`import argparse`.

`parsers.py`: imports **unchanged** (`argparse`, `sys`, `Path`, `Any`, `NoReturn`,
`COMMAND_DESCRIPTIONS`, the four `shared_args` helpers).

`main.py`: replace the single `from .parsers import (...)` with:
```python
from .gh_parsers import add_gh_tool_parsers, add_git_tool_parsers
from .interactive_parsers import add_icoder_parser, add_vscodeclaude_parsers
from .parsers import (
    HelpHintArgumentParser,
    WideHelpFormatter,
    add_check_parsers,
    add_commit_parsers,
    add_init_parser,
    add_install_parser,
    add_prompt_parser,
    add_verify_parser,
)
from .workflow_parsers import (
    add_coordinator_parsers,
    add_create_plan_parser,
    add_create_pr_parser,
    add_fix_ci_parser,
    add_fix_conflict_parser,
    add_implement_parser,
    add_rebase_parser,
    add_review_implementation_parser,
    add_review_plan_parser,
)
```
The `create_parser` body is not touched. Don't change `gh_parsers.py` or any test file:
the symbols they import stay in `parsers.py`.

`command_catalog.py` docstring, lines 5–7. Before:
```text
(``cli/commands/help.py``) and the individual subparsers
(``cli/parsers.py`` / ``cli/gh_parsers.py``) read from these constants, so a
command's description cannot drift between the two.
```
After:
```text
(``cli/commands/help.py``) and the individual subparsers
(``cli/parsers.py`` / ``cli/workflow_parsers.py`` / ``cli/interactive_parsers.py`` /
``cli/gh_parsers.py``) read from these constants, so a
command's description cannot drift between the two.
```

## ALGORITHM
```
baseline = collect_only("tests/cli/")                       # record the number
move_symbol(parsers.py, [9 workflow fns], workflow_parsers.py, dry_run) -> check, then run
move_symbol(parsers.py, [2 interactive fns], interactive_parsers.py, dry_run) -> check, then run
make the move_symbol imports relative; add docstring + __future__; set the main.py imports
edit the command_catalog docstring; remove the allowlist line
format -> ruff fix F401 -> compare imports to HOW -> run checks -> collect_only == baseline
```

## DATA
No new data structures or return values. The module → symbol mapping above is the
whole change.

## Preconditions (if one fails: write one line to `pr_info/.blocked.txt` and stop)
- `list_symbols(src/mcp_coder/cli/parsers.py)` lists exactly the 21 symbols named above.
- Each dry run would modify only `parsers.py`, the destination module and `main.py`.

## Verification
- `run_format_code`; `run_ruff_fix(select=["F401"])`; then `run_ruff_check` (D100 on
  the new modules)
- `run_pylint_check`, `run_mypy_check`, `run_lint_imports_check`, `run_tach_check`,
  `run_vulture_check`
- `run_pytest_check` fast unit run (`-n auto` + marker exclusion from `CLAUDE.md`), plus
  `tests/cli/test_help_anti_drift.py` and `tests/install/test_install_env.py`
  explicitly. They walk the whole parser tree, which proves registration is unchanged.
- `--collect-only -q tests/cli/` equals the baseline.
- `check_file_size`: passes; `parsers.py` < 750 and no stale allowlist entry.
- `git diff` (compact): only import hunks, new-file headers, the 2 docstrings + 2
  `__future__` lines, the `command_catalog.py` lines, the allowlist removal, and
  moved-block previews.

## Commit
`refactor(cli): split parsers.py into workflow and interactive parser modules`
