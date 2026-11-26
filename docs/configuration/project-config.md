# Project config

`[tool.mcp-coder]` keys are per-repo settings, committed with the repo. They
live in `pyproject.toml` and/or a root `mcp-coder.toml`. Per-user settings
(tokens, Jenkins, LLM provider) are in `config.toml`: see the
[Configuration Guide](config.md).

## Files and lookup

- `format_code`, `prompts`, `toolkit` and `setup` are each looked up on their
  own across both files, `pyproject.toml` first. They may live in different
  files, e.g. `toolkit` in `mcp-coder.toml` and `prompts` in `pyproject.toml`.
- `install` and `install-from-github` are read from `pyproject.toml` only.

## Keys

| Key | Files | Default | Read by |
|-----|-------|---------|---------|
| `format_code` | either | `true` | Formatting before commits, the format pre-flight, `mcp-coder verify`. Details: [Bindings](toolkits.md#bindings) |
| `prompts` | either | Shipped prompts, mode `append` | `mcp-coder prompt --add-system-prompts`, `mcp-coder icoder`, `mcp-coder verify`. See [Prompts](#prompts) |
| `toolkit` | either | None — absent is a config error | `utils/toolkit_runner.py`, `mcp-coder verify`. See [Toolkits](toolkits.md) |
| `setup` | either | The `python` built-in when `pyproject.toml` exists, else no steps | `mcp-coder setup`, `verify`'s Setup row, the vscodeclaude launch. See [Project Setup](setup.md) |
| `install` | `pyproject.toml` | `extras` = `dev`; no `post_install_checks` | `mcp-coder install`, setup's `python` built-in, vscodeclaude's launch policy check |
| `install-from-github` | `pyproject.toml` | No overrides | Same readers as `install` |
| `implement` | — | Retired | `mcp-coder verify`; the format pre-flight logs that `[tool.mcp-coder.implement] format_code` is ignored. See [Retired keys](#retired-keys) |
| `labels-config` | — | Retired; ignored at run time | `mcp-coder verify` only. See [Retired keys](#retired-keys) |

## Key in both files

- `format_code`, `prompts`: a warning, and the default is used. `verify` shows
  it in PROMPTS for `prompts`, in PROJECT for `format_code`.
- `toolkit`, `setup`: a config error.

## Wrong value

- `format_code` not a bool → error.
- `prompts` not a table → warning; the defaults are used.
- `claude-system-prompt-mode` other than `append` / `replace` → warning; it
  behaves as `append`. `verify`'s "Claude mode" row shows the raw value as
  `[OK]`.
- `system-prompt` / `project-prompt` must be strings. A non-string value is not
  validated: loading the prompts fails with a `TypeError`.
- `install` / `install-from-github`:
  - a non-string `extras` or a malformed `post_install_checks` aborts
    `mcp-coder install` up front;
  - a `packages` / `packages-no-deps` value that is not a list of strings
    aborts it only when the overrides are applied (not with `--source pypi` or
    `--skip-overrides`);
  - vscodeclaude logs a warning, only when the setup steps include the
    `python` built-in.

## Missing prompt file

A configured `system-prompt` / `project-prompt` path that doesn't exist → a
warning, and the shipped default is used. `verify` shows it as an error in
PROMPTS and exits 1.

## Malformed file

- `toolkit` and `setup`: a malformed `pyproject.toml` or `mcp-coder.toml` is a
  config error, even when the table lives in the other file.
  - `toolkit`: surfaces as listed under
    [`[tool.mcp-coder.toolkit]`](toolkits.md#toolmcp-codertoolkit).
  - `setup`: `mcp-coder setup` fails, `verify`'s Setup row is an error, and
    vscodeclaude logs a warning at launch.
- `format_code` and `prompts`: the defaults are used. `verify` adds a PROJECT
  warning row labelled with the file: "cannot be parsed; format_code and
  prompts use their defaults".
- `install` / `install-from-github`: `mcp-coder install` aborts on a malformed
  `pyproject.toml`. A malformed `mcp-coder.toml` doesn't affect it, but
  `mcp-coder setup` fails on it first. vscodeclaude logs the setup warning
  ("cannot be read; `mcp-coder setup` will abort"), because the setup config
  fails first.

## Checked by verify

- Unknown keys, with a "did you mean" hint.
- `install` / `install-from-github` in `mcp-coder.toml`: "Python-only;
  ignored".
- At the top level and inside `prompts`, `install` and `install-from-github`,
  these are warnings that don't change the exit code.
- An unknown key inside `toolkit` or `setup` is a config error of that table's
  loader and fails `verify`.
- Warnings about `prompts` (unknown inner keys, the table in both files)
  appear in PROMPTS; all others in PROJECT.

## Retired keys

- `[tool.mcp-coder.implement]` in `pyproject.toml`:
  - `format_code` → an error row;
  - `check_type_hints` → its own row; it fails `verify` when `false` while an
    implement binding still requests `check@*`;
  - any other key → "retired and ignored".
- `[tool.mcp-coder.implement]` in `mcp-coder.toml`: the whole table → one
  warning.
- `labels-config`: ignored at run time in either file. `verify` shows
  "[tool.mcp-coder] labels-config is retired and ignored" as a PROJECT warning
  row labelled with the file, once per file that has it; the exit code is
  unchanged.

## Prompts

The `[tool.mcp-coder.prompts]` section configures system and project prompts that are injected into LLM requests. This is particularly important for the **langchain provider**, which has no built-in system prompt — without this, the LLM has no context about its role, tools, or coding conventions. `mcp-coder verify` reads it too and reports the result in its PROMPTS section.

```toml
[tool.mcp-coder.prompts]
system-prompt = "path/to/custom-system-prompt.md"     # optional
project-prompt = ".claude/CLAUDE.md"                   # optional
claude-system-prompt-mode = "append"                   # "append" (default) or "replace"
```

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `system-prompt` | string | Path to system prompt file (role definition, tool usage, coding practices) | Shipped default (`src/mcp_coder/prompts/system-prompt.md`) |
| `project-prompt` | string | Path to project-specific prompt file (project conventions, architecture notes) | Shipped default (`src/mcp_coder/prompts/project-prompt.md`) |
| `claude-system-prompt-mode` | string | How to inject prompts into Claude Code: `"append"` adds to built-in prompt, `"replace"` overrides it | `"append"` |

**Path resolution:** Paths are resolved relative to the project root directory. Absolute paths are also supported. When the section is absent or a field is omitted, shipped defaults from the `mcp_coder` package are used.

**Toolkit slots:** Custom system and project prompts may contain `[language_context]` and `[check_instructions]`, each on a line of its own. The configured toolkit fills them: an empty fragment removes the line, a missing one gives a neutral default. A file without these placeholders is sent unchanged.

**When prompts are injected:**

| Context | Behavior |
|---------|----------|
| `mcp-coder prompt --add-system-prompts` | Opt-in via flag |
| `mcp-coder icoder` | Always injected |
| `mcp-coder verify` | PROMPTS section; the LLM test injects them |
| Automated workflows (`implement`, `create-plan`) | Not injected (these use their own prompt templates) |

**Provider-specific behavior:**

- **Langchain:** System prompt and project prompt are merged (joined by a blank line) into a single `SystemMessage` prepended to the message list. Works in both text and agent modes.
- **Claude Code (append mode):** Prompts are concatenated with section headers (`## System Prompt` / `## Project Prompt`) and passed via `--append-system-prompt`. Claude Code's built-in prompt is preserved.
- **Claude Code (replace mode):** The concatenated prompt replaces Claude Code's entire built-in system prompt via `--system-prompt`. **Use with caution** — this removes Claude Code's tool instructions and safety rules.

**CLAUDE.md redundancy detection:** When using the Claude Code provider, if `project-prompt` points to a `CLAUDE.md` file (in the project root, `.claude/` directory, or any parent directory), the project prompt is automatically skipped to avoid double injection — Claude Code already reads `CLAUDE.md` natively.

**Verification:** Run `mcp-coder verify` to see which prompts are resolved and which mode is active. The iCoder `/info` command also shows prompt paths.
