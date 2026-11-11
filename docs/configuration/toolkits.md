# Toolkits

Workflows never name tools: they request `action@depth` (`format`, `check` or
`test`) from the configured toolkit. Two toolkits ship: `mcp-tools-py` (Python,
`PythonToolkit`) and `command` (any stack; runs the project's own commands).

mcp-coder's side of the interface and how to write a toolkit:
[Toolkit interface](../architecture/toolkit-interface.md).

## Configure a toolkit

Add the `[tool.mcp-coder.toolkit]` table with one `toolkit` line, in
`pyproject.toml` or, for repos without one, a root `mcp-coder.toml`.

Python:

```toml
[tool.mcp-coder.toolkit]
toolkit = "mcp-tools-py"
```

Any other stack:

```toml
[tool.mcp-coder.toolkit]
toolkit = "command"
```

`toolkit = "command"` alone is not enough: the [command toolkit](#command-toolkit)
also needs its `[tool.mcp-coder.toolkit.command]` step tables, at least `format`
unless [formatting is off](#formatting-off), or `mcp-coder verify` fails and
actions return `error`. Start from the [npm example](#npm).

- Full configs: [Examples](#examples).
- No table configured: see
  [Until the next breaking release](#until-the-next-breaking-release).
- Check the setup with `mcp-coder verify`.

## [tool.mcp-coder.toolkit]

| Key | Default | Meaning |
|-----|---------|---------|
| `toolkit` | `"mcp-tools-py"` | Entry-point name in the `mcp_coder.toolkits` group: `mcp-tools-py` or `command` |
| `bindings` | see [Bindings](#bindings) | The requests each workflow step makes |
| `params` | — | Per-action tables (`params.<action>`, with optional `<depth>` sub-tables that override them) passed to the toolkit and validated against its schema. With both shipped toolkits any key under `params` is an error, and so is an action the toolkit doesn't declare; empty tables pass |
| `[tool.mcp-coder.toolkit.<toolkit>]` | — | The configured toolkit's own section |

Rules:

- Location: `pyproject.toml`, else a root `mcp-coder.toml`. Both defining the
  table is an error.
- Any other key is an error, including a section for a toolkit that isn't the
  configured one: a leftover `[tool.mcp-coder.toolkit.command]` after switching,
  or a `command` subtable in a table without `toolkit`.
- `format`, `check` and `test` are reserved keys; using one is a config error.

A config error surfaces as follows:

- Workflows that run the format pre-flight at entry stop: implement, rebase,
  fix_ci and review; check-branch-status only in `--fix` mode with failed CI;
  fix_conflict only in its LLM-rebase fallback, which is then refused.
- `mcp-coder verify` shows an error Toolkit row and fails.
- LLM grant resolution and prompt-slot resolution log a warning and fall back:
  no grants, default slots.

## Bindings

`[tool.mcp-coder.toolkit.bindings]` maps each workflow entry to the requests it
makes.

| Entry | Default | Accepts | Used by |
|-------|---------|---------|---------|
| `implement_task` | `check@quick` | `check`, `test` | implement, after each task |
| `implement_final` | `check@standard`, `test@quick` | `check`, `test` | implement, after the last task (gate) |
| `commit` | `format@apply` | `format` (not `format@check`) | formatting before commits: implement, rebase, review, CI fix |
| `rebase` | `check@standard`, `test@standard` | `check`, `test` | `mcp-coder rebase`: baseline and after the rebase |
| `rebase_automated` | `check@standard`, `test@unattended` | `check`, `test` | automated rebases: the review and fix_conflict rebase fallback |

Rules:

- An entry's list replaces its default entirely; `[]` disables the entry.
  Unknown entries are an error. Requests are lowercase `action@depth`.
- `commit` runs only when `[tool.mcp-coder] format_code` is on (the default).
  `format_code` and `[tool.mcp-coder.implement] check_type_hints` are read from
  `pyproject.toml` only; a repo with only `mcp-coder.toml` turns formatting off
  with `commit = []`.
- Depth fallback: an undeclared `quick` / `standard` / `full` runs the nearest
  lower declared one of these three (logged); anything else undeclared is
  `error`.
- Which actions `mcp-coder verify` checks:
  [Until the next breaking release](#until-the-next-breaking-release).

## mcp-tools-py

- Its own settings stay in `[tool.mcp-tools-py]`: `formatter`, `<tool>-timeout`
  (e.g. `pytest-timeout`), `check-timeout`. A
  `[tool.mcp-coder.toolkit.mcp-tools-py]` section is accepted but
  `PythonToolkit` ignores it.
- pytest, pylint, mypy and deptry run in `VIRTUAL_ENV`'s interpreter, else
  mcp-coder's own (`sys.executable`); a `VIRTUAL_ENV` without an interpreter is
  `error`. The other tools run from mcp-tools-py's own environment.

As of mcp-tools-py's `toolkit.py`, `toolkit_checks.py` and
`utils/project_config.py`, which are authoritative:

| Action | Depth | Runs | Default timeout |
|--------|-------|------|-----------------|
| `format` | `apply`, `check` | the configured formatter | — |
| `check` | `quick` | mypy | mypy, pylint 600 s; others 120 s |
| | `standard` | + pylint | |
| | `full` | + vulture, lint-imports, tach, ruff, bandit, deptry | |
| `test` | `quick` | pytest without the registered markers ending in `integration` (`error` if the marker list can't be read; unfiltered if none is registered) | 300 s |
| | `unattended` | pytest without `claude_cli_integration`, `copilot_cli_integration`, `langchain_integration`, `llm_integration`, `jenkins_integration`, `install_integration`; `strict_markers=false` | 1800 s |
| | `standard` | pytest, unfiltered | 1800 s |
| | `full` | pytest with coverage | 1800 s |

No tests collected → `skipped`. Timeout overrides: `<tool>-timeout`, then
`check-timeout`, take precedence over these defaults.

MCP tools: rebase sessions get mcp-tools-py's MCP tools through mcp-coder's
generated allowlist unless `--settings` replaces it. Every other session gets
them only from its Claude settings (by default the target's
`.claude/settings.local.json`).

## Command toolkit

The `command` toolkit runs the project's own commands for the `format`, `check`
and `test` actions, so any stack (npm, Rust, Java, …) gets the same workflow
behaviour as Python. Each step runs its `argv` directly, without a shell, in the
project directory. Its own settings live in `[tool.mcp-coder.toolkit.command]`;
a full config is in the [npm example](#npm).

### Config reference

#### Defaults

Apply to every step; a step can override `parser`, `exit_codes` and `timeout`.

| Key | Default | Meaning |
|-----|---------|---------|
| `llm_permissions` | `"bash"` | `"bash"`: Claude sessions get an exact `Bash(...)` grant per step and can re-run it. `"none"`: no grants; the LLM only sees results in the fix prompt |
| `parser` | `"exit-code"` | `"exit-code"` or `"junit"` |
| `exit_codes` | `{ 0 = "ok", 1 = "findings" }` | Maps exit codes to `ok`, `findings`, `skipped` or `error`. An unmapped code is `error` |
| `timeout` | `600` | Seconds per step, positive integer. A timeout is `error` |
| `<action>.<depth>` | — | Ordered list of steps |

Rules:

- Action keys are only `format`, `check` and `test`; any other top-level key is
  an error. Depth names are free (`quick`, `standard`, `full`, `apply`,
  `unattended`, `mutation`, …).
- An undeclared `quick` / `standard` / `full` request runs the nearest lower
  declared one of these three, `error` if none is lower.
- A `format.apply` step's exit code 1 maps to `findings` by default, which fails
  formatting: implement fails; rebase, review and CI fix carry on. Set
  `exit_codes` for `apply` to match the formatter.

#### Step fields

| Field | Required | Meaning |
|-------|----------|---------|
| `argv` | yes | Non-empty list of strings; no shell. Also the source of the step's grant |
| `name` | no | Label in logs, fix texts and the fallback finding key. Default: `argv` joined by spaces |
| `parser` | no | Overrides the default parser |
| `exit_codes` | no | Replaces the default table — no merge |
| `timeout` | no | Overrides the default timeout |
| `report` | with `junit` | JUnit XML file written by the step, relative to the project and inside it. Required with `parser = "junit"`, not allowed otherwise |

Rules:

- An `argv[0]` containing a path separator (`scripts/lint.py`) is resolved
  against the project directory, not the process's working directory. Otherwise
  it is looked up on `PATH`.
- All steps of a depth run in order. The worst status wins
  (`error` > `findings` > `ok` > `skipped`) and findings are concatenated.

### Parsers

- `exit-code`: a `findings` status gives one finding keyed by the step's label.
  Rebase can then only tell "failed before / after", and logs that regression
  detection is degraded.
- `junit`: the `report` file is deleted before the step runs and read only when
  the exit code maps to `findings`. One finding per failed or errored test case,
  keyed `classname::name`. A missing or unreadable report is `error`; a report
  without failed cases falls back to the `exit-code` finding.

The fix prompt gets, per failing step, the label, any JUnit failure messages and
the last 200 lines of stdout followed by stderr.

### LLM access

- **Grants are exact.** Each step grants `Bash(<argv joined by single spaces>)`.
  Extra arguments, added flags or changed spacing are denied, so the prompt
  tells the LLM to run each command unchanged. With `llm_permissions = "none"`
  there are no grants.
- **Which sessions.** Only Claude sessions that re-run checks get grants:
  implement task and its fix calls, finalisation, CI fix (union of all grants),
  and rebase fix turns (only the active rebase binding's grants at the resolved
  depth). Other sessions keep Bash off. Copilot and Langchain get no grants
  and log a warning once when grants are dropped.
- **Read-only commands.** Once Bash is on, Claude Code auto-approves read-only
  commands (e.g. `ls`, `cat`) without a grant; see
  [Claude Code's docs](https://code.claude.com/docs). Nothing that writes runs
  without one.
- **Project grants merge in.** `Bash(...)` rules in the project's
  `.claude/settings.local.json` are added to the session's grants.
- **Bash timeout.** The LLM's Bash tool has its own timeout; see
  [Claude Code's docs](https://code.claude.com/docs). Steps that run longer
  can't be re-run by the LLM; their results still reach it through the fix
  prompt.

### Errors

- `mcp-coder verify` and the format pre-flight at workflow entry report global
  problems (unknown keys, bad defaults, bad `llm_permissions`) and problems in
  `format` steps, including an `argv[0]` that can't be found.
- `check` and `test` steps are validated at run time: a malformed step makes its
  depth return `error`, naming the problem.
- A global problem fails closed: no grants, and every request returns `error` —
  even when formatting is off and nothing else runs `verify`.
- An argument is shell-safe only if `shlex.quote` leaves it unchanged and it has
  no comma, on every platform. A non-shell-safe argument is a warning, not an
  error: the step runs, but without a grant.

### Windows

- `argv[0]` is resolved with `shutil.which`, so `npm` finds `npm.cmd`.
- `.sh` scripts can't run without a shell; call them through an interpreter
  that is on `PATH`, or use another script type.
- cmd.exe re-parses the arguments of `.cmd` files (such as `npm.cmd`); avoid
  arguments with `&`, `|`, `^`, `%` or quotes.
- Backslash paths (`C:\tools\lint.exe`, `scripts\lint.py`) are never shell-safe,
  so such steps get no grant. Forward-slash paths (`scripts/lint.py`) are fine.

## Examples

### Python

`pyproject.toml`:

```toml
[tool.mcp-coder.toolkit]
toolkit = "mcp-tools-py"

# Optional: relax the implement gate
[tool.mcp-coder.toolkit.bindings]
implement_final = ["check@quick", "test@quick"]

[tool.mcp-tools-py]
formatter = "ruff"
```

### npm

`mcp-coder.toml` in the project root:

```toml
[tool.mcp-coder.toolkit]
toolkit = "command"

[tool.mcp-coder.toolkit.command]
llm_permissions = "bash"
parser = "exit-code"
exit_codes = { 0 = "ok", 1 = "findings" }

[tool.mcp-coder.toolkit.command.format]
apply = [ { argv = ["npm", "run", "format"] } ]
check = [ { argv = ["npm", "run", "format:check"] } ]

[tool.mcp-coder.toolkit.command.check]
quick    = [ { argv = ["npm", "run", "typecheck"] },
             { argv = ["npm", "run", "lint"] } ]
standard = [ { argv = ["npm", "run", "check"] } ]
full     = [ { argv = ["npm", "run", "check"] },
             { argv = ["npm", "run", "arch"] },
             { argv = ["npm", "run", "deadcode"] },
             { argv = ["npm", "run", "audit"] } ]

[tool.mcp-coder.toolkit.command.test]
quick      = [ { argv = ["npm", "test"], parser = "junit", report = "reports/junit.xml" } ]
standard   = [ { argv = ["npm", "run", "test"], parser = "junit", report = "reports/junit.xml" } ]
full       = [ { argv = ["npm", "run", "test:coverage"], parser = "junit", report = "reports/junit.xml" } ]
unattended = [ { argv = ["npm", "run", "test:ci"], parser = "junit", report = "reports/junit.xml" } ]
mutation   = [ { argv = ["npm", "run", "test:mutation"], timeout = 3600 } ]  # extra depth, requested explicitly
```

Claude sessions get grants such as `Bash(npm run lint)`, `Bash(npm run typecheck)`
and `Bash(npm test)`.

The `test.unattended` depth is what automated rebase requests (binding
`rebase_automated`: `check@standard`, `test@unattended`). Declare it with tests
that need no interaction or external services.

#### Formatting off

To skip formatting before commits, and the format check of the pre-flight at
workflow entry, empty the `commit` binding and leave out the `format` table:

```toml
[tool.mcp-coder.toolkit.bindings]
commit = []
```

## Until the next breaking release

| Today | Planned (#1199) |
|---|---|
| No toolkit configured (or a `[tool.mcp-coder.toolkit]` table without `toolkit`) → falls back to `mcp-tools-py` | Error with the snippet to paste and a link to this page |
| mcp-tools-py (and with it black, isort, ruff and the other checkers) installs with mcp-coder | `mcp-coder[python]` extra; clear error when missing |
| `mcp-tools-py` and `mcp-workspace` are always required MCP servers (`MCP_SERVER_NAMES`) | Required servers come from the configured toolkit; non-Python needs only `mcp-workspace` |
| `mcp-coder verify` and the pre-flight check the toolkit for `format` only; broken `check` / `test` setups show at run time | Calls the toolkit's `verify()` and checks every requested depth exists |
| `check_type_hints = false` drops `check@*` from the implement bindings | Retired; bindings are the only switch |
| Stage and session names say "mypy" | Renamed neutrally |

Other pages link here instead of repeating these facts.
