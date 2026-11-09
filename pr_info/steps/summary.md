# Summary — Split prompts into a general part and toolkit fragments (#1197)

Part of #1192. Depends on #1195 (toolkit runner, `prompt_fragments()`) and #1196 (`command` toolkit).
Follow-ups: #1389 (fix loop `fix.test`), #1198 (skills).

## Goal

Prompts stop assuming Python. mcp-coder keeps a general prompt text; the configured
toolkit supplies language details through `prompt_fragments()` in two slots:
`[language_context]` and `[check_instructions]`.

## Architectural / design changes

### New module `mcp_coder.utils.prompt_slots`

Lives next to `utils/toolkit_runner.py` because `utils` is the only package that
`llm`, `prompt_manager`, `workflows` and `workflow_steps` may all import
(`.importlinter` makes `llm` and `prompt_manager` independent; `tach.toml` keeps
`workflows` away from `mcp_coder.prompts`).

Two functions, used together at every call site:

```python
slots = resolve_prompt_slots(template, project_dir, provider, bash_grants)
prompt = fill_prompt(template, substitutions, slots)
```

- `resolve_prompt_slots(text, project_dir, provider, bash_grants) -> dict[str, str]`
  - Returns `{}` (no toolkit load) when `text` contains no slot. This keeps
    slot-free user prompts and prompts without slots a true no-op.
  - Reads the **raw** `prompt_fragments()` dict (not `get_fragment()`, which
    can't tell missing from `""`).
  - Fragment non-empty → inserted; `""` → `""` (line removed by `fill_prompt`);
    missing / toolkit load fails / `prompt_fragments()` raises → neutral default.
  - Provider-aware rule: `check_instructions` is `""` when the toolkit declares
    `Bash(...)` grants (`llm_permissions(project_dir, "claude")`) and the session
    gets none (provider isn't Claude, or `bash_grants` empty).
  - Never raises (catches `Exception`, logs a warning, returns defaults).
- `fill_prompt(template, substitutions, slots) -> str`
  - Removes the whole line of each slot whose value is `""`; collapses a double
    blank line created by that removal only.
  - One regex pass over the escaped known keys (substitutions + slots) with a
    replacement **function** (backslash-safe). Unknown `[placeholders]`, `- [ ]`,
    `[x]` stay untouched. One pass, so inserted text is never substituted again.
- Constants: `DEFAULT_LANGUAGE_CONTEXT = ""`,
  `DEFAULT_CHECK_INSTRUCTIONS = "Run the project's quality checks (linters, type checkers, tests) and fix all issues."`

`prompt_manager.get_prompt_with_substitutions` becomes a thin wrapper over
`fill_prompt(get_prompt(...), substitutions, {})`.

### Where slots are filled

| Prompt | Filled by |
|---|---|
| Implementation template, Finalisation, CI Fix, Plan creation (`prompts.md`) | Their workflow callers: `get_prompt` → `resolve_prompt_slots` → `fill_prompt` |
| `system-prompt.md`, `project-prompt.md` | Inject path in `llm/interface.py` (`prompt_llm`, `prompt_llm_stream`), after `load_prompts` — not inside it, so `verify` / icoder `/info` never load the toolkit |

### Implement fix loop

`check_and_fix_mypy` stops using the "Mypy Fix Prompt" (deleted). Prompt =
toolkit's raw `fix.check` + `"Check output:"` paragraph + fix text, plus the filled
`check_instructions` only for toolkits with `Bash(...)` grants. Unusable
`fix.check` → warning + `return False`.

### Rebase allowlist

`REBASE_LLM_PERMISSIONS` (hard-coded `mcp-tools-py` tools) is replaced by a fixed
`mcp-workspace` tool list plus the non-Bash grants of
`llm_permissions(project_dir, "claude", entry)`. `enabledMcpjsonServers` is
derived from the `mcp__<server>__` prefixes. `rebase_settings_file` gains
`project_dir` and `entry`. `[pytest_marker_filter]` is renamed `[test_filter]`.
`run_format_code` is dropped (the only intended behaviour change for Python).

## Files

### Created
- `src/mcp_coder/utils/prompt_slots.py`
- `tests/utils/test_prompt_slots.py`

### Modified — source
- `src/mcp_coder/prompt_manager.py` (`get_prompt_with_substitutions` wrapper)
- `src/mcp_coder/prompts/prompts.md`
- `src/mcp_coder/prompts/system-prompt.md`
- `src/mcp_coder/prompts/project-prompt.md`
- `src/mcp_coder/llm/interface.py`
- `src/mcp_coder/workflow_steps/ci.py` (`_run_ci_fix`)
- `src/mcp_coder/workflows/implement/finalisation.py`
- `src/mcp_coder/workflows/implement/task_processing.py`
- `src/mcp_coder/workflows/create_plan/core.py`
- `src/mcp_coder/workflows/rebase_permissions.py`
- `src/mcp_coder/workflows/rebase_prompt.py`
- `src/mcp_coder/workflows/rebase.py`
- `src/mcp_coder/workflows/rebase_automated.py`
- `src/mcp_coder/cli/commands/rebase.py`

### Modified — tests
- `tests/test_prompt_manager.py`
- `tests/prompts/test_prompt_loader.py`
- `tests/llm/` (interface tests for the inject path)
- `tests/workflow_steps/test_ci.py`, `tests/workflow_steps/test_ci_bash_grants.py`
- `tests/workflows/implement/` (finalisation, task processing, `test_task_processing_mypy.py`, `test_task_processing_branch_name.py`)
- `tests/workflows/create_plan/` (prompt filling)
- `tests/workflows/rebase/test_rebase_permissions.py`, `test_llm_steps.py`, `test_prompt.py`, `test_workflow_regression.py`
- `tests/cli/commands/test_rebase.py`

### Modified — docs
- `docs/repository-setup/claude-code.md`
- `docs/repository-setup/python.md`
- `docs/processes-prompts/processes/05-implementation.md`

## Steps

1. `utils/prompt_slots.py` + `get_prompt_with_substitutions` wrapper.
2. Workflow prompts in `prompts.md` + their four callers + `claude-code.md`.
3. System/project prompts + inject path in `llm/interface.py` + `python.md`.
4. Implement fix loop on `fix.check`; delete Mypy Fix Prompt; `05-implementation.md`.
5. Rebase: `[test_filter]` rename + allowlist from `llm_permissions`.

## Out of scope

`.claude/skills/*`, `prompts/prompt_instructions.md`, session names / stage labels /
mypy log messages (#1389 / #1199), `fix.test` and fix-loop order/cap (#1389).
