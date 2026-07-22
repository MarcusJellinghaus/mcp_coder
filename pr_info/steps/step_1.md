# Step 1 — Least-privilege settings resource

Goal: ship the dedicated Claude settings file that pre-authorizes exactly the
write ops the automated rebase session needs (git rebase/add/commit/checkout/
restore + `uv lock` + the MCP file/check tools) **and nothing more** — notably
**no `push`** (Python performs the force-push). One commit.

## WHERE
- CREATE `src/mcp_coder/resources/claude/settings/rebase_settings.json`
- CREATE `tests/workflows/rebase/__init__.py` (empty)
- CREATE `tests/workflows/rebase/test_settings_resource.py`
- `pyproject.toml` is **unchanged** — `[tool.setuptools.package-data]` already
  declares `resources/claude/**/*`.

## WHAT
`rebase_settings.json` — Claude Code settings schema `{"permissions": {"allow": [...]}}`.
Content = `.claude/skills/rebase/SKILL.md` `allowed-tools`, converted to the
`settings.local.json` permission-string format, **minus** any `push` entry,
**plus** `"Bash(uv lock:*)"`. Include the MCP-enablement keys so tools resolve.

Required `permissions.allow` entries (colon form, matching `settings.local.json`):
```
mcp__mcp-workspace__git
Bash(git rebase:*)
Bash(git add:*)
Bash(git rm:*)
Bash(git commit:*)
Bash(git checkout --ours:*)
Bash(git checkout --theirs:*)
Bash(git restore:*)
Bash(git status:*)
Bash(git diff:*)
Bash(uv lock:*)
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-workspace__get_base_branch
mcp__mcp-workspace__read_file
mcp__mcp-workspace__save_file
mcp__mcp-workspace__edit_file
mcp__mcp-workspace__append_file
mcp__mcp-workspace__delete_this_file
mcp__mcp-workspace__move_file
mcp__mcp-workspace__list_directory
mcp__mcp-workspace__search_files
```
Plus top-level keys:
```
"enableAllProjectMcpServers": true,
"enabledMcpjsonServers": ["mcp-tools-py", "mcp-workspace"]
```

## HOW
- Located at runtime via
  `find_data_file("mcp_coder", "resources/claude/settings/rebase_settings.json")`
  (from `mcp_coder.utils.data_files`). Consumed later by Step 7.

## ALGORITHM
None (static resource).

## DATA
JSON object; `permissions.allow` is a `list[str]`.

## TESTS (write first)
`test_settings_resource.py`:
1. `find_data_file("mcp_coder", "resources/claude/settings/rebase_settings.json")`
   returns an existing path.
2. File parses as JSON; `data["permissions"]["allow"]` is a non-empty list.
3. Allow-list **contains** `"Bash(uv lock:*)"` and `"Bash(git rebase:*)"`.
4. Allow-list contains **no** entry with substring `"push"` (guards the
   least-privilege / Python-pushes decision).

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement Step 1
> (TDD). First write `tests/workflows/rebase/test_settings_resource.py` and an
> empty `tests/workflows/rebase/__init__.py` asserting the bundled rebase settings
> file resolves via `find_data_file`, is valid JSON with a non-empty
> `permissions.allow` list that includes `Bash(uv lock:*)` and `Bash(git rebase:*)`
> and excludes any `push` permission. Then create
> `src/mcp_coder/resources/claude/settings/rebase_settings.json` with the
> permission set listed in this step (SKILL.md `allowed-tools` minus push, plus
> `uv lock`, in `settings.local.json` string format) and the MCP-enablement keys.
> Do not modify `pyproject.toml` (package-data already covers
> `resources/claude/**/*`). Run pylint, pytest (`-n auto` with the unit-test
> marker exclusions), and mypy; fix all issues. Produce exactly one commit.
