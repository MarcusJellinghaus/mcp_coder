# Project setup

Each repo declares how it is set up in `[tool.mcp-coder.setup]`. One command runs
it, the same way on Windows, macOS and Linux:

```bash
mcp-coder setup --project-dir <dir> [--refresh] [--skip-overrides]
```

Flags and exit codes: [CLI reference](../cli-reference.md#setup-1).

Callers pass only these flags, so setup changes land in mcp-coder alone:

- VSCodeClaude session launcher: `--refresh`, before the session env is built
  ([coordinator and VSCodeClaude](../coordinator-vscodeclaude.md#session-lifecycle)).
- Linux Jenkins templates (implement, fix-ci, fix-conflict,
  review-implementation): right after `git pull`. A failure moves the issue to
  its failed label and stops the run.
- Windows Jenkins: AutoRunner's provisioning (AutoRunner#59).

`mcp-coder install` is unchanged; it also builds tool envs and stays Python-only.

## Location

- `pyproject.toml`, else a root `mcp-coder.toml`. Both defining the table is an
  error.
- The rule applies per table: `[tool.mcp-coder.toolkit]` and
  `[tool.mcp-coder.setup]` may live in different files.

## Schema

```toml
[tool.mcp-coder.setup]
steps = [
  { builtin = "python" },
  { name = "frontend", argv = ["npm", "ci", "--prefix", "frontend"], timeout = 900 },
]
```

| Key | Required | Meaning |
|-----|----------|---------|
| `steps` | yes | Ordered list of step tables. `[]` = nothing to do. The only key of the table |
| `argv` | one of `argv` / `builtin` | Non-empty list of strings, run directly in the project directory; no shell |
| `builtin` | one of `argv` / `builtin` | Name of a built-in step: `python` |
| `name` | no | Label in logs and errors. Default: the built-in name, else `argv` joined by spaces |
| `timeout` | no, `argv` only | Seconds, positive integer, default `1800`. On a `builtin` step it is an error |

Loading is strict: an unknown key, a wrong type, or a step with both or neither
of `argv` and `builtin` is an error naming the file, the step and the key.

Steps run in order; the first failure stops the run and `setup` exits non-zero.

## Default

| Table | `pyproject.toml` | Steps |
|-------|------------------|-------|
| present | any | the table's `steps` |
| absent | yes | `[{ builtin = "python" }]` |
| absent | no | none; logged as nothing to do |

## Built-in `python`

- Today's `mcp-coder install <dir> --source local --local-path <dir> --use-sync`,
  run in-process: a `uv.lock`-honoring install into `<dir>/.venv`.
- Applies the `[tool.mcp-coder.install-from-github]` overrides (skipped with
  `--skip-overrides`), `[tool.mcp-coder.install]` `extras` and
  `post_install_checks`, all read from `pyproject.toml`. `--refresh` is passed on.
- Steps after it run with the project venv's bin directory first on `PATH` and
  `VIRTUAL_ENV` set to `<dir>/.venv`; their `argv[0]` is resolved against that
  `PATH`.
- Run `setup` from the tool env, never from the project's own `.venv`: on
  Windows `uv sync` rewrites the running executable.

## `argv[0]` resolution

Same rules as the command toolkit:
[step fields](toolkits.md#step-fields) and [Windows](toolkits.md#windows). One
config works on every OS: on Windows `./mvnw` finds `mvnw.cmd` and `npm` finds
`npm.cmd`; with no `PATHEXT` match the step is not found.

## Changed files

In a git repository, setup fails when it changed tracked files or created
untracked, non-ignored files, since workflows would commit them. The error names
the files. Files already dirty before setup are not checked. Outside a git
repository the check is skipped with a log line.

- **Python repos must track or ignore `uv.lock`.** `uv sync` creates a missing
  `uv.lock` and rewrites a stale one, which fails setup.
- **Use lockfile-frozen commands**, which fail instead of rewriting the lockfile:
  `npm ci`, `cargo … --locked`, `pnpm install --frozen-lockfile`,
  `yarn install --frozen-lockfile`.

## Environment

- `setup` sets `UV_GIT_SHALLOW=0` for its steps unless the caller already set it,
  so the `install-from-github` overrides resolve. Callers don't need to set it.
- Non-Python repos have no project venv, so `VIRTUAL_ENV` is unset in sessions
  and Jenkins runs. Their `.mcp*.json` must not reference `${VIRTUAL_ENV}`.

## Subdirectories

There is no per-step `cwd`. Point the tool at the subdirectory with its own flag:
`npm ci --prefix frontend`, `./mvnw -f backend/pom.xml …`,
`cargo fetch --locked --manifest-path crates/app/Cargo.toml`.

## Check the config

`mcp-coder verify` shows a `Setup` row in its PROJECT section. It loads the
config strictly and resolves every `argv[0]`; no step runs.

- A config error or an unresolvable `argv[0]` is an error (exit 1).
- An unresolvable `argv[0]` after the `python` built-in is only a warning while
  `<dir>/.venv` has no interpreter: setup hasn't run yet, and the built-in may
  install it.

## Examples

### TypeScript (npm)

`mcp-coder.toml` in the project root:

```toml
[tool.mcp-coder.setup]
steps = [ { name = "deps", argv = ["npm", "ci"] } ]
```

### Java (Maven wrapper)

```toml
[tool.mcp-coder.setup]
steps = [ { name = "deps", argv = ["./mvnw", "-B", "-DskipTests", "test-compile"] } ]
```

### Java (Gradle wrapper)

```toml
[tool.mcp-coder.setup]
steps = [ { name = "deps", argv = ["./gradlew", "--no-daemon", "testClasses"] } ]
```

On Windows these find `mvnw.cmd` and `gradlew.bat`; commit both wrapper scripts.

### Rust

```toml
[tool.mcp-coder.setup]
steps = [ { name = "deps", argv = ["cargo", "fetch", "--locked"] } ]
```

### Python plus frontend

`pyproject.toml`:

```toml
[tool.mcp-coder.setup]
steps = [
  { builtin = "python" },
  { name = "frontend", argv = ["npm", "ci", "--prefix", "frontend"] },
]
```

Toolchains (Node, JDK, Rust) are the machine's or Docker image's job; setup does
not install them.
