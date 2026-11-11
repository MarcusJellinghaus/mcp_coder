# Toolkit interface

What mcp-coder does with a toolkit, and how to write one. Configuring a
toolkit in a repo: [Toolkits](../configuration/toolkits.md).

## Contract

The types and rules (`Toolkit`, `ToolkitInfo`, `ActionRequest`, `ActionResult`,
`Finding`, `VerifyItem`, status rules) live in mcp-coder-utils:

- [Toolkit interface](https://github.com/MarcusJellinghaus/mcp-coder-utils#toolkit-interface) (README)
- [`toolkit.py`](https://github.com/MarcusJellinghaus/mcp-coder-utils/blob/main/src/mcp_coder_utils/toolkit.py)

mcp-coder imports them only through the `mcp_coder.utils.toolkit` shim. This
page covers only how mcp-coder uses the contract.

## What mcp-coder does with a toolkit

### Registry

`utils/toolkit_runner.py`:

- Toolkits are looked up by name in the entry-point group `mcp_coder.toolkits`
  (`ENTRY_POINT_GROUP`).
- `load_toolkit()` builds the toolkit on every call: `toolkit_class(config)`
  with the toolkit's own section, then `describe()`, then validates the
  configured `params` against `params_schema`. Nothing is cached.
- Exceptions from loading the entry point, the constructor, `describe()` or
  `verify()` become config errors (`ValueError`). An exception from `run()`
  becomes an `error` result (`run_request`).
- Bindings and config keys: [Bindings](../configuration/toolkits.md#bindings).

### Depth resolution

`_resolve_depth`, `run_request`:

| Requested depth | Runs |
|---|---|
| Declared by the toolkit | As is |
| Undeclared `quick` / `standard` / `full` | Nearest lower declared one of these three, logged as `<action>: depth <d> not declared, running <r>` |
| Anything else undeclared, or no lower one | Nothing; `error` result |

### Result handling

**Implement fix loop** (`workflows/implement/check_loop.py`):

- All `check` requests of the binding run first; `test` requests run only when
  every check is clean. Any fix turn restarts from the checks.
- `MAX_FIX_TURNS = 3` fix turns, shared by checks and tests per binding run.
- An `error` result aborts the run. `skipped` is logged and ignored.
- Fix prompt (`_build_fix_prompt`), parts joined by a blank line:
  1. the `fix.check` or `fix.test` fragment, used raw;
  2. `Check output:` followed by the `fix_text` of every result with findings
     (empty `fix_text` → `summary`);
  3. the filled `check_instructions` slot, only when the toolkit declares
     `Bash(...)` grants.

  Fragments need no placeholder.
- A missing or empty fix fragment returns `cap` at once, with no fix turn.
  Findings left after the last turn also return `cap`.
- On `cap`, `implement_task` commits and continues (`task_processing.py`);
  `implement_final` fails with `checks_exhausted` (`core.py`).

**Rebase** (`workflows/rebase_checks.py`, `workflows/rebase.py`):

- An `error` result, or a toolkit that fails to load, raises `CheckRunError`.
- Each finding becomes the key `"<action>: <Finding.key>"`. `skipped` adds no
  keys.
- `fix_text` (fallback `summary`) is inlined in the regression-fix prompt.
- A regression is a key present after the rebase but not in the baseline.
- Up to `_MAX_FIX_ATTEMPTS = 2` fix attempts, with a stall guard (stops when
  the regressions are unchanged). Each attempt is followed by the formatters
  and a commit.
- Baseline checks fail to run → exit 2. Post-rebase checks fail to run → reset
  to the pre-rebase commit, exit 1.

**Formatting** (`workflow_steps/commit.py::run_formatters`):

| Situation | Result |
|---|---|
| `format_code` off, or `commit` binding empty | `True`, nothing runs |
| Every request `ok` or `skipped` | `True` |
| Any other status | `False`: implement fails; rebase, review and CI fix carry on |
| Config error | raises `FormatterConfigError` |

### Prompt slots and fragments

`utils/prompt_slots.py`, `workflows/rebase_prompt.py`,
`workflows/rebase_automated.py`, `llm/interface.py`:

- Slots: `[language_context]` and `[check_instructions]`, filled from the
  matching fragments. Neutral defaults when the toolkit has none:
  `DEFAULT_LANGUAGE_CONTEXT` (empty) and `DEFAULT_CHECK_INSTRUCTIONS`.
- A slot whose value is `""` on a line of its own drops that line.
- `check_instructions` is `""` when the toolkit declares `Bash(...)` grants the
  session doesn't get (non-Claude provider, or a session without grants).
- Slots are filled in workflow prompt templates and in the injected system and
  project prompts (`_fill_injected_prompts`).
- `check_instructions.unattended` fills the regression-fix prompt's test-filter
  line, in automated rebases only (`rebase_with_llm_fallback`: the review and
  fix_conflict rebase fallback). It is empty when the provider dropped the Bash
  grants.
- `fix.check` / `fix.test`: implement fix loop only, see
  [Result handling](#result-handling).
- An exception in `prompt_fragments()` yields the defaults; in the fix loop it
  yields `cap` (`get_fragment` returns `""`).
- Custom prompts and their slots:
  [Prompt Configuration](../repository-setup/python.md#prompt-configuration).

### LLM permissions

`utils/toolkit_runner.py::llm_permissions`, `workflows/rebase_permissions.py`,
`cli/utils.py::resolve_claude_settings_path`,
`llm/providers/claude/claude_code_cli.py`:

| Session | Grants |
|---|---|
| Implement task, its fix turns, finalisation, CI fix | Union of all `Bash(...)` grants the toolkit declares |
| Rebase fix turns | The active rebase binding's grants at the resolved depth |
| Everything else | None |

- `Bash(...)` grants go to Claude via `--allowedTools`; the Bash tool is
  enabled only when there are grants.
- Non-Claude providers drop the `Bash(...)` grants, with one warning per
  process.
- A toolkit that fails to load gives no grants (warning logged).
- Rebase sessions get a generated allowlist (`rebase_settings`): fixed
  mcp-workspace tools plus the binding's non-Bash grants;
  `enabledMcpjsonServers` is derived from their `mcp__<server>__` prefixes.
  `--settings` replaces it; the `Bash(...)` grants still apply.
- Other sessions get MCP tools only from their Claude settings (by default the
  target's `.claude/settings.local.json`).

### Verify

`workflow_steps/commit.py::check_formatter_config`,
`cli/commands/verify_sections.py::_toolkit_rows`:

- Two callers: the format pre-flight at workflow entry and `mcp-coder verify`.
  Both call `verify(project_dir, "format")`, and only with `format_code` on and
  a non-empty `commit` binding.
- A `VerifyItem` named `formatter` is hidden from `mcp-coder verify`'s rows and
  exit status, but counts in the pre-flight.
- `hint` is not shown. The pre-flight ignores warnings.
- What `verify` does not cover:
  [Until the next breaking release](../configuration/toolkits.md#until-the-next-breaking-release).

## Writing a toolkit

For toolkits maintained alongside mcp-coder; there is no stable third-party
API yet (#1194).

Checklist:

1. **Entry point** under `mcp_coder.toolkits`; the key is the name users
   configure. See
   [Registration](https://github.com/MarcusJellinghaus/mcp-coder-utils#registration).
2. **Config through the constructor** (`self.config`). Problems surface in
   `verify`, never in the constructor. Keep the constructor, `describe()` and
   `prompt_fragments()` cheap and free of side effects: mcp-coder rebuilds the
   toolkit repeatedly. See
   [Public API](https://github.com/MarcusJellinghaus/mcp-coder-utils#public-api).
3. **`describe()`** with a closed `params_schema`. See
   [Parameters schema](https://github.com/MarcusJellinghaus/mcp-coder-utils#parameters-schema).
4. **`run` never raises.** An undeclared action or depth returns `error`; so
   does a config problem (what `verify` covers today:
   [Until the next breaking release](../configuration/toolkits.md#until-the-next-breaking-release)).
   See [Status rules](https://github.com/MarcusJellinghaus/mcp-coder-utils#status-rules).
5. **`verify(project_dir, action)`**, scoped to the action; an `error` item for
   an undeclared action. Don't name an item `formatter`. See
   [Status rules](https://github.com/MarcusJellinghaus/mcp-coder-utils#status-rules).
6. **Finding keys**: stable, line-insensitive, no action prefix (rebase adds
   it). Without stable keys, return one fallback finding; rebase regression
   detection then degrades to "failed before / after". See
   [`toolkit.py`](https://github.com/MarcusJellinghaus/mcp-coder-utils/blob/main/src/mcp_coder_utils/toolkit.py)
   (`Finding`).
7. **`fix_text`** carries everything the LLM needs, including locations; empty
   falls back to `summary`. See
   [Status rules](https://github.com/MarcusJellinghaus/mcp-coder-utils#status-rules).
8. **`llm_permissions`**: MCP tool names, or exact `Bash(...)` grants. See
   [`toolkit.py`](https://github.com/MarcusJellinghaus/mcp-coder-utils/blob/main/src/mcp_coder_utils/toolkit.py)
   (`ToolkitInfo`).
9. **Fragments**: supply `language_context`, `check_instructions`,
   `check_instructions.unattended`, `fix.check` and `fix.test` as needed. A
   missing `fix.check` / `fix.test` gives `cap` without a fix turn
   (`implement_final` fails, `implement_task` continues). Rebase and CI fix
   never use the `fix.*` fragments; rebase has its own prompt plus `fix_text`.
   See [Prompt fragments](https://github.com/MarcusJellinghaus/mcp-coder-utils#prompt-fragments).

Gotchas:

- The entry point registers only after a reinstall of the package that
  declares it.
- An MCP-based toolkit's server must be in the target's `.mcp.json`, and its
  tools allowed in the Claude settings the session uses (by default the
  target's `.claude/settings.local.json`).
- `MCP_SERVER_NAMES` (`utils/mcp_verification.py`) knows only mcp-tools-py and
  mcp-workspace; see
  [Until the next breaking release](../configuration/toolkits.md#until-the-next-breaking-release).
