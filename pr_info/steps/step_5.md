# Step 5: Print Migration — Core CLI Commands

## LLM Prompt
> Read `pr_info/steps/summary.md` for full context. Implement Step 5: Migrate status/error print() calls to logging in core CLI command files. Keep data-producing prints as-is. Run all three code quality checks after changes.

## WHERE
Files to modify (migrate prints):
- `src/mcp_coder/cli/main.py`
- `src/mcp_coder/cli/commands/commit.py`
- `src/mcp_coder/cli/commands/create_pr.py`
- `src/mcp_coder/cli/commands/create_plan.py`
- `src/mcp_coder/cli/commands/implement.py`
- `src/mcp_coder/cli/commands/init.py`
- `src/mcp_coder/cli/commands/prompt.py`
- `src/mcp_coder/cli/commands/set_status.py`
- `src/mcp_coder/cli/commands/gh_tool.py`
- `src/mcp_coder/cli/commands/git_tool.py`

Files NOT modified (data output):
- `src/mcp_coder/cli/commands/help.py` — `print(help_text)` is pipeable data
- `src/mcp_coder/cli/commands/verify.py` — formatted verification report is data

## WHAT

### Migration Rules

Each file needs `from ...utils.log_utils import OUTPUT` (or appropriate relative import depth).

**Rule 1: Error prints → `logger.error()`**
```python
# BEFORE
print(f"Error: {e}", file=sys.stderr)
print("Error: --dry-run requires --repo NAME", file=sys.stderr)

# AFTER
logger.error("%s", e)
logger.error("--dry-run requires --repo NAME")
```

**Rule 2: Status/progress prints → `logger.log(OUTPUT, ...)`**
```python
# BEFORE
print(f"SUCCESS: Commit created: {commit_result['commit_hash']}")
print(f"Created default config at: {path}")
print("Operation cancelled by user.")

# AFTER
logger.log(OUTPUT, "SUCCESS: Commit created: %s", commit_result['commit_hash'])
logger.log(OUTPUT, "Created default config at: %s", path)
logger.log(OUTPUT, "Operation cancelled by user.")
```

**Rule 3: Keep data-producing prints**
```python
# KEEP AS-IS (data output to stdout for piping/parsing):
print(help_text)          # help.py
print(result)             # git_tool.py compact-diff
print(output)             # check_branch_status.py report
print(base_branch)        # gh_tool.py get-base-branch
print(branch_name)        # gh_tool.py checkout-issue-branch
print(json.dumps(...))    # prompt.py JSON output
print(session_id)         # prompt.py session-id mode
```

**Rule 4: Hint/instruction prints → `logger.log(OUTPUT, ...)`**
```python
# BEFORE
print("Try 'mcp-coder coordinator --help' for more information.", file=sys.stderr)
print("Please update it with your actual credentials and settings.")

# AFTER
logger.log(OUTPUT, "Try 'mcp-coder coordinator --help' for more information.")
logger.log(OUTPUT, "Please update it with your actual credentials and settings.")
```

### Per-File Details

**`cli/main.py`** (~15 prints):
- `_handle_coordinator_command()`: error prints → `logger.error()`
- `_handle_check_command()`: error prints → `logger.error()`
- `_handle_gh_tool_command()`: error prints → `logger.error()`
- `_handle_vscodeclaude_command()`: error prints → `logger.error()`
- `_handle_git_tool_command()`: error prints → `logger.error()`
- `_handle_commit_command()`: error print → `logger.error()`
- `main()`: `print(help_text)` → KEEP (data output); `print("\nOperation cancelled by user.")` → `logger.log(OUTPUT, ...)`; `print(f"Error: {e}")` → `logger.error()`
- Remove `import sys` if no longer needed after migration (check remaining uses)

**`cli/commands/commit.py`** (~8 prints):
- Error prints → `logger.error()`
- Success prints → `logger.log(OUTPUT, ...)`
- Preview mode prints (commit message display + confirmation prompt) → KEEP as `print()` (interactive terminal UI)

**`cli/commands/create_pr.py`** (~3 prints):
- Error prints → `logger.error()`
- "Operation cancelled" → `logger.log(OUTPUT, ...)`

**`cli/commands/create_plan.py`** (~3 prints):
- Error prints → `logger.error()`
- "Operation cancelled" → `logger.log(OUTPUT, ...)`

**`cli/commands/implement.py`** (~3 prints):
- Error prints → `logger.error()`
- "Operation cancelled" → `logger.log(OUTPUT, ...)`

**`cli/commands/init.py`** (~5 prints):
- All prints → `logger.log(OUTPUT, ...)` (status messages about config creation)

**`cli/commands/prompt.py`** (~8 prints):
- Error prints → `logger.error()`
- Status prints (session resumption) → `logger.log(OUTPUT, ...)`
- KEEP: `print(session_id)`, `print(json.dumps(...))`, streaming output — data

**`cli/commands/set_status.py`** (~6 prints):
- Error prints → `logger.error()`
- Success print → `logger.log(OUTPUT, ...)`
- KEEP: `print(format_status_labels(...))` when called without args — data output (listing labels)

**`cli/commands/gh_tool.py`** (~4 prints):
- Error prints → `logger.error()`
- KEEP: `print(base_branch)`, `print(branch_name)` — data output

**`cli/commands/git_tool.py`** (~3 prints):
- Error prints → `logger.error()`
- KEEP: `print(result)` — compact-diff data output

## DATA
- No new data structures
- All migrations are print→logging, no behavioral change

## HOW — Integration Points
- Each file adds `from ...utils.log_utils import OUTPUT` (adjust relative import depth)
- `sys.stderr` imports may become unnecessary in some files after migration — remove if unused
- `logger` already exists in all files (`logger = logging.getLogger(__name__)`)

## Commit Message
```
refactor(cli): migrate status/error prints to logging

- Error prints → logger.error()
- Status prints → logger.log(OUTPUT, ...)
- Keep data-producing prints (help, diffs, reports, JSON)
- Consistent logging across all CLI commands
```
