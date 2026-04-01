# Step 4: Decouple CI log parser test fixtures from real tool names

## References
- [Summary](summary.md)
- Issue #672

## WHERE
- `tests/checks/test_ci_log_parser.py`

## WHAT

Replace real tool command names in test fixture data with realistic-but-fictional names. This decouples test data from actual tool names so future tool renames don't require test updates.

### VULTURE_LOG fixture

Replace:
```python
"##[group]Run vulture --version && ./tools/vulture_check.sh\n"
"vulture --version && ./tools/vulture_check.sh\n"
```
With:
```python
"##[group]Run tool-alpha --version && ./tools/tool_alpha.sh\n"
"tool-alpha --version && ./tools/tool_alpha.sh\n"
```

Update tool output to match fictional name:
```python
"tool-alpha 2.15\n"           # was "vulture 2.15\n"
"Checking for dead code...\n"  # keep — describes behavior, not tool name
```

### Assertions in test methods

Update all string matches that reference the old command/tool names:

- `"Run vulture"` → `"Run tool-alpha"`
- `"vulture 2.15"` → `"tool-alpha 2.15"`
- `"Run vulture --version && ./tools/vulture_check.sh"` → `"Run tool-alpha --version && ./tools/tool_alpha.sh"`

### FILE_SIZE_LOG fixture

**No changes** — `mcp-coder check file-size` is not a replaced tool.

### test_branch_status.py

**No changes** — confirmed no references to the three scripts.

## HOW

Edit string literals in test file. Keep log structure (GitHub Actions `##[group]`/`##[endgroup]`/`##[error]` markers) identical.

## ALGORITHM

```
1. Replace tool name strings in VULTURE_LOG constant
2. Update version string to match fictional name
3. Update assertion strings in test_vulture_real_log_structure
4. Update assertion strings in test_captures_output_between_endgroup_and_error
5. Update assertion strings in test_error_fallback_with_outside_output
6. Run pytest to verify all tests still pass
```

## DATA

**Input**: Test fixture strings with real tool names
**Output**: Test fixture strings with fictional names, same log format

Fictional naming convention:
- CLI command: `tool-alpha` (hyphenated, like real CLI tools)
- Script: `./tools/tool_alpha.sh` (underscored, like real scripts)

## Verification

- All tests in `tests/checks/test_ci_log_parser.py` pass
- No references to `vulture_check.sh` or plain `vulture` remain in the file (except in test method names, which are kept unchanged)
- `FILE_SIZE_LOG` fixture is unchanged
- Log format markers (`##[group]`, `##[endgroup]`, `##[error]`) are preserved
- Test logic is identical — only string literals changed

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md for context.

Edit `tests/checks/test_ci_log_parser.py`:
1. Replace real tool names in VULTURE_LOG fixture with fictional "tool-alpha" / "tool_alpha.sh"
2. Update version string: "vulture 2.15" → "tool-alpha 2.15"
3. Update all assertion strings that match against the old names
4. Keep log format structure identical (##[group], ##[endgroup], ##[error] markers)
5. Do NOT modify FILE_SIZE_LOG or any other fixture

Do NOT rename test methods or functions — only change string literals in fixtures and assertions.

Run pytest to verify: mcp__tools-py__run_pytest_check with extra_args ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration and not textual_integration"]

Run all quality checks. Commit as: "test: decouple CI log parser fixtures from real tool names"
```
