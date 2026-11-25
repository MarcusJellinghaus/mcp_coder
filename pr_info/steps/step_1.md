# Step 1 — `project-config.md`, prompts move, `config.md`, index and root README

## LLM prompt

> Read `pr_info/steps/summary.md`, then this file. Implement Step 1 only:
> - create `docs/configuration/project-config.md`;
> - move the prompts description out of `docs/repository-setup/python.md`;
> - update `docs/configuration/config.md`, `docs/README.md`, the root `README.md`
>   and the two prompt links (`docs/cli-reference.md`,
>   `docs/architecture/toolkit-interface.md`).
>
> Docs only — no `src/` or `tests/` change. Describe behaviour as the code on
> this branch implements it, and check every statement against the source files
> named below. Run the checks listed at the end, then make one commit.

## Precondition

Open `src/mcp_coder/cli/commands/verify_project_keys.py`. #1466 must be merged:

- `_SCHEMA` and `_SETTINGS` no longer contain `"labels-config"`;
- `_UNPARSEABLE` reads `cannot be parsed; format_code and prompts use their defaults`;
- `_classify` reports `[tool.mcp-coder] labels-config is retired and ignored`.

If any of these does not hold, write one line to `pr_info/.blocked.txt`
(`#1466 not merged: labels-config still live in verify_project_keys`) and stop.

## WHERE

- Create `docs/configuration/project-config.md`.
- Modify `docs/README.md`, `docs/repository-setup/python.md`,
  `docs/configuration/config.md`, `README.md`, `docs/cli-reference.md`
  (`### prompt` only) and `docs/architecture/toolkit-interface.md` (the prompt
  link only).

Sources to check statements against:

- `src/mcp_coder/config/toml_utils.py`: `find_mcp_coder_table`,
  `find_mcp_coder_table_lenient`, `MCP_CODER_CONFIG_FILES`
- `src/mcp_coder/utils/pyproject_config.py`: `get_format_code`,
  `get_prompts_config`, `get_install_extras`, `get_post_install_checks`,
  `get_github_install_config`
- `src/mcp_coder/utils/setup_config.py`
- `src/mcp_coder/utils/toolkit_runner.py`
- `src/mcp_coder/cli/commands/verify_project_keys.py`
- `src/mcp_coder/cli/commands/verify_sections.py`: `_print_project_section` and
  the PROMPTS section
- the install command / `mcp_coder/install/`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` and
  `validate_target_repo`
- the prompt loader

## WHAT — `docs/configuration/project-config.md`

Outline. Use tables where cases are uniform and bullets where they are not.

```
# Project config
Intro, 2–3 lines:
  - [tool.mcp-coder] keys are per-repo and committed.
  - They live in pyproject.toml and/or a root mcp-coder.toml.
  - User settings: config.md.

## Files and lookup
- format_code, prompts, toolkit and setup are each looked up on their own
  across both files, pyproject.toml first, so they may live in different
  files (find_mcp_coder_table).
- install and install-from-github are read from pyproject.toml only.

## Keys
| Key | Files | Default | Read by |
  - format_code: either file; true; formatting before commits, the format
    pre-flight, verify. Details: toolkits.md#bindings
  - prompts: either file; shipped prompts, mode append; prompt
    --add-system-prompts, icoder, verify. See #prompts
  - toolkit: either file; none (absent = config error); toolkit_runner,
    verify. See toolkits.md
  - setup: either file; the python built-in when pyproject.toml exists, else
    no steps; mcp-coder setup, verify's Setup row, vscodeclaude launch.
    See setup.md
  - install: pyproject.toml; extras dev, no post_install_checks;
    mcp-coder install, setup's python built-in, and vscodeclaude's launch
    policy check (validate_target_repo / _warn_python_policy)
  - install-from-github: pyproject.toml; no overrides; same readers
  - implement: retired; verify, and the format pre-flight
    (check_formatter_config(warn_legacy_key=True) in
    workflow_steps/commit.py logs that [tool.mcp-coder.implement]
    format_code is ignored). See #retired-keys
  - labels-config: retired; ignored at run time; verify only.
    See #retired-keys

## Key in both files
- format_code, prompts: warning, default used (PROMPTS row for prompts,
  PROJECT row for format_code)
- toolkit, setup: config error

## Wrong value   (kept apart from "both files")
- format_code not a bool → error.
- prompts not a table → warning, defaults.
- claude-system-prompt-mode other than append / replace → warning, behaves
  as append. verify's "Claude mode" row shows the raw value as [OK].
- Non-string prompt values are left out.
- install / install-from-github:
  - a non-string extras or a malformed post_install_checks aborts
    mcp-coder install up front;
  - a packages / packages-no-deps value that is not a list of strings
    aborts it only when overrides are applied (not with --source pypi or
    --skip-overrides);
  - vscodeclaude logs a warning only when the setup steps include the
    python built-in.

## Missing prompt file
A configured system-prompt / project-prompt path that doesn't exist →
warning and the shipped default. verify shows it as an error in PROMPTS and
exits 1.

## Malformed file
- toolkit and setup: a malformed pyproject.toml or mcp-coder.toml is a config
  error even when the table lives in the other file.
  - toolkit: link to the config-error list in toolkits.md#toolmcp-codertoolkit.
  - setup: mcp-coder setup fails, verify's Setup row is an error, vscodeclaude
    logs a warning at launch.
