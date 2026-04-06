The `ruff-docstrings` CI job failed due to a ruff DOC201 violation in `src/mcp_coder/utils/user_config.py` at line 548-549. The `_normalize_url` nested function (inside `find_repo_section_by_url`) has a docstring that says "Strip trailing .git and slash from URL." but the function returns a value (`str`). Ruff's DOC201 rule requires that any function with a `return` statement that yields a value must document that return value in a "Returns" section within its docstring.

The fix is localized to a single file: `src/mcp_coder/utils/user_config.py`. The `_normalize_url` inner function at line 548 needs its docstring expanded to include a "Returns" section describing the normalized URL string. For example, adding a "Returns:" block stating that the function returns the URL with trailing `.git` and `/` removed.

No other CI jobs failed, so this is the only change needed. The fix is purely a docstring documentation change with no impact on runtime behavior.
