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

## Round 2 — 2026-09-06

**Round 1 fixes verified.** The reviewer re-checked all eight entries in
`Decisions.md` against the repository; every one landed correctly, including the
achievability of the new grep exit criterion (18 `src/` + 22 `tests/` hits, all
owned by Step 2 or 3) and the claim that `subprocess` is used only in `run()` and
`_ensure_system_uv()`, so the dropped bare `ignore_imports` row genuinely could
never have matched.

**Findings** (5, all mechanical, none needing a human decision):

- `step_2.md:79-84` — high — the WHAT block puts `MCP_CODER_REPO`,
  `REPORT_BINARIES` and `REPORT_PACKAGES` in `__init__.py`, but `_phases.py`
  consumes all three, closing an `__init__ ↔ _phases` cycle. `pycycle` is in
  Step 2's own verification block, so the step could not commit green. Same
  hazard the Decision 11/12 note already reasons about for `InstallConfig` — the
  constants were missed.
- `step_5.md:10-11`, `step_6.md:124` — medium — `reinstall_local.bat:3` and
  `.sh:3` ("Delegates to install.bat/install.sh in the same dir") are unowned.
  Step 6 is scoped to `docs/` so cannot reach `tools/`, yet its verification
  demands a clean whole-repo grep; Step 5's grep covers only `install\.py`. Same
  failure mode round 1 fixed for `src`/`tests`, with the scope not widened.
- `summary.md:170-172` — medium — `run_vulture_check` is missing from Steps 2 and
  3, though CI runs it in the same PR-only architecture job as tach, lint-imports
  and pycycle, which both steps do run. Step 2 is the step moving ~570 lines of
  never-vulture-scanned code into `src/`.
- six wrong line citations — low — pylint disable list, ruff, pycycle, tach
  `tests` array, and four of six assert lines in `step_3.md:121`.
- `summary.md:127-152` — low — Modified table omits the
  `tests/cli/commands/test_help.py` row that `step_2.md`'s WHERE table carries.

**Decisions**: all five accepted and applied. One reviewer item skipped as
cosmetic — `step_3.md:116`'s docstring sentence spans `:7-9` not `:8`, and the
grep exit criterion covers it regardless.

Note on the vulture finding: it is the *permitted* class of gate finding — a CI
gate absent from a step's verification block — as distinct from predicting a
gate's output, which is what burned run 1's rounds 3 and 4.

**User decisions**: none required this round.

**Changes**: see the round 2 commit.

**Status**: committed

## Round 3 — 2026-09-06

**Round 2 fixes verified.** All five landed correctly. The reviewer confirmed the
cycle reasoning against the real code (`_phase_install_main` uses
`MCP_CODER_REPO`, `_phase_versions` iterates the report lists, `subprocess`
appears only in `run()` and `_ensure_system_uv()` — both bound for `_env.py`), so
the resulting `__init__ → _phases → _env` graph is acyclic and the single
`ignore_imports` row is right. A repo-wide grep for all three `install.*`
patterns now shows every remaining hit owned by a step.

**Findings** (5, no highs, all mechanical, plus 2 judgment calls):

- `step_2.md` TESTS — medium — instructs porting `TestGithubOverridesParser`,
  but HOW drops the function it tests; its five cases already exist verbatim
  against the replacement in `tests/utils/test_pyproject_config.py:11-56`. Should
  be a deletion, keeping the `_write_pyproject` helper.
- `step_2.md` TESTS — medium — no harness named for the ported argv-level tests.
  `_run_install_check` and `TestUseSyncTargetGuard` drive `install.main(...)`, but
  the plan drops both `main` and `parse_args`. Left open, the likely wrong turns
  are re-adding `parse_args` or coupling `tests/install/` to `mcp_coder.cli`.
- `step_1.md`, `step_3.md`, `step_4.md` — medium — `run_ruff_check` missing from
  all three prompts although `summary.md` calls it non-optional and all three
  change Python under `src/`.
