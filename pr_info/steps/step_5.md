# Step 5 — E402: file-level suppression in `main.py`

See `pr_info/steps/summary.md` for the overall goal and rationale.

## Precondition check

Run `mcp__mcp-tools-py__run_ruff_check` with `select=["E402"]` and
`extra_args=["--preview"]`. Confirm it reports `E402` at exactly
`src/mcp_coder/cli/main.py`, lines 15–43 (24 occurrences), and nowhere else.
If the locations differ, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

`src/mcp_coder/cli/main.py`, the module docstring/header (lines 1–13):

```python
"""Main CLI entry point for MCP Coder.

isort:skip_file
"""

import argparse
import faulthandler
import logging
import sys

# Enable faulthandler early to capture tracebacks on crashes (e.g. segfaults)
# before heavy imports. Zero cost, writes to stderr.
faulthandler.enable(file=sys.stderr, all_threads=True)

from .. import __version__
...
```

## WHAT

No function signatures change. All 24 `E402` findings are the module-level
imports below `faulthandler.enable(...)`, which must run before those
imports are resolved — this ordering is deliberate, not an oversight.
Suppress the whole file with one `# ruff: noqa: E402` directive plus a
one-line comment explaining why, rather than 24 inline `# noqa: E402`
comments or disabling the rule project-wide.

## HOW

Add the directive as its own line, with the explanatory comment, placed
after the module docstring and before the first import (next to the
existing `isort:skip_file` marker, which exists for the same ordering
reason):

```python
"""Main CLI entry point for MCP Coder.

isort:skip_file
"""

# ruff: noqa: E402 — faulthandler.enable() must run before the heavy
# imports below it; see the comment at its call site.

import argparse
```

## ALGORITHM

N/A — config-comment addition, no logic change.

## DATA

No change to return values or data structures.

## Test-first note

This is a suppression-comment addition with no runtime effect. No new
tests; verification is the existing test suite passing unchanged and ruff
no longer flagging the file.

## Steps

1. Add the `# ruff: noqa: E402` line with its explanatory comment as shown
   above.
2. Run `mcp__mcp-tools-py__run_pytest_check` with
   `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`.
3. Run `mcp__mcp-tools-py__run_pylint_check` and `mcp__mcp-tools-py__run_mypy_check`.
4. Run `mcp__mcp-tools-py__run_ruff_check` with `select=["E402"]`,
   `extra_args=["--preview"]` — must report 0 findings.
5. Run `mcp__mcp-tools-py__run_format_code`.
6. Commit: `fix(lint): suppress E402 in main.py for faulthandler bootstrap`.

## LLM prompt for this step

> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_5.md`: add a single file-level `# ruff: noqa: E402`
> suppression with an explanatory comment to
> `src/mcp_coder/cli/main.py`, covering the 24 imports that intentionally
> sit after the `faulthandler.enable()` bootstrap call. Follow the
> precondition check first — if it fails, write one line to
> `pr_info/.blocked.txt` and stop. Otherwise make the edit, run the checks
> listed in the step, format the code, and produce exactly one commit with
> the given message.
