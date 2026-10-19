
# Step 1 — Remove the type-stub `uv sync` step from coordinator templates

See `pr_info/steps/summary.md` for full context.

**LLM prompt:** Read `pr_info/steps/summary.md` and this file in full before making
any change. Implement exactly what is specified below for issue #1243, step 1 of 2.
Produce exactly one commit containing both the test changes and the implementation
changes.

## Precondition check (do this first)

Open `src/mcp_coder/cli/commands/coordinator/command_templates.py` and verify both
exact substrings below are present, verbatim, in the file:

- Substring A (Windows, appears 8 times):
  `"echo Install type stubs in project environment ====================\nuv sync --inexact --project %WORKSPACE%\\repo --extra types\n\n"`
- Substring B (Linux, appears 8 times):
  `"uv sync --inexact --extra types\n"`

If either substring does not match verbatim (different wording, different count of
`=` characters, different line breaks, etc.), **write one line to
`pr_info/.blocked.txt` and stop.** Do not attempt to guess or fix up the template
text yourself.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/command_templates.py` — remove the step
  from all 16 occurrences (8 Windows constants, 8 Linux constants).
- `tests/cli/commands/coordinator/test_command_templates.py` — replace the two test
  classes that currently assert the step's *presence*.

## WHAT

No new functions or symbols. This step only edits existing module-level string
constants and test methods.

Windows constants affected (8): `DEFAULT_TEST_COMMAND_WINDOWS`,
`CREATE_PLAN_COMMAND_WINDOWS`, `IMPLEMENT_COMMAND_WINDOWS`,
`CREATE_PR_COMMAND_WINDOWS`, `REVIEW_PLAN_COMMAND_WINDOWS`,
`REVIEW_IMPLEMENTATION_COMMAND_WINDOWS`, `FIX_CI_COMMAND_WINDOWS`,
`FIX_CONFLICT_COMMAND_WINDOWS`.

Linux constants affected (8): `DEFAULT_TEST_COMMAND`, `CREATE_PLAN_COMMAND_TEMPLATE`,
`IMPLEMENT_COMMAND_TEMPLATE`, `CREATE_PR_COMMAND_TEMPLATE`,
`REVIEW_PLAN_COMMAND_TEMPLATE`, `REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE`,
`FIX_CI_COMMAND_TEMPLATE`, `FIX_CONFLICT_COMMAND_TEMPLATE`.

## HOW (TDD order)

1. **Tests first.** In `tests/cli/commands/coordinator/test_command_templates.py`,
   delete the classes `TestLinuxTemplatesUseTypesExtra` and
   `TestWindowsTemplatesInstallTypeStubs`. Replace them with one new class,
   `TestTypeStubSyncStepRemoved`, containing exactly two test methods (see
   ALGORITHM below). Run the targeted test file — the two new methods must
   **fail** at this point (the step is still in the templates), confirming the
   test actually exercises the change.
2. **Implementation.** In `command_templates.py`, remove substring A from all 8
   Windows constants and substring B from all 8 Linux constants (a single
   find-and-replace-all per substring is sufficient since the text is identical
   in every occurrence). Do not alter any other line.
3. Re-run the targeted test file — both new methods must now **pass**.
4. Run the full check suite (pylint, pytest with `-n auto` excluding integration
   markers per CLAUDE.md, mypy) and fix anything it flags in these two files.
5. Run `mcp__mcp-tools-py__run_format_code`, then stage and commit both files
   together in one commit.

## ALGORITHM

```
class TestTypeStubSyncStepRemoved:
    def test_linux_templates_have_no_type_stub_sync(self):
        for template in (DEFAULT_TEST_COMMAND, CREATE_PLAN_COMMAND_TEMPLATE,
                          IMPLEMENT_COMMAND_TEMPLATE, CREATE_PR_COMMAND_TEMPLATE,
                          REVIEW_PLAN_COMMAND_TEMPLATE,
                          REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
                          FIX_CI_COMMAND_TEMPLATE, FIX_CONFLICT_COMMAND_TEMPLATE):
            assert "uv sync --inexact --extra types" not in template

    def test_windows_templates_have_no_type_stub_sync(self):
        for template in (DEFAULT_TEST_COMMAND_WINDOWS, CREATE_PLAN_COMMAND_WINDOWS,
                          IMPLEMENT_COMMAND_WINDOWS, CREATE_PR_COMMAND_WINDOWS,
                          REVIEW_PLAN_COMMAND_WINDOWS,
                          REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
                          FIX_CI_COMMAND_WINDOWS, FIX_CONFLICT_COMMAND_WINDOWS):
            assert "uv sync --inexact --project" not in template
            assert "Install type stubs in project environment" not in template
```

Each loop iteration is one assertion target → 8 + 8 = 16 assertions total,
matching the issue's required coverage (all 8 templates per platform, not just
the 4 previously covered).

## DATA

No return values or data structures — this step is pure string-constant editing
and boolean pytest assertions. No new imports are needed in either file (all
referenced constants are already imported in the test file's existing import
block).
