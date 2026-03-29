# Plan Review Log 2 — Issue #624

CLI: add '--help' hint to argument error messages

## Round 1 — 2026-03-29
**Findings**:
- 1 Critical: `_handle_commit_command` else branch is NOT dead code — reachable when `commit_mode=None` (no subcommand given). Wrongly listed in step 3 as dead code to delete.
- 8 Accept: plan structure, subparser inheritance, algorithm, error paths, `add_help=False` compatibility, test coverage, step self-containment all verified correct against source code
- 1 Skip: pre-existing stdout/stderr inconsistency in manual error paths (out of scope)

**Decisions**:
- Critical #1: Accept and fix — straightforward factual correction. Move `_handle_commit_command` from step 3 (deletion) to step 2 (add help hint + logger downgrade). Add test.
- All Accept items: no changes needed
- Skip #8: ignored (pre-existing issue, out of scope)

**User decisions**: none needed

**Changes**:
- `pr_info/steps/step_2.md` — added `_handle_commit_command` to manual error path table, added `test_commit_no_subcommand_shows_help_hint` to test list, updated note about dead vs reachable code
- `pr_info/steps/step_3.md` — struck through `_handle_commit_command` row, added explanation that branch is reachable and moved to step 2

**Status**: committed (f6abc27)

## Round 2 — 2026-03-29
**Findings**: Re-verified step_2.md and step_3.md against source code. All corrections applied correctly. Remaining dead code entries in step 3 confirmed truly unreachable. Minor note: `_handle_commit_command` error message says "Commit mode 'None' not yet implemented" for the no-subcommand case — implementer can adjust wording during step 2.
**Decisions**: No further changes needed.
**User decisions**: none
**Changes**: none
**Status**: no changes needed

## Final Status

- **Rounds**: 2 (1 with changes, 1 verification)
- **Commits**: 1
- **Plan status**: Ready for approval. Critical finding resolved (commit_command reclassified). Plan has 3 steps: parser subclass, CLI wiring (now with 8 manual error paths), dead code removal (now 5 branches, not 6).
