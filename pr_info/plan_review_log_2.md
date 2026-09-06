# review-plan review log 2

Issue #1151 — refactor(install): make the installer package code and move
target-repo policy to the target repo.

Run 1 (`plan_review_log_1.md`) ran five rounds and stopped at the round limit
without converging. Two medium findings were reported in both round 4 and
round 5 and never applied:

- `step_5.md` — the `.sh` rewrite's new hard-fail branch is specified only in
  `.bat` form (`exit /b 1`); `reinstall_local.sh` is `source`-able and guards
  its failure path with `_SOURCED` (`return 1` vs `exit 1`).
- `step_2.md` — `subprocess_isolation`'s `source_modules` includes `tests`, and
  the plan adds no `tests.install` entry; the ported tests only stay legal
  because they reach subprocess as a module attribute.

This run carries those forward as pre-accepted work.

**Correction to the second pre-accepted item.** This round established that the
`tests.install` entry must *not* be added. An `ignore_imports` row that matches
no import edge is an `AlertLevel.ERROR` hard failure, and the ported tests reach
subprocess only as a module attribute, so the row would be unmatched. The real
work is to record that module-attribute constraint for whoever ports the tests.

**Note on run 1's provenance.** Run 1 was produced by the headless `review-plan`
workflow (`src/mcp_coder/workflows/review/`, `REVIEW_MAX_ROUNDS = 5` at
`core.py:55`), not by the interactive `plan_review` skills. Its non-convergence
causes are filed as #1155.

## Round 1 — 2026-09-06

**Findings** (9, none duplicating run 1):

- `step_2.md:161-165` — high — the prescribed `subprocess_isolation` pair is
  invalid. `unmatched_ignore_imports_alerting` defaults to `AlertLevel.ERROR`, so
  the bare `mcp_coder.install -> subprocess` row — which cannot match, since
  `subprocess` lives in `_env.py` — fails `lint-imports`. Contradicts an explicit
  Scope bullet in the issue.
- `step_2.md:161` (1b) — same mechanism reshapes the `tests.install` item: add no
  row; record the module-attribute constraint instead.
- `step_3.md:14` — medium — `workspace.py:554` names `install.py` and is unowned;
  the step lists only `:550` and `:561`, so its own `git grep` exit criterion
  cannot pass.
- `step_3.md:104-105`, `summary.md:135` — medium — "update the six
  `build_install_argv` assertions" is false; all six assert only
  `--skip-overrides`, which this refactor does not change. The file actually needs
  two docstring edits (`:4`, `:151`).
- `step_2.md:110` — medium — wrong line for the command count: `test_help.py:38`
  is `len(COMMAND_CATEGORIES) == 4`; the `== 22` assertion is at `:66`.
- `step_5.md:60-80` — medium — the wrapper rewrite drops the *existing*
  post-install failure guard (`reinstall_local.bat:14-17`, `.sh:15,20-23`),
  distinct from the new driver-resolution hard-fail.
- `step_3.md:14` — low — `session_setup.py:115` names the retired
  `install_script_path` and is invisible to an `install\.py` grep.
- `step_3.md` — low — the line-number enumeration style is the shared root cause
  of the three reference misses; replace with a grep exit criterion.
- `step_2.md:18-21` — low — test layout does not mirror src.

Verified-correct (no action): step atomicity throughout, coverage of the issue's
Scope and Tests sections, no new dependency, no coordinator version-skew risk, no
step missing a verification gate, and run 1's finding #7 (coordinator upgrade
prerequisite) confirmed invalid.

**Decisions**: all nine accepted. Eight applied as mechanical plan fixes. The
high finding was escalated because it contradicts the issue's Scope.

**User decisions**:

- Import-linter pair → *fix the plan only, leave the issue as it is, accept the
  gap.* The plan therefore records the divergence explicitly so an implementer
  does not revert it to the issue's wording.
- Skill/workflow improvements → filed as #1155 rather than changed in this run.

**Changes**: `step_2.md`, `step_3.md`, `step_5.md`, `summary.md`, and a new
`Decisions.md`. Step 3's reference enumeration became a two-pattern grep exit
criterion; the install test modules were renamed to mirror their sources and the
CLI-dispatch test relocated to `tests/cli/commands/test_install.py`.

**Status**: committed
