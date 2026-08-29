# review-plan review log 3

Issue #1132 — Remove `--execution-dir`: collapse Claude's working directory onto `project_dir`.

Run 1 (`plan_review_log_1.md`) hit the 5-round limit and was handed to a human. Run 2
(`plan_review_log_2.md`) applied the lead-approved corrections in a single round (split
`step_4.md` into `4a`/`4b`, added test rule 3, created `Decisions.md`) but never ran a
confirming zero-change round. This run resumes from there.

Plan files under review: `summary.md`, `step_1.md`, `step_2.md`, `step_3.md`, `step_4a.md`,
`step_4b.md`, `step_5.md`, `Decisions.md`.

`TASK_TRACKER.md` has no populated tasks — no step is implemented yet, so the whole plan is
under review.

Base: branch is one commit behind `origin/main` (`47e72e0`, vscodeclaude session focus —
touches only `docs/coordinator-vscodeclaude.md`, four `workflows/vscodeclaude/` modules and
their tests). Disjoint from every file this plan modifies — **no rebase required**. Main's red
isort job is on that same unrelated file.

All eight of run 2's `Decisions.md` corrections were re-verified against the plan files and
confirmed landed.

## Round 1 — 2026-08-29

**Findings**: zero high — the reviewer could not break the greenness argument. Verified against
source: `project_dir` is in scope at every 4a call site; the two E1 exception rows are correct;
`RealLLMService`'s `*` insertion is safe (sole production construction passes by keyword);
`check_and_fix_ci`'s `execution_dir` is the last positional before a `*`; the 35
`@patch(...resolve_execution_dir)` decorators are exactly the 35 that exist; the `execution_dir`
marker is applied in exactly the three places step 3 removes.

- `step_5.md` — medium — the WHERE row and WHAT bullet name a "📂 Execution Directory Flag"
  section with a "Key Distinction" list. `.claude/CLAUDE.md` has no such heading; the real
  target is `## Execution directory` (`:130-135`).
