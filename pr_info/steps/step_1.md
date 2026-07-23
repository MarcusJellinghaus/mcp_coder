# Step 1 — Least-privilege permissions constant

Goal: define the in-code constant that holds exactly the write ops the automated
rebase session needs (git rebase/add/rm/commit/checkout/restore/remote get-url +
the MCP file/check tools) **and nothing more** — notably **no `push`** (Python
performs the force-push) and **no `uv lock`** (lockfiles are out of scope; see
summary). One commit.

## WHERE
- CREATE `src/mcp_coder/workflows/rebase_permissions.py` (module-level constant
  `REBASE_LLM_PERMISSIONS`).
- CREATE `tests/workflows/rebase/__init__.py` (empty)
- CREATE `tests/workflows/rebase/test_rebase_permissions.py`

Not a shipped JSON resource: a resource under `resources/claude/settings/` would
be gitignored and wiped+rebuilt by `setup.py` on every build, so it would vanish
at install time. The permissions live in code; Step 7 materializes a temp
settings file from this constant at runtime.

## WHAT
`REBASE_LLM_PERMISSIONS` — a `dict` holding the least-privilege Claude Code
settings/permissions payload, schema `{"permissions": {"allow": [...]}}` plus the
MCP-enablement keys. Content = `.claude/skills/rebase/SKILL.md` `allowed-tools`
for the git-write ops and MCP check/file tools it uses, converted to the
`settings.local.json` permission-string format, **minus** any `push` entry and
**minus** any `uv lock` entry.

Add a short module comment noting this constant is intended to be folded into the
configurable-permissions system from EPIC #1038 (sub-issue #1054, "Claude
provider — static settings translation") once that lands.

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
Bash(git remote get-url:*)
Bash(git status:*)
Bash(git diff:*)
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
- Imported by Step 7, which writes it as JSON to a temp file and passes that path
  to `prompt_llm` as `settings_file`.

## ALGORITHM
None (static constant).

## DATA
`dict`; `REBASE_LLM_PERMISSIONS["permissions"]["allow"]` is a `list[str]`.

## TESTS (write first)
`test_rebase_permissions.py` (unit test — asserts the dict's contents):
1. `REBASE_LLM_PERMISSIONS["permissions"]["allow"]` is a non-empty list.
2. Allow-list **contains** the git-write ops (`Bash(git rebase:*)`,
   `Bash(git add:*)`, `Bash(git commit:*)`, `Bash(git checkout --theirs:*)`,
   `Bash(git restore:*)`, `Bash(git remote get-url:*)`).
3. Allow-list contains **no** entry with substring `"push"` (guards the
   least-privilege / Python-pushes decision).
4. Allow-list contains **no** entry with substring `"uv lock"` (lockfile handling
   is out of scope for this repo).

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement Step 1
> (TDD). First write `tests/workflows/rebase/test_rebase_permissions.py` and an
> empty `tests/workflows/rebase/__init__.py` asserting `REBASE_LLM_PERMISSIONS`
> has a non-empty `permissions.allow` list that includes the git-write ops
> (`Bash(git rebase:*)` etc.) and excludes any `push` and any `uv lock`
> permission. Then create `src/mcp_coder/workflows/rebase_permissions.py` with the
> module-level `REBASE_LLM_PERMISSIONS` dict (SKILL.md `allowed-tools` git-write +
> MCP check/file tools, minus push, minus uv lock, in `settings.local.json` string
> format) and the MCP-enablement keys, plus a comment noting future folding into
> EPIC #1038 / #1054. Run pylint, pytest (`-n auto` with the unit-test marker
> exclusions), and mypy; fix all issues. Produce exactly one commit.
