# Plan Review Log — Issue #1022 (Split `cli/commands/coordinator/commands.py`)

Supervised plan review. Base: main. Branch: 1022-split-cli-commands-coordinator-commands-py.

## Round 1 — 2026-07-06

**Findings** (from `/plan_review` engineer):
- Plan files (summary.md, step_1.md, step_2.md) exist and are internally consistent; two-step structure (test reorg → source move) is sound and each step is one commit. Step 2 cannot be sub-split.
- Verified against real code: the 5 moved / 3 kept functions match; `IssueData` is VSCodeClaude-only; the trailing-dot blanket replace is safe (no double-substitution, skips `from … import` lines); `test_integration.py` needs no repoint (Jenkins-path deps); both workflow test files auto-update + get repointed; both src importers use the package facade so `__all__` stays unchanged.
- [STRAIGHTFORWARD] Step 2 blanket repoint in `test_vscodeclaude_cli.py` also touches PRE-EXISTING `coordinator.commands.` patch strings (e.g. `TestCommandHandlers`), not just the two moved classes — plan under-described this.
- [STRAIGHTFORWARD] `TestAtCapacityDiagnosticLog` has a third method (`test_process_eligible_issues_at_capacity_log_is_debug`) that imports `process_eligible_issues` directly and patches nothing on `coordinator.commands`; moves cleanly, needs no repoint — not enumerated.
- [STRAIGHTFORWARD] summary.md KISS wording "references only moved symbols" is imprecise — several repointed deps are SHARED and survive in `commands.py` (`load_config`, `create_default_config`, `get_config_file_path`, `IssueManager`, `IssueBranchManager`, `load_repo_config`).
- [STRAIGHTFORWARD / key] Plan asserts but does not hard-gate two `move_symbol` behaviors: rewriting in-function imports, and duplicating every SHARED dependency into the new module. If a shared dep is missing from `commands_vscodeclaude.py`, repointed `@patch` strings raise `AttributeError`. The dry-run preview should be an explicit checklist.
- Note (no action): `check_file_size(max_lines=750)` is the allowlist gate, not the 600-line goal; both files land ~370/~460 lines.

**Decisions** (tech lead triage):
- No [DESIGN/REQUIREMENTS] items — clean mechanical refactor, nothing escalated to user.
- ACCEPT (substantive): harden Step 2 `move_symbol` dry-run into an explicit pre-apply verification gate (in-function import rewrite + shared-dep duplication).
- ACCEPT (clarity): note pre-existing patch strings repointed in `test_vscodeclaude_cli.py`; enumerate the third `TestAtCapacityDiagnosticLog` method.
- ACCEPT (cosmetic): fix "references only moved symbols" wording in summary.md.
- SKIP: `check_file_size(max_lines=750)` — correct as-is, no change.

**User decisions**: None required — no design/requirements questions raised.

**Changes** (via `/plan_update`):
- `pr_info/steps/step_2.md`: added a `## GATE` section converting the dry-run preview into a hard pre-apply checklist; added a scope note that the blanket `replace_all` also repoints pre-existing patch strings in `test_vscodeclaude_cli.py`.
- `pr_info/steps/step_1.md`: enumerated the three methods of `TestAtCapacityDiagnosticLog` and noted the direct-import method needs no repoint.
- `pr_info/steps/summary.md`: reworded KISS decision 1 — the repoint follows the function under test into its new namespace regardless of whether the patched symbol is shared.

**Status**: Plan changed this round — committing; loop continues with a fresh review round.


## Round 2 — 2026-07-06

**Findings** (from fresh `/plan_review` engineer, verifying Round-1 revisions):
- Plan is now internally consistent; all four Round-1 revisions read coherently and are factually accurate against the code.
- Verified: the GATE's named shared deps are genuinely used by BOTH families (so `move_symbol` really could leave them behind); the 7 pre-existing `coordinator.commands.` patch strings in `test_vscodeclaude_cli.py` exercise moved functions (repoint correct); `TestAtCapacityDiagnosticLog`'s third method needs no repoint; reworded KISS rationale matches reality.
- Completeness cross-check: repo-wide search finds exactly 5 files with `coordinator.commands.<symbol>` patch strings — the 3 repointed all patch moved deps; the 2 left untouched (`test_commands.py` post-Step-1, `test_integration.py`) patch only Jenkins deps. Scope correct and complete.
- No new inconsistencies introduced by the Round-1 edits.
- [STRAIGHTFORWARD, minor/optional] The GATE hardens the destination (missing dep → AttributeError) but not source-side unused-import pruning in `commands.py`. Low risk — `run_pylint_check`/`run_vulture_check` in the verify suite already backstop it.

**Decisions** (tech lead triage):
- No [DESIGN/REQUIREMENTS] items.
- SKIP the optional source-side pruning note: already backstopped by pylint/vulture in the verify suite; adding it does not simplify the plan. Default-to-simpler.

**User decisions**: None required.

**Changes**: None — plan unchanged this round.

**Status**: Zero plan changes → review loop terminates.

## Final Status

- **Rounds run**: 2
- **Commits produced**: 1 plan-content commit (`00fb577` — Round 1 hardening) plus the log commit.
- **Outstanding design/requirements questions**: None — clean mechanical move-don't-change refactor, nothing escalated to the user.
- **Verdict**: Plan is internally consistent, scope-complete, and verified against the real source/tests. **Ready for approval / implementation.**
