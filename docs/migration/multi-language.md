# Migration: multi-language toolkit

Configuration reference: [toolkits](../configuration/toolkits.md).

## A toolkit is required; mcp-tools-py is optional (#1199)

- **No toolkit is an error.** Without `[tool.mcp-coder.toolkit]`, or with a table that has no `toolkit` key, mcp-coder no longer falls back to `mcp-tools-py`: the format pre-flight stops workflows and `mcp-coder verify` fails, both with the snippets to paste. Python repos add `toolkit = "mcp-tools-py"` to `pyproject.toml`; see [Configure a toolkit](../configuration/toolkits.md#configure-a-toolkit).
- **mcp-tools-py is the `python` extra.** It (and with it black, isort, ruff and the other checkers) no longer installs with mcp-coder. Python repos install `pip install "mcp-coder[python]"`; `dev` includes it. A missing extra is a config error with the install hint; the ENVIRONMENT row shows `[WARN] not installed (optional)`, and the launchers warn and continue.
- **Required MCP servers come from the toolkit.** `mcp-workspace` plus the servers named in the toolkit's `llm_permissions`: `mcp-tools-py` for the Python toolkit, none for `command`. `mcp-coder verify` fails when a required server is `not listed` by `claude mcp list`. See [Required MCP servers](../configuration/toolkits.md#required-mcp-servers).
- **Non-Python repos drop `mcp-tools-py` from `.mcp.json`.** Every `.mcp.json` server is still fatal at session start.
- **`verify` checks every binding.** It runs the toolkit's `verify()` for each requested action, not just `format`, and reports requested depths the toolkit doesn't declare. A command toolkit missing e.g. `test.quick` or `test.unattended` now fails `verify` instead of at run time.
- **`check_type_hints` is retired; bindings are the only switch.** `[tool.mcp-coder.implement] check_type_hints = false` no longer drops `check@*`. Repos without mypy set `implement_task = []` and `implement_final = ["test@quick"]` under `[tool.mcp-coder.toolkit.bindings]`. `mcp-coder verify` fails on a leftover `false` while the implement bindings still request checks, and warns about any other leftover value.
- **Neutral names.** The implement stage "Final mypy check" is now "Final checks"; fix-turn sessions `step_N_mypy_M` are now `step_N_check_M`.

## Implement checks are a gate (#1389)

- **Behaviour change.** `implement_task` runs `check@quick` after each task; `implement_final` runs `check@standard` and `test@quick` after the last task, as a gate. Checks run before tests. Each binding run gets up to 3 LLM fix turns.
  - At the cap, a task commits and continues; the final check fails the run (`checks_exhausted`, label `implementing_failed`).
  - An `error` result aborts the step.
  - Every check-stage abort makes a rescue commit `wip(implement): checks failed (<reason>)` and pushes it.
- **Opt out of the per-task check:** `implement_task = []` under `[tool.mcp-coder.toolkit.bindings]`.
- **Relax the gate per repo:** `implement_final = ["check@quick", "test@quick"]`, or `[]` to turn it off.
- **pylint required.** `check@standard` needs pylint in the project env. A missing tool is `error` and aborts `implement_final` without a fix turn.
- **Repos without mypy** abort at the per-task `check@quick` with `error`. Set `implement_task = []` and `implement_final = ["test@quick"]`; `implement_task = []` alone isn't enough, because `check@standard` also runs mypy.
- **Test budget.** Check the `test@quick` budget against the suite: mcp-tools-py's default is 300 s, and a timeout is `error`. Raise it with `pytest-timeout` in `[tool.mcp-tools-py]` (overrides every depth; this repo uses 1800).
- **Paths without the project venv.** Windows `implement.bat` activates the tool env until AutoRunner#59. Where project dependencies aren't installed, collection failures become findings and the run fails at the cap, or at once as `general` if `conftest.py` can't import.
- **Missing fix fragments.** A toolkit without a `fix.check` or `fix.test` fragment (missing or empty) no longer just disables that fix loop: its findings fail `implement_final` at once.
- **Undeclared actions or depths.** A toolkit that doesn't declare a requested action or depth (e.g. a command toolkit with no `test.quick`) now aborts: `run_request` returns `error`, and `quick` has no lower depth to fall back to. Override `implement_task` / `implement_final` to match the declared depths.

## Project setup is declared per repo (#1204)

Reference: [Project setup](../configuration/setup.md).

- **One command.** The session launcher, the Linux create-plan, implement, review-plan, review-implementation, fix-ci and fix-conflict templates, and all Windows templates run `mcp-coder setup`. It runs the repo's `[tool.mcp-coder.setup]` steps; without the table a repo with a `pyproject.toml` gets `{ builtin = "python" }` (the previous `mcp-coder install --source local --use-sync`). `mcp-coder install` is unchanged.
- **Windows Jenkins runs setup in the templates (#1426).** Every Windows workflow and the coordinator test run `mcp-coder setup --refresh` instead of AutoRunner's provisioning; a workflow's setup failure moves the issue to its failed label. The changed-files check now applies on Windows too, including an untracked `uv.lock`.
- **Linux Python repos are now provisioned** into `.venv` on every run, and checks run there. Repos whose dev extras lack their check tools now fail.
- **Track or ignore `uv.lock`.** Setup fails on files it changed or created; `uv sync` creates a missing `uv.lock` and rewrites a stale one.
- **`VIRTUAL_ENV` only with a venv.** Sessions and the Linux templates set it only when `<repo>/.venv` has an interpreter, and drop an inherited one otherwise. The Windows templates set it only when `<repo>\.venv\Scripts\python.exe` exists; AutoRunner's `run-mcp-command.bat` wrapper (AutoRunner#59) clears an inherited one. A non-Python repo's `.mcp*.json` must not reference `${VIRTUAL_ENV}`.
- **`MCP_CODER_VENV_DIR` names the tool env** in sessions too (it was `<repo>/.venv`), which changes how `${MCP_CODER_VENV_DIR}` expands in a session's `.mcp.json`.
- **Linux Docker image.** It installs `mcp-coder` at build time; rebuild it before a coordinator with this change dispatches Linux jobs, or `mcp-coder setup` is not found.
