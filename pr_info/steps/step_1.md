# Step 1 — Add `--inexact` to all `uv sync --extra types` template lines

Refer to `pr_info/steps/summary.md` for the overall problem and fix rationale.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/command_templates.py` (implementation)
- `tests/cli/commands/coordinator/test_command_templates.py` (tests)

No new files. No new functions or classes — this step only changes literal
string content inside existing module-level `str` constants.

## WHAT

Module-level string constants to change in `command_templates.py`:

Linux (pattern `uv sync --extra types` → `uv sync --inexact --extra types`),
occurs once in each of:
- `DEFAULT_TEST_COMMAND`
- `CREATE_PLAN_COMMAND_TEMPLATE`
- `IMPLEMENT_COMMAND_TEMPLATE`
- `CREATE_PR_COMMAND_TEMPLATE`
- `REVIEW_PLAN_COMMAND_TEMPLATE`
- `REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE`

Windows (pattern `uv sync --project %WORKSPACE%\repo --extra types` →
`uv sync --inexact --project %WORKSPACE%\repo --extra types`), occurs once in
each of:
- `DEFAULT_TEST_COMMAND_WINDOWS`
- `CREATE_PLAN_COMMAND_WINDOWS`
- `IMPLEMENT_COMMAND_WINDOWS`
- `CREATE_PR_COMMAND_WINDOWS`
- `REVIEW_PLAN_COMMAND_WINDOWS`
- `REVIEW_IMPLEMENTATION_COMMAND_WINDOWS`

Test assertions to change in `test_command_templates.py`:

`TestLinuxTemplatesUseTypesExtra` (4 methods): each currently asserts
`"uv sync --extra types" in <TEMPLATE>`. Change the literal to
`"uv sync --inexact --extra types" in <TEMPLATE>`. The existing
`"uv sync --extra dev" not in <TEMPLATE>` assertions are unchanged.

`TestWindowsTemplatesInstallTypeStubs` (4 methods): each currently asserts
`"uv sync --project %WORKSPACE%" in <TEMPLATE>` and `"--extra types" in <TEMPLATE>`.
Add `assert "--inexact" in <TEMPLATE>` to each method (keep the two existing
assertions as-is).

Scope note: only the 8 existing assertions (4 Linux + 4 Windows, covering
`DEFAULT_TEST_COMMAND[_WINDOWS]`, `CREATE_PLAN`, `IMPLEMENT`, `CREATE_PR`) are
updated — the review-plan/review-implementation templates get the `--inexact`
fix in the implementation but have no dedicated sync-line test today, and
adding one is out of scope for this fix.

## HOW

TDD order within this one commit:
1. Edit the test file first so the 8 assertions require `--inexact` (now red,
   since the templates don't have it yet).
2. Edit `command_templates.py`. Since the Linux substring is identical across
   all 6 Linux templates, and the Windows substring is identical across all 6
   Windows templates, use `mcp__mcp-workspace__edit_file` with
   `replace_all=True` — two calls total (one per OS pattern) instead of 12
   separate edits.
3. Re-run tests — now green.

No imports, decorators, or new integration points — these are plain string
literals consumed later by `WORKFLOW_TEMPLATES` / `.format()`, which are
untouched.

## ALGORITHM

```
for each of the 2 edit_file calls:
    old_string = "uv sync --extra types"               # or the Windows variant
    new_string = "uv sync --inexact --extra types"      # or the Windows variant
    replace_all = True   # matches all 6 occurrences for that OS at once
```

## DATA

No data structures change. Return values of `.format()` calls on these
templates are unaffected beyond the added `--inexact` substring; the
`test_templates_placeholders_still_resolve` and
`test_all_templates_format_uniformly_with_all_kwargs` tests (unchanged) must
still pass, confirming no placeholder was accidentally altered.

## Commit

Run `mcp__mcp-tools-py__run_pylint_check`, `run_pytest_check`
(`extra_args=["-n", "auto"]`, excluding the integration markers per
CLAUDE.md), and `run_mypy_check` — all must pass. Then
`run_format_code`, stage, and commit:

```
fix(coordinator): preserve provisioned packages when syncing type stubs

Add --inexact to uv sync --extra types in all 12 command templates so
the sync is additive instead of exact, leaving packages from an earlier
`uv sync --extra dev` provisioning step installed.
```

## LLM prompt for this step

> Read `pr_info/steps/summary.md` and this file
> (`pr_info/steps/step_1.md`). Update
> `tests/cli/commands/coordinator/test_command_templates.py` so the 8
> assertions listed under WHAT require `--inexact`, confirm they fail, then
> update `src/mcp_coder/cli/commands/coordinator/command_templates.py` using
> two `replace_all` edits (one per OS) to add `--inexact` to all 12
> `uv sync ... --extra types` lines. Run pylint, pytest, and mypy; fix any
> failures. Format the code, then create exactly one commit with the message
> given in the "Commit" section.
