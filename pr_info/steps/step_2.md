# Step 2: `docs/architecture/toolkit-interface.md` (mcp-coder's side and authoring guide)

## LLM prompt

> Read `pr_info/steps/summary.md` (ground rules, files, Done-when) and this file,
> `pr_info/steps/step_2.md`. Implement Step 2 only: create
> `docs/architecture/toolkit-interface.md` as specified below, add it to
> `docs/README.md`, and link it from the intro of
> `docs/configuration/toolkits.md`. Do not restate the toolkit contract (it lives
> in mcp-coder-utils) or anything `toolkits.md` already owns — link instead.
> Check every symbol, default and number against the source file named next to
> it; when they disagree, write what the code does and add a line to the commit
> message body. Docs only — do not change code. Run the verification below,
> then pylint, pytest and mypy, and produce exactly one commit.

## WHERE

- Create `docs/architecture/toolkit-interface.md`
- Edit `docs/README.md`, "Architecture & Design" list
- Edit `docs/configuration/toolkits.md`, intro (one link)

## WHAT — page outline

```
# Toolkit interface
## Contract
## What mcp-coder does with a toolkit
### Registry
### Depth resolution
### Result handling          (implement fix loop / rebase / formatting)
### Prompt slots and fragments
### LLM permissions
### Verify
## Writing a toolkit          (authoring guide: scope line, 9-item checklist, gotchas)
```

`docs/README.md`, under "Architecture & Design", after Architecture Overview:
`- **[Toolkit Interface](architecture/toolkit-interface.md)** - What mcp-coder does with a toolkit, and how to write one`.

`toolkits.md` intro: add "mcp-coder's side of the interface and how to write a
toolkit: [Toolkit interface](../architecture/toolkit-interface.md)."

## HOW — content per section, with sources

**`## Contract`.** The types and rules (`Toolkit`, `ToolkitInfo`,
`ActionRequest`, `ActionResult`, `Finding`, `VerifyItem`, status rules) live in
mcp-coder-utils. Link
`https://github.com/MarcusJellinghaus/mcp-coder-utils#toolkit-interface` and
`https://github.com/MarcusJellinghaus/mcp-coder-utils/blob/main/src/mcp_coder_utils/toolkit.py`.
mcp-coder imports them only through the `mcp_coder.utils.toolkit` shim. Don't
restate the contract; this page states only how mcp-coder uses it, including
the fragments (no issue-number note).

**`### Registry`** (`utils/toolkit_runner.py` `ENTRY_POINT_GROUP`, `_toolkit_class`,
`load_toolkit`, `run_request`, `verify_toolkit`): entry-point group
`mcp_coder.toolkits`; `toolkit_class(config)` with the toolkit's section; rebuilt
on every `load_toolkit()` call; exceptions from loading, the constructor,
`describe()` or `verify()` become config errors, from `run()` an `error` result.
Bindings and config keys: link `../configuration/toolkits.md#bindings`.

**`### Depth resolution`** (`_resolve_depth`, `run_request`): declared depth runs
as is; undeclared `quick` / `standard` / `full` → nearest lower declared one,
logged as `<action>: depth <d> not declared, running <r>`; otherwise `error`.

**`### Result handling`**:
- Implement fix loop (`workflows/implement/check_loop.py`): checks before tests;
  `MAX_FIX_TURNS = 3` fix turns shared per binding run; `error` aborts. Fix
  prompt (`_build_fix_prompt`) = the `fix.check` / `fix.test` fragment used raw,
  then a `Check output:` heading with `fix_text` (empty → `summary`), then
  `check_instructions` only when the toolkit declares `Bash(...)` grants — so
  fragments need no placeholder. A missing or empty fragment returns `cap` at
  once with no fix turn; `implement_task` then commits and continues,
  `implement_final` aborts (`checks_exhausted`; `workflows/implement/core.py`).
- Rebase (`workflows/rebase_checks.py`, `workflows/rebase.py`): `error` →
  `CheckRunError`; keys prefixed with the action (`"<action>: <Finding.key>"`);
  `fix_text` inlined (fallback `summary`); a regression is a key present after
  the rebase but not in the baseline; `skipped` adds no keys; capped fix
  attempts with a stall guard, each followed by the formatters and a commit; a
  baseline error exits 2, a post-rebase error resets and exits 1 (verify both
  exit codes in `rebase.py`).
- Formatting (`workflow_steps/commit.py::run_formatters`): returns `False` for
  any status other than `ok` / `skipped` (implement fails; rebase, review and CI
  fix carry on), raises `FormatterConfigError` on a config error, returns `True`
  when `format_code` is off or `commit` is empty.

**`### Prompt slots and fragments`** (`utils/prompt_slots.py`,
`workflows/rebase_prompt.py`, `workflows/rebase_automated.py`, `llm/interface.py`):
`[language_context]`, `[check_instructions]`; neutral defaults
(`DEFAULT_LANGUAGE_CONTEXT`, `DEFAULT_CHECK_INSTRUCTIONS`); `""` drops the
line; `check_instructions` is `""` when the toolkit declares `Bash(...)`
grants the session doesn't get; `check_instructions.unattended` fills the
regression prompt's test-filter line in automated rebases only
(`rebase_automated`: the review and fix_conflict fallback), and is empty when
the provider dropped the Bash grants. Slots are filled in workflow templates
and in the injected system and project prompts (`llm/interface.py`). An
exception in `prompt_fragments()` yields the defaults (in the fix loop: `cap`).
Custom prompts: link `../repository-setup/python.md#prompt-configuration`.

