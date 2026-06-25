# Decisions

Decisions logged from the plan-review triage discussion for issue #960.

## 2026-06-25 — Step 4 plan-review triage (3 accepted changes)

Tech lead triaged a plan review and accepted three changes, all scoped to Step 4
(formatter / `sdk_serialization` removal step). Applied via `/plan_update`.

1. **Remove the second stale architecture.md line (accepted).** Step 4 already
   schedules a fix for the `sdk_serialization.py` line in
   `docs/architecture/architecture.md`. The same file also has a stale line for
   `claude_code_api.py` (`- claude_code_api.py - Claude Code API integration
   (legacy, not used by interface)`). Since the module is deleted in Step 4
   (Step 3 explicitly leaves it intact), the doc fix belongs in Step 4's
   architecture.md edit. Added an instruction to also remove that line so no
   dangling doc reference to the deleted module remains.

2. **Refresh the formatters.py module docstring (accepted).** After deleting
   `format_text_response`, `format_verbose_response`, and `format_raw_response`,
   the module docstring describing "text, verbose, raw" output formats is stale.
   Added an instruction to Step 4 to rewrite the docstring to describe the
   surviving streaming role (`print_stream_event`).

3. **Tighten the `json` import wording (accepted).** Step 4's guidance about the
   `json` import in `formatters.py` was internally contradictory ("keep json" vs.
   "drop imports vulture flags"). `json` is still used by `print_stream_event`
   (`json.dumps(...)`), so it must be kept and vulture will not flag it. Tightened
   the wording to "Keep `json` (used by `print_stream_event`); remove only the
   `sdk_serialization` import" and removed the misleading "drop if vulture flags
   it" hedge as applied to `json`.

## 2026-06-25 — Step 4 plan-review triage round 2 (1 accepted change)

Tech lead triaged a second plan review and accepted one change, again scoped to
Step 4. Applied via `/plan_update`.

1. **Refresh the remaining stale doc prose created by Step 4's deletions
   (accepted).** Step 4 already edits the `sdk_serialization.py` /
   `claude_code_api.py` lines in `docs/architecture/architecture.md` and rewrites
   `src/mcp_coder/llm/formatting/__init__.py`, but three parallel prose
   descriptions go stale from the same deletions and were not yet covered.
   Extended Step 4 to also handle them:
   - `docs/architecture/architecture.md` — the `- **Formatting**: llm/formatting/
     - Response formatters and SDK utilities` line: drop "and SDK utilities"
     (gone once `sdk_serialization.py` is deleted).
   - `docs/architecture/architecture.md` — the `- formatters.py - Text/verbose/raw
     output formatting` line: rewrite to describe the surviving
     `print_stream_event` streaming role (`formatters.py` is streaming-only after
     this PR).
   - `src/mcp_coder/llm/formatting/__init__.py` — the module docstring
     `"Response formatting and SDK object serialization utilities."`: drop "SDK
     object serialization".