- format_code and prompts: defaults, plus a PROJECT key-warning row labelled
  with the file ("cannot be parsed; format_code and prompts use their
  defaults").
- install / install-from-github: mcp-coder install aborts on a malformed
  pyproject.toml. A malformed mcp-coder.toml doesn't affect it, but
  mcp-coder setup fails on it first. vscodeclaude logs the setup warning
  ("cannot be read; `mcp-coder setup` will abort"), because the setup
  config fails first.

## Checked by verify
- Unknown keys, with a "did you mean" hint.
- install / install-from-github in mcp-coder.toml: "Python-only; ignored".
- At the top level and inside prompts, install and install-from-github,
  these are warnings that don't change the exit code.
- An unknown key inside toolkit or setup is a config error of that
  table's loader and fails verify.
- Warnings about prompts (unknown inner keys, the table in both files)
  appear in PROMPTS; all others in PROJECT.

## Retired keys
- implement, in pyproject.toml:
  - format_code → error row;
  - check_type_hints → its own row (fails verify when false while an
    implement binding still requests check@*);
  - other keys → "retired and ignored".
- implement, in mcp-coder.toml: the whole table → one warning.
- labels-config: ignored at run time in either file. verify shows
  "[tool.mcp-coder] labels-config is retired and ignored" as a PROJECT
  key-warning row labelled with the file, once per file that has it; the
  exit code is unchanged.

## Prompts
The text moved verbatim from python.md "### Prompt Configuration" (snippet,
field table, path resolution, toolkit slots, injection table, provider
behaviour, CLAUDE.md redundancy, verification), with two edits:
  - it names verify as a reader;
  - the "When prompts are injected" table gains a row:
    `mcp-coder verify` | PROMPTS section; the LLM test injects them.
The "Other sections" paragraph does NOT move here.
```

Do not use a `--flag` that a command lacks. The moved text names the Claude CLI
flags `--append-system-prompt` and `--system-prompt`; that is fine, because this
page is not `cli-reference.md`.

## WHAT — other edits

- **`docs/README.md`.** Under "Setup & Configuration", after "Project Setup",
  add:
  `**[Project Config](configuration/project-config.md)** - Every [tool.mcp-coder] key: file, default, reader, and what happens on a problem`.
- **`docs/repository-setup/python.md`:**
  - Reword the lead-in: "…read by the Python tools; `[tool.mcp-tools-py] formatter` also by mcp-coder's formatting".
  - Remove only the `[tool.mcp-coder*]` rows of Key Sections. Keep the other
    rows and `### Key Sections`.
  - Replace the "mcp-coder-specific behavior…" sentence with a link to
    `../configuration/project-config.md`.
  - Move the "Other sections" paragraph to the end of Key Sections.
  - Keep the "Formatting requires a declared formatter" paragraph, and link its
    `format_code` mention to `../configuration/project-config.md`.
  - Keep `### Prompt Configuration` with one line: a link to
    `../configuration/project-config.md#prompts`.
- **`docs/cli-reference.md` `### prompt`.** `--add-system-prompts` injects the
  prompts from `[tool.mcp-coder.prompts]` (or the shipped defaults); link
  `configuration/project-config.md#prompts`. Drop "in `pyproject.toml`".
- **`docs/architecture/toolkit-interface.md`.** Point the "Custom prompts and
  their slots" link at `../configuration/project-config.md#prompts`.
- **`docs/configuration/config.md`:**
  - Quick Reference "Check your config" row: `verify` also reports unknown
    `[tool.mcp-coder]` keys; link `project-config.md`.
  - "Configuration Systems":
    - drop "two separate configuration files", e.g. "MCP Coder reads two
      configuration systems:";
    - keep the `config.toml` row;
    - the second row becomes `pyproject.toml` / `mcp-coder.toml` | Per-project
      | — | `[tool.mcp-coder]` keys: link to `project-config.md`.
  - The priority line: environment variables override `config.toml` values
    only. The project config reads no environment variables.
  - Replace "`pyproject.toml` lives in the project root…" with: the project
    config files live in the repo root and are committed.
  - Rename `#### Environment Variable Overrides` (under `### [llm.langchain]`)
    to `#### LLM environment variables`. Leave
    `## Environment Variable Overrides` unchanged.
- **Root `README.md`.** "The full checklist, with every config key, is in…" →
  the checklist is in Repository Setup; every project config key is in
  [Project config](docs/configuration/project-config.md).

## ALGORITHM (anchor safety)

```
for anchor in [python.md#prompt-configuration, config.md env-var headings]:
    search_files(pattern=anchor-name, glob="**/*.md")
    update every inbound link that would now land wrongly
confirm "two separate configuration files" no longer occurs in docs/
confirm python.md#key-sections and #prompt-configuration still exist
```

## DATA

No code data structures. Output: one new Markdown page and the edits above.

## Checks, then commit

- `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "tests/docs"])`
- `run_pylint_check`, `run_mypy_check`. These should be unaffected; run them
  anyway.
- `run_format_code`, then `git_commit` with `paths` listing the files above.
  Message:
  `docs: add project-config reference, move prompts docs, fix config.md (#1453)`.
