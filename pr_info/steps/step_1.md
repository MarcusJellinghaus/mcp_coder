# Step 1: `docs/configuration/toolkits.md` (fold in and delete `command-toolkit.md`)

## LLM prompt

> Read `pr_info/steps/summary.md` (ground rules, files, Done-when) and this file,
> `pr_info/steps/step_1.md`. Implement Step 1 only: create
> `docs/configuration/toolkits.md` as specified below, fold in the content of
> `docs/configuration/command-toolkit.md` with the listed corrections, delete
> the old page, and replace its entry in `docs/README.md`. Check every symbol,
> default and number you write against the source file named next to it; when
> they disagree, write what the code does and add a line to the commit message
> body. Docs only — do not change code. Run the verification below, then
> pylint, pytest and mypy, and produce exactly one commit.

## WHERE

- Create `docs/configuration/toolkits.md`
- Delete `docs/configuration/command-toolkit.md` (`mcp__mcp-workspace__delete_this_file`)
- Edit `docs/README.md`, "Setup & Configuration" list

## WHAT — page outline (headings are the "signatures"; keep them exact where marked)

```
# Toolkits
## Configure a toolkit                      <- exact; anchor #configure-a-toolkit
## [tool.mcp-coder.toolkit]                 <- config reference
## Bindings
## mcp-tools-py
## Command toolkit                          <- exact; anchor #command-toolkit
### Config reference / ### Parsers / ### LLM access / ### Errors / ### Windows
## Examples
### Python / ### npm
## Until the next breaking release          <- transitional section
```

`docs/README.md`: replace the line
`- **[Command Toolkit](configuration/command-toolkit.md)** - ...` with
`- **[Toolkits](configuration/toolkits.md)** - Select and configure the toolkit that formats, checks and tests a repo; bindings; the mcp-tools-py and command toolkits`.

## HOW — content per section, with the source that proves each fact

