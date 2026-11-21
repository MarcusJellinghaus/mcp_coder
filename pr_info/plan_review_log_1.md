# review-plan review log 1

## Round 1 — 2026-11-21
**Findings**:
Plan files read; now checking key claims against the code.Now verify_sections.py around the project section.Checking icoder env_setup, info and banner code against Steps 4–5.Verifying the coordinator templates and remaining test-fixture claims.pr_info/steps/step_7.md:26 — medium — The Tests list leaves out two files that patch `mcp_coder.cli.commands.verify_sections.verify_toolkit`: `tests/cli/commands/test_verify_render.py:246` and `tests/cli/commands/test_verify_setup.py:214`. Step 7 removes that name from `verify_sections`, so `patch()` raises AttributeError in both. `test_verify_render.py:255` also pins the item indent `"      ruff "` (indent + 2), which becomes indent + 4 under the new action header. Add both files with the new patch target and the new indent.
pr_info/steps/step_11.md:27 — low — "any test asserting `source is None`" also matches `tests/utils/test_setup_config.py:75`, which checks `SetupConfig.source` and must not change. Limit the item to `ToolkitConfig.source` (`tests/utils/test_toolkit_config.py:30,38`).
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_7.md Tests list, add tests/cli/commands/test_verify_render.py (patch at line 246) and tests/cli/commands/test_verify_setup.py (patch at line 214): update their patch target from mcp_coder.cli.commands.verify_sections.verify_toolkit to the toolkit verify function\'s new location, and update the item indent assertion at test_verify_render.py:255 from indent + 2 ("      ruff ") to indent + 4 under the new action header.', 'In pr_info/steps/step_11.md:27, change "any test asserting `source is None`" to cover only ToolkitConfig.source (tests/utils/test_toolkit_config.py:30,38), and state that tests/utils/test_setup_config.py:75 (SetupConfig.source) stays unchanged.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-21
**Findings**:
Plan files read; now checking the plan's key claims against the code (toolkit_runner, verify, icoder, check loop).Still verifying: checking `mcp_verification.py`, the banner code and the test fixture against Steps 4, 5 and 11.Checking the remaining claims: ENVIRONMENT packages, `/info`, the event log, and pyproject's install config.pr_info/steps/step_7.md:78 — medium — The plan doesn't say what happens to an action group that ends up with no rows. Under the autouse stub (`verify_toolkit` → `[]`), PythonToolkit declares every default depth, so no depth rows are added either. That leaves three bare `format`/`check`/`test` header lines in the PROJECT section of every existing verify test. Groups also empty out when their items are lifted into global items. State that an action header is printed only when its group has a raised row, an item or a depth row, and add a test for it in `tests/cli/commands/test_verify_toolkit_rows.py`.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_7.md (around line 78), state that an action header (format/check/test) is printed only when its group has at least one row: a raised row, an item, or a depth row. Empty groups, including those emptied when their items are lifted into global items, print nothing. Add a test in tests/cli/commands/test_verify_toolkit_rows.py checking that no bare action header appears when verify_toolkit returns [] and every default depth is declared.'], escalate_reason=None)
**Changes**:
applied