- `step_4b.md` section F — medium — the docstring inventory lists four sites but reads as
  complete; 17 further `execution_dir:` `Args:` lines travel with the 23 deleted parameters.
  Nothing enforces this automatically (ruff's `DOC` rules check no argument lists), so an
  implementer would discover them only at the final grep.
- `step_2.md` WHAT — low — the illustrative `ask_copilot_cli` block adds a keyword-only `*` the
  current signature does not have and no requirement asks for. The block is written to be copied.
- `step_1.md` TDD step 1 — low — line labels are wrong: `:168` is a section comment, `:173` a
  class docstring, `:233` a test docstring. The real keyword arguments are `:269` and `:316`.
- `step_2.md` WHERE — low — copilot kwarg assertion sites unnamed (`test_interface.py:1989`,
  `:2012`).
- `step_3.md` — low — two comments explaining "`execution_dir=None` means the real
  `resolve_execution_dir` runs" survive the mechanical row and would name a deleted function.
- `step_4a.md` — low — the mypy caveat understates the tooling. CI runs `mypy --strict src
  tests` and these test functions are annotated, so mypy does report the missing argument.
- `summary.md` — low — the per-step quality gate omits `run_format_code`, which `.claude/
  CLAUDE.md` requires before every commit and CI gates on.
- Step sizing — observation — step 3 is the largest single commit (three CLI modules, nine
  commands, `pyproject.toml`, ~15 test files).

**Decisions**: accepted all eight defects — every one is a plan-precision problem, none touches
scope, architecture or step boundaries, so nothing was escalated. Skipped the step-3 split: the
flag has to disappear atomically with its nine call sites, and the alternative leaves two
resolvers coexisting, which is worse than a large step. Left the 4a line drift alone
(`Decisions.md` rules it out of scope) and did not chase line counts, per
`software_engineering_principles.md`.

**User decisions**: none required.

**Changes**: `step_5.md` retargeted onto `## Execution directory` (three edits, including the
same stale name inside the step's LLM prompt). `step_4b.md` section B gained the 17-line
docstring worklist plus the note that F carries only the docstrings with no parameter to delete.
`step_2.md` lost the `*` and gained the named assertion sites. `step_1.md` TDD step 1 rewritten
onto the real call, assertion and rename targets. `step_3.md` mechanical row gained the two
stale comments. `step_4a.md` mypy caveat replaced — mypy is the worklist, grep the safety net.
`summary.md` quality gate gained `run_format_code`. `Decisions.md` untouched.

**Status**: committed

## Round 2 — 2026-08-29

A confirming round with a fresh reviewer. All eight of round 1's fixes were re-verified against
source and confirmed landed and accurate. The reviewer also independently re-derived the hard
parts — the seven-signature greenness argument, the two E1 exception rows, the `RealLLMService`
keyword-only mechanism, the four dead `cwd = …` fallbacks, the 35 patched-resolver decorators,
the `report_context_root` arity collapse — and the complete `src/` inventory (all 219
`execution_dir` hits across 34 files map to a step). Confirmed no agent, skill or template
outside `docs/`, `.claude/CLAUDE.md` and `pr_info/` references the flag.

**Findings**: zero high.

- `step_4a.md` — medium — a seventh test pins the removed semantics:
  `tests/icoder/test_llm_service.py:338` `test_real_llm_service_project_dir_none` asserts
  `project_dir is None`. The step's `RealLLMService` sweep instruction ("add `project_dir=` to
  every construction that omits it") applied to this test leaves the assertion failing, so 4a
  is red at pytest.
- `step_4a.md` — medium — mechanical rule 1 has no test-side counterpart to the
  `commit_operations` E1 exception. `tests/workflow_utils/test_commit_operations.py:143`/`:154`
  passes and asserts `execution_dir="/x"`; rule 1 rewrites it to `project_dir == "/x"`, but 4a
  makes `commit_operations.py:166` pass `str(project_dir)` instead. Fails in 4a's own gate.
- `step_4b.md` — low — `tests/workflow_steps/test_ci.py:198` passes `cwd=` to `CIFixConfig`;
  neither mechanical rule matches it (both target `execution_dir=` keywords and `Namespace`
  attributes). Recoverable via mypy, but named nowhere.
- `step_4b.md` — low — the `generate_commit_message_with_llm` note names only the two `src/`
  callers, both already keyword-safe. The real positional callers are ~10 calls of
  `(project_dir, "claude", "api")` in `tests/workflow_utils/test_commit_operations.py`. After
  the deletion `"api"` silently rebinds onto `mcp_config`; both are `Optional[str]` and the
  tests mock `prompt_llm` without asserting it, so **neither mypy nor pytest catches it**.
- `step_3.md` — low — the renamed `test_claude_cwd_integration.py` keeps flag prose throughout
  the two surviving tests (docstrings `:8`, `:10`, `:232-233`, `:295-301`; comments `:314`,
  `:371`, and `:338-340`, which narrates `resolve_execution_dir`'s removed branch by name).
  Same defect class round 1 fixed for the `check_branch_status` comments; 4b's grep is
  `src/`-only so nothing catches it.
- `commit.py:98` — low — assigned to both step 3 and `step_4b.md` section F.
- `step_5.md` — low — `architecture.md:118` is listed as needing a deprecation clause trimmed;
  it has none and is already correct. The verification search pattern is also case-sensitive
  and would miss `:124`'s "Execution directory".
- `step_3.md` — low — the `prompt.py:68-70` inline comment becomes false and is assigned
  nowhere, unlike the analogous `commit.py:74-75` one.

**Decisions**: accepted all eight. The two medium findings each fail loudly inside 4a's own
quality gate rather than shipping, and the `generate_commit_message_with_llm` one fails
silently — all three have a real cost. The remaining five are cheap prose fixes in the same
defect class the plan already handles well. Nothing touched scope, architecture or step
boundaries, so nothing was escalated.

**User decisions**: none required.

**Changes**: `step_4a.md` gained the seventh delete-or-rewrite row plus a note that this
construction is handled by the table rather than by adding a directory, and the rule-1 exception
mirroring E1. `step_4b.md` section D named the `CIFixConfig` test construction; the
`generate_commit_message_with_llm` note now names the test file and states that a miss is
invisible to both gates; section F dropped `commit.py:98` to step 3. `step_3.md` extended the
rename row to the surviving prose and assigned the `prompt.py` comment. `step_5.md` dropped
`:118` and moved to a case-insensitive search pattern — the reviewer ran the new pattern rather
than assuming it. `summary.md` count corrected six → seven as a consequence of the first finding.
`Decisions.md` untouched.

**Status**: committed

## Round 3 — 2026-08-29

Second confirming round, fresh reviewer. Round 2's eight fixes re-verified against source and
confirmed landed and accurate, including running step 5's new case-insensitive search pattern
(20 hits in `docs/`, all inside the listed ranges, plus `.claude/CLAUDE.md:130,132,135`; no
other `.md` in the repo matches).

**Findings**: zero high — nothing ships broken; all three medium findings fail loudly inside
their own step's quality gate.

- `step_3.md` — medium — `tests/cli/commands/test_commit.py` is in no row.
  `TestCommitAutoExecutionDir` (`:786-980`) is a five-test class built on the flag, and the
  catch-all row does not authorise deleting a test. One must be deleted:
  `test_invalid_execution_dir_returns_error` (`:868-887`) asserts exit 1 and "execution
  directory" in the log, but step 3 deletes `commit.py:76-83` and `resolve_claude_cwd` cannot
  raise, so execution falls through to the unpatched real `generate_commit_message_with_llm`.
- `step_3.md` — medium — two assertions on the removed argparse attribute sit outside every
  listed range: `tests/cli/test_main.py:631` (`args.execution_dir is None` → `AttributeError`)
  and `tests/cli/commands/test_review.py:265` (`hasattr(args, "execution_dir")` → `False`).
- `step_4a.md` — medium — the delete-or-rewrite table and its single rule-1 exception are short
  by six sites: `test_prompt.py:1005-1035` (pins `project_dir`-as-prompt-switch and is reached
  by neither rule), `test_task_tracker_prep.py:100`, `:505`, `:457`, and
  `test_task_processing.py:1398`, `:1432`, whose `TestBranchNameSource` uses a deliberately
  distinct `_EXECUTION_DIR`.
- `tests/` — low — stale `execution_dir` names and prose remain unassigned across seven further
  files. The reviewer proposed one blanket sweep line rather than a fourth enumeration.

**Decisions**: accepted all four. Beyond them I asked for a structural change: three rounds have
each found more per-site test handling, so the blanket sweep was strengthened to close the class
rather than only catch identifiers — it must also catch assertions whose *expected value* pins
the removed semantics (a directory distinct from `project_dir`, or an `is None` on a now-required
argument), state that the enumerated tables are the known cases rather than a complete list, and
name mypy plus the step's own pytest run as the backstop. All three sweep steps carry a pointer
to it. Nothing escalated; scope, architecture and step boundaries untouched for the third round
running.

**User decisions**: none required.

**Changes**: `step_3.md` gained rows for `test_commit.py` and `test_review.py` and the stray
`test_main.py:631` assertion. `step_4a.md`'s table gained three sites and rule 1 gained two more
exceptions, with the class names and `TestBranchNameSource` docstring/constant routed to 4b.
`step_4b.md` gained the `test_commit.py:978-979` handover note (a `KeyError`, not a rename, once
`project_dir` becomes positional) and the new two-part `tests/` sweep subsection. `summary.md`
dropped the stale count and points at the sweep. `Decisions.md` untouched.

**Note**: rounds 2 and 3 were committed together — the round-2 commit agent was still running
when round 3's edits landed in the same files, so it was stopped before staging and the two
rounds were committed as one.

**Status**: committed

## Round 4 — 2026-08-29

Third confirming round, fresh reviewer. Round 3's fixes re-verified against source and confirmed
landed and accurate.

**The round's main question — does the two-part `tests/` sweep close the defect class?** Yes.
The reviewer walked all 37 `tests/` files carrying `execution_dir` and confirmed every one falls
under a mechanical rule, an enumerated table, or the sweep, with mypy and pytest behind them —
so individual unenumerated sites stopped being findings. It also checked for a second
type-invisible positional shift like `generate_commit_message_with_llm` and found none: every
other function losing a mid-signature `execution_dir` has a differently-typed next parameter, so
mypy discriminates, and `commit_changes`'s is keyword-only. `commit_operations.py:66-70` is
genuinely the unique case, and 4b already names it.

**Findings**: zero high, zero medium.

- `step_4b.md` — low — both sweep parts and all three mechanical rules key off the
  `execution_dir` keyword or identifier, so a test supplying the removed argument
  **positionally** carries neither. Two verified instances:
  `tests/cli/commands/test_verify_mcp_edit_smoke.py:115`, `:131`, `:147`, `:208` (the file
  contains no `execution_dir` string at all; after 4b, `str(tmp_path)` slides onto
  `symbols: dict[str, str]`) and `tests/cli/commands/test_check_branch_status_auto_fixes.py:88-90`.
  Both are caught by mypy or pytest, so 4b goes red rather than shipping broken.

**Decisions**: accepted. Skipped the `test_main.py:619` "six vs seven" item count, per
`software_engineering_principles.md`.

**User decisions**: none required.

**Changes**: `step_4b.md`'s sweep gained a third part, **Positional forms**, and section E2 named
the four `test_verify_mcp_edit_smoke.py` positional callers. Six cross-references describing the
sweep as "two-part" were updated to "three-part" as a mechanical consequence (`step_3.md`,
`step_4a.md`, `step_4b.md`'s own prompt, `summary.md`). The engineer verified its own edit and
corrected one miscitation in the process (`:97-99` → `:88-90`). `Decisions.md` untouched.

**Status**: committed

## Final Status

**Converged. The plan is ready for approval and implementation.**

Four rounds, three of them by independent fresh reviewers. Across all four, the architecture,
step boundaries, the 3 → 4a → 4b ordering argument, the greenness argument, the `inject_prompts`
per-call-site mapping and the provider decisions were never challenged — every finding was
plan-precision, and no question needed escalating to the user.

Verified independently, more than once: all 219 `execution_dir` hits across 34 `src/` files map
to a step; requirements 1-7 and all ten acceptance criteria are each assigned; the 23 signatures,
20 direct `prompt_llm` callers, 10 parser call sites, 35 `@patch(...resolve_execution_dir)`
decorators, three marker applications and 19 documentation references match the source exactly;
`W0613` really is disabled project-wide, so 4a's seven temporarily-unused parameters are
harmless; the `RealLLMService` keyword-only insertion is safe.

The review's one structural outcome: three consecutive rounds each found more per-site test
handling, so `step_4b.md` now ends with a three-part `tests/` sweep — identifiers and prose,
assertions whose expected value pins the removed semantics, and positional forms — stating
explicitly that the enumerated tables are the known cases rather than a complete list, with mypy
and each step's own pytest run as the backstop. Round 4 confirmed the sweep closes the class.

**Not converged by exhaustion.** Round 4 returned zero high and zero medium findings; the review
was closed on a single low-severity one-line addition, verified by the engineer that made it,
rather than on a round limit — unlike run 1, which hit the 5-round cap.

**Rounds**: 4. **Commits**: `5d948f9`, `559c533`, plus this round's.
**Rebase**: not required — branch one commit behind `origin/main` (`47e72e0`, vscodeclaude),
disjoint files. Main's red isort job is on that same unrelated file, not on anything this branch
touches.
**Next step**: implementation, starting with step 1.
