# review-implementation review log 1

## Round 1 — 2026-11-09
**Findings**:
Now the core source files.Reviewing remaining tests for spec coverage (warning-once, fix-turn grants, fragments, timeout).`src/mcp_coder/toolkits/command/toolkit.py:194` — medium — `_steps_text` removes duplicate steps by `label` (the step's name), not by command. If two steps share a `name` but run different commands (e.g. `name = "lint"` with `npm run lint` in `check.quick` and `npm run lint:strict` in `check.full`), only the first command is listed. The LLM then never gets the exact grant string for the second one, which breaks Scope 9 ("each granted step is given exactly as its grant string"). Remove duplicates by `step.grant` / argv instead, and add a test for it.

`src/mcp_coder/workflows/rebase.py:606` — low — `llm_permissions(project_dir, provider, entry)` runs on every rebase that reaches the regression check, even when there are no regressions. For Copilot/Langchain this logs the "Bash grants dropped" warning although no fix session ever starts. Compute `perms` / `check_tools` only once `regressions` is non-empty.
**Decisions**:
Verdict(decision='tasks', tasks=['In src/mcp_coder/toolkits/command/toolkit.py:194, change `_steps_text` so it removes duplicate steps by `step.grant` (or argv), not by `label`. Two steps with the same name but different commands (e.g. `lint` running `npm run lint` in check.quick and `npm run lint:strict` in check.full) must each have their exact grant string listed. Add a unit test for this case that checks both grant strings appear.', "In src/mcp_coder/workflows/rebase.py:606, call `llm_permissions(project_dir, provider, entry)` and compute `perms`/`check_tools` only after `regressions` is found to be non-empty. That way a rebase with no regressions does not log the 'Bash grants dropped' warning for Copilot/Langchain. Add or adjust a test that confirms the warning is not logged when there are no regressions."], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-09
**Findings**:
Reviewing the core diff is done; now checking the integration test and the end-to-end "done when" test.Checking the docs' bindings example, then I'll write the report.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