**`### LLM permissions`** (`toolkit_runner.py::llm_permissions`,
`workflows/rebase_permissions.py`, `cli/utils.py::resolve_claude_settings_path`,
`llm/providers/claude/claude_code_cli.py`): which sessions get the `Bash(...)`
union, passed via `--allowedTools` (implement task and fix turns, finalisation,
CI fix — confirm by searching the callers of `llm_permissions` / `bash_grants`);
rebase fix turns get the binding's grants at the resolved depth; non-Claude
providers drop Bash grants (warned once). The rebase allowlist takes the
non-Bash grants and derives `enabledMcpjsonServers` from their `mcp__<server>__`
prefixes, unless `--settings` replaces it; other sessions get MCP tools only
from their Claude settings (by default the target's `.claude/settings.local.json`).

**`### Verify`** (`workflow_steps/commit.py::check_formatter_config`,
`cli/commands/verify_sections.py::_toolkit_rows`): callers are the format
pre-flight and `mcp-coder verify`, both `action="format"`, only with
`format_code` on and a non-empty `commit` binding. A `VerifyItem` named
`formatter` is hidden from `mcp-coder verify`'s rows and exit status but counts
in the pre-flight; `hint` is not shown; the pre-flight ignores warnings. What
`verify` does not cover today: link
`../configuration/toolkits.md#until-the-next-breaking-release`.

**`## Writing a toolkit`.** Opening line, exactly in substance: "For toolkits
maintained alongside mcp-coder; there is no stable third-party API yet (#1194)."
Numbered checklist; each item links the contract (README anchor or `toolkit.py`):
1. entry point under `mcp_coder.toolkits` (the key is the name users configure);
2. config through the constructor (`self.config`); problems surface in
   `verify`, never in the constructor; the constructor, `describe()` and
   `prompt_fragments()` are cheap and side-effect free (mcp-coder rebuilds the
   toolkit repeatedly);
3. `describe()` with a closed `params_schema`;
4. `run` never raises; undeclared action or depth → `error`; config problems
   also → `error` (link the transitional section for what `verify` covers);
5. `verify(project_dir, action)`, scoped; `error` item for an undeclared
   action; don't name an item `formatter`;
6. finding keys: stable, line-insensitive, no action prefix (rebase adds it);
   without stable keys, one fallback finding (rebase detection degrades);
7. `fix_text` carries everything the LLM needs, including locations (empty
   falls back to `summary`);
8. `llm_permissions`: MCP tool names, or exact `Bash(...)` grants;
9. fragments: which to supply (`language_context`, `check_instructions`,
   `check_instructions.unattended`, `fix.check`, `fix.test`); a missing
   `fix.check` / `fix.test` gives `cap` without a fix turn (`implement_final`
   fails, `implement_task` continues); rebase and CI fix never use the `fix.*`
   fragments (rebase has its own prompt plus `fix_text`).

Gotchas (bullets): the entry point registers only after a reinstall; an
MCP-based toolkit's server must be in the target's `.mcp.json` and its tools
allowed in the Claude settings the session uses (by default the target's
`.claude/settings.local.json`); `MCP_SERVER_NAMES` (`utils/mcp_verification.py`)
knows only mcp-tools-py and mcp-workspace (link
`../configuration/toolkits.md#until-the-next-breaking-release`).

## ALGORITHM

```
read toolkit_runner.py, prompt_slots.py, check_loop.py, rebase_checks.py, rebase.py,
     rebase_permissions.py, commit.py, verify_sections.py, installed mcp_coder_utils/toolkit.py
write each section, re-reading the cited symbol before each fact
link toolkits.md for bindings/config/transitional facts instead of restating them
add the docs/README.md entry and the toolkits.md intro link
run the verification searches; fix until all pass
```

## DATA — verification (replaces tests)

- `search_files(glob="docs/architecture/toolkit-interface.md", pattern="(?i)proposed|planned|will be|until |#1199")`
  → no match except `#until-the-next-breaking-release` link anchors.
- `search_files(glob="docs/architecture/toolkit-interface.md", pattern="#\\d+")`
  → only `#1194` in the authoring guide's opening line.
- Both mcp-coder-utils URLs present; every relative link resolves to an existing
  file (`list_directory` / `search_files`).
- `search_files(glob="docs/README.md", pattern="toolkits\\.md|toolkit-interface\\.md")` → 2 matches.
- `check_file_size` passes; pylint, pytest (`-n auto`, fast unit marker filter
  from CLAUDE.md) and mypy pass.

## Blocked

If `docs/configuration/toolkits.md` does not exist (Step 1 not done), write one
line to `pr_info/.blocked.txt` and stop.

## Commit

`docs(toolkit): add toolkit-interface.md for mcp-coder's side` — body lists any
plan-vs-code discrepancies.
