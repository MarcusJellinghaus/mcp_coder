# Step 8: Migration note and doc updates

Documents the behaviour change and removes the old "mypy-only, log and continue" descriptions.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_8.md`. Implement step 8 only: create `docs/migration/multi-language.md` and update the four listed docs. Keep the wording short and factual. Run pylint, mypy and the fast pytest suite (docs tests may check links); all must pass. Format, then make one commit.

## WHERE
- Create `docs/migration/multi-language.md`.
- Modify `docs/repository-setup/python.md` (line ~22, `check_type_hints` row).
- Modify `docs/processes-prompts/processes/05-implementation.md` (line ~40).
- Modify `docs/architecture/architecture.md` (lines ~9, 26, 47, 60, 116).
- Modify `docs/repository-setup/quality-and-security-checks.md` (line ~50 and any "implement runs mypy" wording).
- If a docs index (e.g. `docs/README.md`) lists every doc and a test enforces it, add the new note there.

## WHAT

### `docs/migration/multi-language.md`
Title "Migration: multi-language toolkit". One section "Implement checks are a gate (#1389)" covering, as short bullets:
1. Behaviour change: `implement_task` runs `check@quick` per task; `implement_final` runs `check@standard` and `test@quick` as a gate. Checks run before tests; up to 3 LLM fix turns per binding run. At the cap a task commits and continues; the final check fails the run (`checks_exhausted`, label `implementing_failed`). An `error` result aborts the step. Every check-stage abort makes a rescue commit `wip(implement): checks failed (<reason>)` and pushes it.
2. Opt out of the per-task check: `implement_task = []` under `[tool.mcp-coder.toolkit.bindings]`.
3. Relax the gate per repo: `implement_final = ["check@quick", "test@quick"]`, or `[]` to turn it off.
4. `check@standard` needs pylint in the project env; a missing tool is `error` and aborts `implement_final` without a fix turn.
5. Repos without mypy abort at the per-task `check@quick` with `error`: set `[tool.mcp-coder.implement] check_type_hints = false`, which drops `check@*` from both implement bindings. `implement_task = []` alone isn't enough, because `check@standard` also runs mypy.
6. Check the `test@quick` budget against the suite: mcp-tools-py's default is 300 s; a timeout is `error`. Raise it with `pytest-timeout` in `[tool.mcp-tools-py]` (overrides every depth; this repo uses 1800).
7. Paths without the project venv: Windows `implement.bat` activates the tool env, and the Linux executor has no project venv until #1204 / AutoRunner#59. Where project dependencies aren't installed, collection failures become findings and the run fails at the cap, or at once as `general` if `conftest.py` can't import.
8. A toolkit without a `fix.check` or `fix.test` fragment (missing or empty) no longer just disables that fix loop: its findings fail `implement_final` at once.
9. A toolkit that doesn't declare a requested action or depth (e.g. a command toolkit with no `test.quick`) now aborts: `run_request` returns `error`, and `quick` has no lower depth to fall back to. Override `implement_task` / `implement_final` to match the declared depths.

Note at the top: #1199 extends this note.

### Doc fixes
- `python.md` `check_type_hints` row: "Bool, default `true`. `false` drops the `check@*` requests from the `implement_task` and `implement_final` bindings; the remaining requests (e.g. `test@quick`) still run. Set `false` for a repository without mypy." Link the migration note.
- `05-implementation.md` line ~40: after each task mcp-coder runs the `implement_task` binding (`check@quick`), after the last task the `implement_final` binding (`check@standard`, `test@quick`) as a gate, each with up to 3 LLM fix turns; at the cap the final check fails the run. Remove the claim that `check_type_hints = false` turns off the final check; say it drops the `check@*` requests. Point to the migration note for overrides.
- `architecture.md`: remove "`implement` calls Python tools directly (mypy, the formatter)" / "calls mypy and the formatter directly" / "(mypy, formatting)"; say `implement` runs checks, tests and formatting through the toolkit bindings. Line ~60: implement runs the `implement_task` and `implement_final` bindings with a capped fix loop; the final one is a gate. Line ~116: "after the last task runs the final checks and tests as a gate".
- `quality-and-security-checks.md` line ~50: replace "(mypy, ruff-format also run in `implement`)" with wording that `implement` runs the `implement_task` / `implement_final` bindings (mypy per task; mypy, pylint and fast pytest at the end, as a gate) and ruff-format on commit.

## HOW
Search each file for `mypy`, `continuing`, `continues`, `check_type_hints` and fix every hit that describes the old behaviour.

## ALGORITHM
None.

## DATA
None.

## Tests
No new tests. Run the fast suite in case docs link checks exist.
