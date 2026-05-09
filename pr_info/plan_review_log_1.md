# Plan Review Log — Run 1

**Issue:** #963 — vscodeclaude: implement macOS/Linux launch support
**Branch:** 963-vscodeclaude-implement-macos-linux-launch-support
**Started:** 2026-05-09

This log records each review round, findings, decisions, and resulting plan changes. The supervisor loop runs review rounds until a round produces zero plan changes.


## Round 1 — 2026-05-09

**Findings** (engineer report, condensed):
- summary.md: wrong MCP tool namespace (`mcp__tools-py__` vs `mcp__mcp-tools-py__`); incomplete pytest exclusion list (missing copilot_cli, jenkins, llm, textual integration markers).
- step_1.md: "three test cases" said where four are listed.
- step_2.md: parametrized "wrong platform file" test under-specified — what files must be present per platform run is ambiguous.
- step_4.md: `(n/a)` cells in test cases table weaken platform-isolation assertion; unused `is_windows` local not explicitly removed in the plan.
- step_5.md: docstring `Raises:` block not updated; test #6 vague "or equivalent" marker check; missing intervention POSIX test; missing PATH-re-prepend test; `{mcp_config}` slot asymmetry not surfaced; `VSCODE_PROCESS_NAMES` macOS verification (issue requested) not in plan.
- step_5.md (DESIGN): plan applied POSIX `'` escape to title + repo + status + url + emoji via a function-local `q()` helper, contradicting issue Decisions ("Inline replace + single-quote wrapping. No helper function.").
- (Borderline, skipped) step 3 could merge with step 5; `regenerate_session_files` POSIX spot-check; explicit Windows-regression assertion enumeration.

**Decisions:**
- Accepted: all STRAIGHTFORWARD fixes (tool names, exclusion list, test count, test specs, missing tests, docstring update, asymmetry note, `VSCODE_PROCESS_NAMES` verification note, `is_windows` cleanup, concrete test table values).
- Skipped: borderline merges and speculative additions (per software_engineering_principles.md: skip cosmetic / pre-existing).
- Escalated to user: POSIX escape scope (3 options presented).

**User decisions:**
- POSIX escape scope → **Option A**: escape `title` only, inline `.replace()`, no helper (not even function-local). Other banner fields (`repo`, `status`, `issue_url`, `emoji`, `issue_number`) come from controlled sources (GitHub naming rules, project labels, URL encoding, codepoints, integers) — none can structurally contain `'`. Matches issue Decisions table; defensive escaping of fields that can't carry `'` is YAGNI.

**Changes applied:**
- `summary.md`: fixed tool namespace; full CLAUDE.md exclusion marker list.
- `step_1.md`: count corrected.
- `step_2.md`: explicit per-platform fixture spec for `test_does_not_accept_wrong_platform_file`.
- `step_4.md`: concrete values replace `(n/a)`; removal of unused `is_windows` made explicit.
- `step_5.md`: docstring update; tightened test #6; added test #13 (intervention POSIX) and #14 (PATH re-prepend); `{mcp_config}` slot asymmetry note; `VSCODE_PROCESS_NAMES` macOS verification note; replaced `q()` helper / multi-field escape with inline title-only escape (Option A).

**Status:** committing via commit agent.

## Round 2 — 2026-05-09

**Findings:**
- Template-count typo: plan said "six" POSIX template constants in 5 places (summary.md L33, L47, L66; step_5.md L7, L17) but the table actually lists seven, and the existing Windows side has seven (`STARTUP_SCRIPT_WINDOWS`, `INTERVENTION_SCRIPT_WINDOWS`, `VENV_SECTION_WINDOWS`, `INTERACTIVE_ONLY_SECTION_WINDOWS`, `AUTOMATED_SECTION_WINDOWS`, `AUTOMATED_RESUME_SECTION_WINDOWS`, `INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS`).
- step_4.md style divergence: WHAT block initializes `setup_commands: list[str] = []` before the loop; ALGORITHM block uses `for/else: commands = []`. Functionally equivalent but the inconsistency confuses the implementer.

**Round 1 verification:** all seven Round-1 changes landed correctly. No traces of the `q()` helper remain after Option A.

**Decisions:** both findings STRAIGHTFORWARD — no user input needed. Accepted both.

**Changes applied:**
- `summary.md`: three "six" → "seven" replacements.
- `step_5.md`: Goal line, WHAT header replaced; redundant `(Seven total — ...)` parenthetical removed.
- `step_4.md`: ALGORITHM rewritten in the simpler initialize-before-loop form; trailing one-liner split into 3 lines.

**Status:** committing via commit agent.

## Round 3 — 2026-05-09

**Findings:** none.

**Round 2 verification:**
- "six" → "seven" replacement: LANDED-OK across all 5 referenced locations; no stray "six" remains.
- step_4 ALGORITHM style alignment: LANDED-OK; uses initialize-before-loop, mirroring the WHAT block.

**Step-by-step verdict:** all six plan files PASS. Design decisions, file/function targets, test cases, and acceptance criteria are internally consistent.

**Status:** no plan changes this round → loop terminates.

---

## Final Status

- **Rounds run:** 3
- **Commits produced (excluding this log):**
  - `cf3585c` — Plan review round 1: fix tool names, clarify tests, simplify POSIX escaping (#963)
  - `b6f3a0d` — Plan review round 2: fix template count, align step_4 algorithm style (#963)
- **User decisions captured:** 1 (POSIX escape scope → Option A: title-only, inline replace, no helper function)
- **Outcome:** Plan is **ready for approval**.

### Summary of plan health (post-review)

The implementation plan for issue #963 (vscodeclaude macOS/Linux launch support) is internally consistent across `summary.md` and `step_1.md` … `step_5.md`. All design decisions in the issue's Decisions table are reflected in the plan. Test plans are concrete and parametrized over Windows / Darwin / Linux where relevant, with explicit per-platform fixture specifications. The biggest design correction during review was simplifying the POSIX single-quote escape from a multi-field `q()` helper down to an inline `title`-only `.replace()` call, matching the issue's "Inline replace + single-quote wrapping. No helper function." decision exactly.

No remaining open questions, scope concerns, or plan-vs-code mismatches.
