# Migration: multi-language toolkit

> #1199 extends this note.

## Implement checks are a gate (#1389)

- **Behaviour change.** `implement_task` runs `check@quick` after each task; `implement_final` runs `check@standard` and `test@quick` after the last task, as a gate. Checks run before tests. Each binding run gets up to 3 LLM fix turns.
  - At the cap, a task commits and continues; the final check fails the run (`checks_exhausted`, label `implementing_failed`).
  - An `error` result aborts the step.
  - Every check-stage abort makes a rescue commit `wip(implement): checks failed (<reason>)` and pushes it.
- **Opt out of the per-task check:** `implement_task = []` under `[tool.mcp-coder.toolkit.bindings]`.
- **Relax the gate per repo:** `implement_final = ["check@quick", "test@quick"]`, or `[]` to turn it off.
- **pylint required.** `check@standard` needs pylint in the project env. A missing tool is `error` and aborts `implement_final` without a fix turn.
- **Repos without mypy** abort at the per-task `check@quick` with `error`. Set `[tool.mcp-coder.implement] check_type_hints = false`, which drops `check@*` from both implement bindings. `implement_task = []` alone isn't enough, because `check@standard` also runs mypy.
- **Test budget.** Check the `test@quick` budget against the suite: mcp-tools-py's default is 300 s, and a timeout is `error`. Raise it with `pytest-timeout` in `[tool.mcp-tools-py]` (overrides every depth; this repo uses 1800).
- **Paths without the project venv.** Windows `implement.bat` activates the tool env, and the Linux executor has no project venv until #1204 / AutoRunner#59. Where project dependencies aren't installed, collection failures become findings and the run fails at the cap, or at once as `general` if `conftest.py` can't import.
- **Missing fix fragments.** A toolkit without a `fix.check` or `fix.test` fragment (missing or empty) no longer just disables that fix loop: its findings fail `implement_final` at once.
- **Undeclared actions or depths.** A toolkit that doesn't declare a requested action or depth (e.g. a command toolkit with no `test.quick`) now aborts: `run_request` returns `error`, and `quick` has no lower depth to fall back to. Override `implement_task` / `implement_final` to match the declared depths.