- `step_5.md` — low — the CI block rewrite would silently drop the job-local
  `env: UV_GIT_SHALLOW: "0"` (`ci.yml:158-160`, tied to #817), which sits between
  the two named comment ranges.
- `step_2.md` HOW — low — `test_every_leaf_is_described` asserts the subparser's
  `help=` equals `COMMAND_DESCRIPTIONS[name]`, so `add_install_parser` must pass
  the constant, not a literal.

**Decisions**: all five accepted. Both judgment calls also accepted:

- `docs/architecture/architecture.md` §5 gains an `install/` entry. Deliberately
  beyond the issue's Scope — §5 carries one section per top-level package and this
  PR creates the staleness, so it is a bounded Boy Scout fix in the step that
  already owns docs.
- The two-readers simplification (`get_install_extras` + `install_extras_declared`
  → one `-> str | None`) was passed to the engineer **conditionally**: collapse
  only if `step_4.md`'s documented rationale for splitting them does not hold.
  Not forced — a preference, not a defect.

Line-number citation precision was ruled out of scope for this round, per
`software_engineering_principles.md` ("precise line numbers are not crucial").
References that would *misdirect an edit* remain in scope; the cosmetic kind does
not. This closed the last cheap-findings channel.

**User decisions**: none required this round.

**Changes**: see the round 3 commit.

**Status**: committed

## Round 4 — 2026-09-06

**Round 3 fixes verified, including the design change.** The collapsed extras
reader is coherent end to end: `get_install_extras(project_dir, *, strict=False)
-> str | None` in Step 1, `from_args` as the sole `"dev"` fallback site reading
the Decision-17-resolved `local_path`, and Step 4's warn row as
`get_install_extras(folder_path) is None`. `--extras` keeps `default=None`, so an
explicit `--extras ""` stays distinguishable from not-passed (`""` is falsy but
not `None`, and only `is not None` is tested) — the issue's Decision 4 and its §4
contract table row are both satisfied. No stale `-> str` expectation and no
surviving `install_extras_declared` anywhere in `pr_info/steps/`. Each of steps 1,
2 and 4 is still green alone; Step 4 adds no tach or import-linter edge because
`workflows` already imports `pyproject_config`.

**Findings** (3, all low, all mechanical — no highs or mediums):

- `step_2.md` — low — the obsolete `install-env` name is ported into user-facing
  strings that no step owns: `_ensure_system_uv`'s two failure messages
  (`install.py:500,510`) and the header/footer prints (`:553`, `:566`). After
  Decisions 1–2 they name nothing invocable, and both steps' greps miss them.
- `step_5.md` — low — the `.sh` rewrite adds `MC` (and loop variable `p`) with no
  `MC=""` initializer and no `unset`. `[ -z "$MC" ]` is the only guard, so a second
  `source` in the same shell reuses the stale value and both variables leak. The
  script unsets everything else precisely because it is source-able; `.bat` is
  already safe via `set "MC="` inside `setlocal`.
- `step_2.md` — low — `_namespace`'s default pinning is directional and partial.

**Decisions**: first two accepted, plus the `# shellcheck disable=SC1091`
one-liner (`ci.yml:180`) folded into round 3's existing preservation clause — same
class as the `env:` fix.

Two items **skipped**, recorded rather than dropped:

- Hardening `_namespace`'s pinning to the complete namespace. The pin already
  works in the direction that matters, and the three pinned defaults are exactly
  the ones this refactor changes. Per `software_engineering_principles.md`, a
  change that only pays off if someone later makes a mistake is speculative.
- Moving the duplicated `_namespace` into `tests/install/conftest.py`. Raised as a
  preference; duplicating a small helper across two test modules is unremarkable.

**Stopping rule for round 5.** Rounds have gone 9 findings (1 high) → 5 (1 high)
→ 5 (0 high) → 3 (0 high, 0 medium). If round 5 surfaces only low or cosmetic
items with no correctness impact, the run stops and those are recorded here as
accepted-known rather than triggering another edit. Recording beats dropping —
run 1 dropped findings silently and the same ones resurfaced every round.

**User decisions**: none required this round.

**Changes**: see the round 4 commit.

**Status**: committed

## Round 5 — 2026-09-06

**Round 4 fixes verified.** All three landed. The reviewer also confirmed the
reworded `install-env` messages break no existing assertion — `TestEnsureSystemUv`
asserts only on `"pip install uv"` and `"astral.sh"` — and that a repo-wide grep
for `install-env` finds nothing outside the four ported strings and `ci.yml:179`,
which sits inside the block Step 5 replaces.

**Findings**: none. No high, no medium, no low worth acting on.

Re-verified this round: all 21 top-level symbols in `tools/install.py` are either
ported or explicitly dropped, with none unassigned; `extras = ""` is already safe
in the ported code (`_phase_install_main:347` guards on `if args.extras`, and the
`uv sync` loop skips empty segments), so the `""`-means-no-extras contract needs no
extra work; Step 3's atomicity claim holds exactly (`create_startup_script` touches
the filesystem for `mcp_coder_install_path` nowhere else once the resolver is
gone); the grep exit criterion remains achievable with every remaining hit owned by
a step; and the citations that could misdirect an edit all land on the right
construct.

Two items the reviewer considered and deliberately did not raise: the stale
`# Activate the venv install-env created` comment at `ci.yml:179` (Step 5's
replacement block simply does not carry it) and docstring-rule consequences of
relocating `format_toml_error` (Step 1's verification block runs
`run_ruff_check`, so it surfaces in-step).

**Decisions**: nothing to accept or skip.

**Changes**: none — the stopping rule's converged outcome.

**Status**: no changes needed

## Final Status

**Converged after 5 rounds.** Round 5 produced zero plan changes and an explicit
"ready for implementation" verdict.

| Round | Findings | Highs | Outcome |
|---|---|---|---|
| 1 | 9 | 1 | all applied; 1 escalated to the user |
| 2 | 5 | 1 | all applied |
| 3 | 5 | 0 | all applied, incl. 2 judgment calls |
| 4 | 3 | 0 | 2 applied, 2 skipped and recorded |
| 5 | 0 | 0 | converged |

**Commits**: `afa6efc`, `06a7917`, `bd740c2`, `040dd05`, plus this log.

**User decisions recorded**:

1. The `subprocess_isolation` row is fixed in the plan only; issue #1151's Scope
   bullet asserting "Both rows are required" is left as-is and the gap accepted.
   `Decisions.md` records the divergence and instructs against reverting it.
2. The review-workflow defects that made run 1 fail are filed as #1155 rather than
   fixed during this run.

**Deliberate scope addition**: `docs/architecture/architecture.md` §5 gains an
`install/` subsection (Step 6). Not in the issue's Scope; accepted because this
change creates the staleness.

**Skipped items, recorded rather than dropped**: the `_namespace` full-namespace
default pin and moving `_namespace` into `tests/install/conftest.py` (both
speculative or preference), and `step_3.md`'s `:7-9` docstring span (cosmetic, and
covered by the grep criterion).

**Why this run converged where run 1 did not.** Run 1 enumerated individual lint
rule codes into the plan, each edit forcing a round that found the next rule, and
it dropped findings silently so the same ones returned every round. This run ruled
lint-output prediction and line-citation auditing out of scope, replaced step 3's
reference enumeration with a grep exit criterion that closes the whole class, and
recorded every skipped item. The plan is ready for approval.
