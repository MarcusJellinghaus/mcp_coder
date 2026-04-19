# Step 5: Add `[tool.mcp-coder.implement]` to this repo's pyproject.toml

## Context
See `pr_info/steps/summary.md` for full design. This step enables the new config for this repository itself.

## WHERE
- `pyproject.toml` — add new section
- `tests/test_pyproject_config.py` — add verification test

## WHAT

### New TOML section
Add after the existing `[tool.mcp-coder.install-from-github]` section (around line 339):

```toml
[tool.mcp-coder.implement]
format_code = true
check_type_hints = true
```

## HOW
Append the section to `pyproject.toml` right after the `[tool.mcp-coder.install-from-github]` block.

## TESTS (write first)
Add to `tests/test_pyproject_config.py`:
1. `test_pyproject_implement_config_exists` — verify `[tool.mcp-coder.implement]` section exists with both keys set to `true`

This follows the pattern of the existing `test_pyproject_install_from_github_config_exists` test in the same file.

## LLM PROMPT
```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_5.md.

Add [tool.mcp-coder.implement] section with format_code = true and
check_type_hints = true to pyproject.toml. Add a test in
tests/test_pyproject_config.py verifying the section exists, following the
pattern of test_pyproject_install_from_github_config_exists.
```
