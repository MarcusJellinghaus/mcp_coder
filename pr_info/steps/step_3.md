# Step 3 — `[tool.mcp-coder.prompts]` from either file

See `pr_info/steps/summary.md` (design change 2). Depends on step 2
(`find_mcp_coder_table_lenient`).

## WHERE

- `src/mcp_coder/utils/pyproject_config.py` — `get_prompts_config`, module docstring.
- `tests/utils/test_pyproject_config.py` — new class `TestGetPromptsConfigFiles`.

## WHAT

```python
def get_prompts_config(project_dir: Path) -> PromptsConfig: ...  # signature unchanged
```

`PromptsConfig` is unchanged.

## ALGORITHM

```
found = find_mcp_coder_table_lenient(project_dir, "prompts")
source, prompts = found if found is not None else ("pyproject.toml", {})
if not isinstance(prompts, dict):
    logger.warning("Invalid [tool.mcp-coder.prompts] in %s: expected a table, got %s; using defaults", source, type(prompts).__name__)
    prompts = {}
mode = prompts.get("claude-system-prompt-mode", "append")
if mode not in _VALID_PROMPT_MODES:
    logger.warning("Invalid claude-system-prompt-mode '%s' in %s; expected ...", mode, source)
return PromptsConfig(prompts.get("system-prompt"), prompts.get("project-prompt"), mode)
```

## HOW

- The lenient handling stays inside `get_prompts_config`. Its callers
  (`load_prompts`, `load_system_prompt`, `load_project_prompt`,
  `get_project_prompt_path`) don't change.
- The whole `prompts` table comes from one file. Both files defining it is a
  conflict even when their keys differ, which `find_mcp_coder_table` already
  enforces.
- Module docstring: say that `format_code` and `prompts` are read from
  `pyproject.toml`, else `mcp-coder.toml`, and that `install`,
  `install-from-github` and the legacy `implement` readers are
  `pyproject.toml`-only.

## DATA

`PromptsConfig(system_prompt, project_prompt, claude_system_prompt_mode)`, unchanged.

## Tests (write first)

`TestGetPromptsConfigFiles` in `tests/utils/test_pyproject_config.py`:
- `mcp-coder.toml` only, with
  `[tool.mcp-coder.prompts]\nproject-prompt = "p.md"\nclaude-system-prompt-mode = "replace"\n`
  → values used;
- both files define `[tool.mcp-coder.prompts]` with different keys → all
  defaults, and a `caplog` warning naming both files;
- malformed `mcp-coder.toml` and a valid `pyproject.toml` with prompts → defaults
  and a warning;
- invalid mode in `mcp-coder.toml` → the warning text contains `mcp-coder.toml`;
- `mcp-coder.toml` only, with `[tool.mcp-coder]\nprompts = "x"\n` → all
  defaults (no `AttributeError`), and a `caplog` warning containing
  `mcp-coder.toml`.

The existing `TestMalformedTomlRegression::test_prompts_config_returns_defaults`
and `tests/prompts/test_prompt_loader.py::test_get_prompts_config_warns_on_invalid_mode`
must keep passing.

## Checks

pylint, mypy, pytest (fast set); then `run_format_code`. One commit:
`feat(config): read [tool.mcp-coder.prompts] from mcp-coder.toml`.

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` with
> TDD: add the `TestGetPromptsConfigFiles` tests, then switch
> `get_prompts_config` to `find_mcp_coder_table_lenient`, fall back to defaults
> with a logged warning when `prompts` is not a table, and make its mode
> warning name the source file. Run pylint, mypy and pytest. Commit once.
