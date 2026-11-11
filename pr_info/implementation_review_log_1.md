# review-implementation review log 1

## Round 1 — 2026-11-11
**Findings**:
Reviewing the #1200 docs diff; now checking `toolkits.md` claims against `toolkit_runner.py` and the command toolkit source.Checking `toolkit-interface.md` claims against `commit.py` and `verify_sections.py` next.Both new pages match the code so far. Now reviewing the edits to existing docs.tests/workflows/implement/test_core_workflow.py:70 — low — Out-of-scope test change on a docs-only issue (#1200 Constraints: "Docs only; no code change"; summary.md: "No code, test or config change"). It mocks `run_finalisation` and `get_current_branch_name` in a Windows-only test. It is reasonable as a test-isolation fix, but the PR description must call it out and say why, or it should move to its own PR.
docs/configuration/toolkits.md:29 — low — "also needs its `[tool.mcp-coder.toolkit.command]` step tables, at least `format`, or `mcp-coder verify` fails" is stated unconditionally. It contradicts the "Formatting off" section (line 294–302) and the code: `_toolkit_rows` and `check_formatter_config` skip `verify(…, "format")` when `commit = []` or `format_code` is off. Scope it to "unless formatting is off" or link `#formatting-off`.
**Decisions**:
Verdict(decision='tasks', tasks=['In docs/configuration/toolkits.md:29, make the statement that `[tool.mcp-coder.toolkit.command]` step tables (at least `format`) are required for `mcp-coder verify` conditional: add "unless formatting is off" and link to the `#formatting-off` section. This matches the section at lines 294–302 and the `_toolkit_rows`/`check_formatter_config` behaviour, which skips the `format` verify when `commit = []` or `format_code` is off.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-11
**Findings**:
Spot-checked the new pages' cited symbols against the code (all match); now checking the mcp-tools-py depth table and the edits to existing docs.tests/workflows/implement/test_core_workflow.py:70 — low — Still unresolved from round 1: the issue is docs-only ("Docs only; no code change"), but this branch also changes a test. The PR description must name the change and give the reason, or the change should move to its own PR.
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
