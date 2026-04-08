The CI pipeline failed on the `ruff-docstrings` job due to two ruff docstring convention violations (rules DOC201 and DOC502) in `src/mcp_coder/cli/commands/init.py`.

The first error (DOC201) is on `_has_all_subdirs` at line 19. The function has a one-line docstring but returns a `bool` value without documenting it. Ruff requires a "Returns" section in the docstring for any function that has a `return` statement with a value. The fix is to add a `Returns:` section to the docstring describing the boolean return value.

The second error (DOC502) is on `_find_claude_source_dir` at line 24. The docstring declares `Raises: SystemExit` but the function body calls `sys.exit(1)` rather than explicitly raising `SystemExit`. Ruff's DOC502 rule flags documented exceptions that are not raised with an explicit `raise` statement. The fix is either to remove the `Raises: SystemExit` section from the docstring (since `sys.exit` is used instead of `raise SystemExit`), or to change `sys.exit(1)` to `raise SystemExit(1)` so the docstring matches the code.

Both fixes are localized to `src/mcp_coder/cli/commands/init.py`. No other files or jobs were affected.