**Intro (2–3 lines).** Workflows never name tools; they request `action@depth`
(`format` / `check` / `test`) from the configured toolkit. Shipped toolkits:
`mcp-tools-py` (Python, `PythonToolkit`) and `command` (any stack, runs the
project's own commands). (Step 2 adds a link to `toolkit-interface.md` here;
don't add it now.)

**`## Configure a toolkit`.** Shortest path: add the table with one `toolkit`
line, in `pyproject.toml` or (non-Python repos) a root `mcp-coder.toml`. Show
both one-liners (`toolkit = "mcp-tools-py"`, `toolkit = "command"`), link to
`#examples`, `#command-toolkit`, and to the transitional section for what
happens when nothing is configured. Check with `mcp-coder verify`.

**`## [tool.mcp-coder.toolkit]`** (source: `src/mcp_coder/utils/toolkit_runner.py`
`load_toolkit_config`, `_RESERVED_KEYS`, `_PER_ACTION_KEYS`, `_validate_params`, `load_toolkit`):
- Key table: `toolkit` (entry-point name, default `mcp-tools-py`), `bindings`
  (see Bindings), `params` (passed to the toolkit and validated against its
  schema; any key under `params` is an error with both shipped toolkits, and so
  is an action the toolkit doesn't declare; empty tables pass),
  `[tool.mcp-coder.toolkit.<toolkit>]` (the toolkit's own section).
- Location: `pyproject.toml`, else a root `mcp-coder.toml`; both defining the
  table is an error.
- Any other key is an error, including a section for a toolkit that isn't the
  configured one (a leftover `[tool.mcp-coder.toolkit.command]` after
  switching, or a `command` subtable in a table without `toolkit`).
- `format` / `check` / `test` as keys: one line — reserved; a config error. No roadmap.
- How a config error surfaces (verify each against its file):
  - workflows that run the format pre-flight (`check_formatter_config` in
    `workflow_steps/commit.py`) stop: implement (`workflows/implement/core.py`),
    rebase (`workflows/rebase.py`), fix_ci (`workflows/fix_ci/core.py`),
    review (`workflows/review/core.py`); check-branch-status only in `--fix`
    mode with failed CI (`cli/commands/check_branch_status.py`); fix_conflict
    only in its LLM-rebase fallback, which is then refused (`workflows/rebase_automated.py`,
    `workflows/fix_conflict/core.py`);
  - `mcp-coder verify` shows an error Toolkit row and fails (`cli/commands/verify_sections.py::_toolkit_rows`);
  - grant resolution (`llm_permissions`) and prompt-slot resolution
    (`utils/prompt_slots.py::resolve_prompt_slots`) log a warning and fall back
    (no grants, default slots).

**`## Bindings`** (source: `toolkit_runner.py` `DEFAULT_BINDINGS`, `_ALLOWED_ACTIONS`,
`_FORBIDDEN_REQUESTS`, `_REQUEST_RE`, `_resolve_depth`; callers via `search_files`):

| Entry | Default | Accepts | Used by |
|---|---|---|---|
| `implement_task` | `check@quick` | `check`, `test` | implement, after each task |
| `implement_final` | `check@standard`, `test@quick` | `check`, `test` | implement, after the last task (gate) |
| `commit` | `format@apply` | `format` (not `format@check`) | formatting before commits: implement, rebase, review, CI fix |
| `rebase` | `check@standard`, `test@standard` | `check`, `test` | `mcp-coder rebase`: baseline and after the rebase |
| `rebase_automated` | `check@standard`, `test@unattended` | `check`, `test` | automated rebases: the review and fix_conflict rebase fallback |

Rules (bullets):
- an entry's list replaces its default entirely; `[]` disables the entry;
  unknown entries are an error; requests are lowercase `action@depth`;
- `commit` runs only when `[tool.mcp-coder] format_code` is on. `format_code`
  and `[tool.mcp-coder.implement] check_type_hints` are read from
  `pyproject.toml` only (`utils/pyproject_config.py`); a repo with only
  `mcp-coder.toml` turns formatting off with `commit = []`;
- depth fallback: an undeclared `quick` / `standard` / `full` runs the nearest
  lower declared one of these three (logged); anything else undeclared is `error`;
- which actions `mcp-coder verify` checks: link `#until-the-next-breaking-release`
  (don't restate).

**`## mcp-tools-py`** (sources: installed `mcp_tools_py/toolkit.py`,
`mcp_tools_py/toolkit_checks.py`, `mcp_tools_py/utils/project_config.py`,
`mcp_tools_py/utils/environment_info.py`):
- Own settings stay in `[tool.mcp-tools-py]`: `formatter`, `<tool>-timeout`
  (e.g. `pytest-timeout`), `check-timeout`. A `[tool.mcp-coder.toolkit.mcp-tools-py]`
  section is accepted but `PythonToolkit` ignores it.
- pytest, pylint, mypy and deptry run in `VIRTUAL_ENV`'s interpreter, else
  mcp-coder's own (`sys.executable`); a `VIRTUAL_ENV` without an interpreter is
  `error`. The other tools run from mcp-tools-py's own environment
  (`_build_context`, `TOOL_MODULES`).
- Compact depth table, captioned "as of mcp-tools-py's `toolkit.py`,
  `toolkit_checks.py` and `utils/project_config.py`, which are authoritative":

  | Action | Depth | Runs | Default timeout |
  |---|---|---|---|
  | `format` | `apply`, `check` | the configured formatter | — |
  | `check` | `quick` | mypy | mypy, pylint 600 s; others 120 s |
  | | `standard` | + pylint | |
  | | `full` | + vulture, lint-imports, tach, ruff, bandit, deptry | |
  | `test` | `quick` | pytest without registered `*integration` markers (`error` if the marker list can't be read; unfiltered if none is registered) | 300 s |
  | | `unattended` | pytest without the six fixed markers (list them from `UNATTENDED_EXCLUDED_MARKERS`), `strict_markers=false` | 1800 s |
  | | `standard` | pytest, unfiltered | 1800 s |
  | | `full` | pytest with coverage | 1800 s |

  No tests collected → `skipped`. Timeout overrides: `<tool>-timeout`, then
  `check-timeout`, take precedence over these defaults.
- MCP tools: rebase sessions get mcp-tools-py's MCP tools through mcp-coder's
  generated allowlist (`workflows/rebase_permissions.py`) unless `--settings`
  replaces it; every other session gets them only from its Claude settings (by
  default the target's `.claude/settings.local.json`; `cli/utils.py::resolve_claude_settings_path`).

**`## Command toolkit`** (source: `src/mcp_coder/toolkits/command/config.py`,
`toolkit.py`). Carry over `command-toolkit.md` nearly verbatim, headings one
level down, with exactly these corrections:
1. Drop the "> Will be folded into `toolkits.md` (#1200)." line and the
   duplicated "Select it in …" paragraph (Configure a toolkit covers it).
2. Rule "An undeclared `quick` / `standard` / `full` request runs the nearest
   lower declared one of these three" → add ", `error` if none is lower".
3. The format pre-flight runs at workflow entry, not at commit (fix "Formatting
   off" and "Errors" wording).
4. A `format.apply` script's exit code 1 maps to `findings` by default, which
   fails formatting (implement fails; rebase, review and CI fix carry on); set
   `exit_codes` for `apply`.
5. "Non-shell-safe (see Windows below)" → an argument is safe only if
   `shlex.quote` leaves it unchanged and it has no comma, on every platform
   (`config.py::_safe`).
6. Claude Code facts: keep the behaviour, drop the numbers ("about 2 minutes …
   10 minutes at most"), link Claude Code's docs (https://code.claude.com/docs)
   for the Bash timeout and the auto-approval of read-only commands.

Move the npm example out of this section into `## Examples` and link to it.

**`## Examples`.**
- `### Python` (`pyproject.toml`):
  ```toml
  [tool.mcp-coder.toolkit]
  toolkit = "mcp-tools-py"

  # Optional: relax the implement gate
  [tool.mcp-coder.toolkit.bindings]
  implement_final = ["check@quick", "test@quick"]

  [tool.mcp-tools-py]
  formatter = "ruff"
  ```
  No `params`.
- `### npm` (`mcp-coder.toml`): the example from `command-toolkit.md` as is (no
  `sarif`, `junit` with `report`, `test.unattended` declared), plus its
  "grants such as …" and `test.unattended` notes, and the `commit = []`
  "Formatting off" snippet.

**`## Until the next breaking release`** — one line per item, exactly:

| Today | Planned (#1199) |
|---|---|
| No toolkit configured (or a `[tool.mcp-coder.toolkit]` table without `toolkit`) → falls back to `mcp-tools-py` | Error with the snippet to paste and a link to this page |
| mcp-tools-py (and with it black, isort, ruff and the other checkers) installs with mcp-coder | `mcp-coder[python]` extra; clear error when missing |
| `mcp-tools-py` and `mcp-workspace` are always required MCP servers (`MCP_SERVER_NAMES`) | Required servers come from the configured toolkit; non-Python needs only `mcp-workspace` |
| `mcp-coder verify` and the pre-flight check the toolkit for `format` only; broken `check` / `test` setups show at run time | Calls the toolkit's `verify()` and checks every requested depth exists |
| `check_type_hints = false` drops `check@*` from the implement bindings | Retired; bindings are the only switch |
| Stage and session names say "mypy" | Renamed neutrally |

Add one sentence: other pages link here instead of repeating these facts.

## ALGORITHM

```
read command-toolkit.md, toolkit_runner.py, command/config.py, installed mcp_tools_py sources
write toolkits.md section by section, re-reading the cited symbol before writing each fact
apply the six command-toolkit corrections; move the npm example to ## Examples
delete command-toolkit.md; replace its docs/README.md entry
run the verification searches; fix until all pass
```

## DATA — verification (replaces tests)

- `search_files(pattern="command-toolkit\\.md")` → matches only under `pr_info/`.
- `search_files(glob="docs/configuration/toolkits.md", pattern="^## (Configure a toolkit|Command toolkit)$")` → 2 matches.
- `search_files(glob="docs/configuration/toolkits.md", pattern="(?i)proposed|will be|until ")`
  → only the `## Until the next breaking release` heading.
- `search_files(glob="docs/configuration/toolkits.md", pattern="(?i)planned|#1199")`
  → only inside the transitional section.
- `check_file_size` passes.
- pylint, pytest (`-n auto`, fast unit marker filter from CLAUDE.md) and mypy pass.

## Blocked

If `docs/configuration/command-toolkit.md` does not exist at the start of this
step, or `DEFAULT_BINDINGS` is not in `src/mcp_coder/utils/toolkit_runner.py`,
write one line to `pr_info/.blocked.txt` and stop.

## Commit

`docs(toolkit): add toolkits.md configuration reference` — body lists any
plan-vs-code discrepancies.
