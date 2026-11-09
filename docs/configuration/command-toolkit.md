# Command Toolkit

> Will be folded into `toolkits.md` (#1200).

The `command` toolkit runs the project's own commands for the `format`, `check`
and `test` actions, so any stack (npm, Rust, Java, …) gets the same workflow
behaviour as Python. Each step runs its `argv` directly, without a shell, in the
project directory.

Select it in `[tool.mcp-coder.toolkit]` (in `pyproject.toml`, else a root
`mcp-coder.toml`):

```toml
[tool.mcp-coder.toolkit]
toolkit = "command"
```

Its own settings live in `[tool.mcp-coder.toolkit.command]`.

## Config reference

### Defaults

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
  declared one of these three.

### Step fields

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

## Example (npm)

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

### Formatting off

To skip formatting, and its pre-flight, at commit time, empty the `commit`
binding and leave out the `format` table:

```toml
[tool.mcp-coder.toolkit.bindings]
commit = []
```

## LLM access

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
  commands (e.g. `ls`, `cat`) without a grant. Nothing that writes runs without
  one.
- **Project grants merge in.** `Bash(...)` rules in the project's
  `.claude/settings.local.json` are added to the session's grants.
- **Bash timeout.** The LLM's Bash tool has its own timeout (about 2 minutes by
  default, 10 minutes at most). Steps that run longer can't be re-run by the
  LLM; their results still reach it through the fix prompt.

## Errors

- `mcp-coder verify` and the format pre-flight at commit report global problems
  (unknown keys, bad defaults, bad `llm_permissions`) and problems in `format`
  steps, including an `argv[0]` that can't be found.
- `check` and `test` steps are validated at run time: a malformed step makes its
  depth return `error`, naming the problem.
- A global problem fails closed: no grants, and every request returns `error` —
  even when formatting is off and nothing else runs `verify`.
- A non-shell-safe argument (see Windows below) is a warning, not an error: the
  step runs, but without a grant.

## Windows

- `argv[0]` is resolved with `shutil.which`, so `npm` finds `npm.cmd`.
- `.sh` scripts can't run without a shell; call them through an interpreter
  that is on `PATH`, or use another script type.
- cmd.exe re-parses the arguments of `.cmd` files (such as `npm.cmd`); avoid
  arguments with `&`, `|`, `^`, `%` or quotes.
- Backslash paths (`C:\tools\lint.exe`, `scripts\lint.py`) are never shell-safe,
  so such steps get no grant. Forward-slash paths (`scripts/lint.py`) are fine.
