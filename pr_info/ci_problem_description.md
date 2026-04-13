The CI `ruff-docstrings` job failed with a DOC501 violation in `src/mcp_coder/utils/tui_preparation.py` at line 65. The `_present_prompt` method raises `TuiPreflightAbort` in three code paths (lines 70, 77, and 78), but the docstring does not document the raised exception. Ruff's DOC501 rule enforces that all exceptions explicitly raised in a function body must appear in the docstring's `Raises:` section.

The fix requires updating the docstring for `_present_prompt` on line 65 of `src/mcp_coder/utils/tui_preparation.py`. The current single-line docstring `"""Present a prompt to the user. Both choices result in abort."""` needs a `Raises:` section listing `TuiPreflightAbort` with a description of when it is raised. This is a documentation-only change — no logic or behavior modifications are needed.

The mypy failure is a separate issue and should be investigated independently from this docstring fix.
