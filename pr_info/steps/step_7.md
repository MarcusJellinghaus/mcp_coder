# Step 7 — fix-conflict runs the LLM fallback

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_7.md` only.
> Write/adjust the tests first, then the implementation. Run pylint, pytest (fast
> unit set, `-n auto`), mypy and lint-imports until they pass, run
> `run_format_code`, and make exactly one commit.

## WHERE

- `src/mcp_coder/cli/workflow_parsers.py` (`add_fix_conflict_parser`)
- `src/mcp_coder/cli/commands/fix_conflict.py` (`execute_fix_conflict`)
- `src/mcp_coder/workflows/fix_conflict/core.py`
- `src/mcp_coder/cli/commands/coordinator/command_templates.py`
  (`FIX_CONFLICT_COMMAND_TEMPLATE`, `FIX_CONFLICT_COMMAND_WINDOWS`)
- Tests: `tests/cli/commands/test_fix_conflict.py`, `tests/workflows/fix_conflict/test_core.py`,
  `tests/cli/commands/coordinator/test_command_templates.py`

## WHAT

```python
def run_fix_conflict_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    settings_override: str | None = None,
) -> int
```

## HOW

- Parser: add `add_llm_method_arg`, `add_mcp_config_arg`, `add_settings_arg`
  (as create-pr); fix the docstring ("project-dir only").
- CLI (mirror `execute_rebase`):
  `provider = parse_llm_method_from_args(resolve_llm_method(args.llm_method)[0])`,
  `mcp_config = resolve_mcp_config_path(args.mcp_config, project_dir=args.project_dir)`,
  `settings = resolve_claude_settings_path(args.settings, project_dir=args.project_dir) if args.settings else None`
  — no auto-detection, so `REBASE_LLM_PERMISSIONS` applies unless `--settings` is given.
- Workflow: `outcome = rebase_with_llm_fallback(project_dir, provider, mcp_config, settings_override)`;
  the rest (mergeable poll, verdicts) is unchanged — `.ok` now covers LLM success.
- `_fail`: append `("LLM rebase", outcome.llm_detail)` to `fields`.
- Update module/CLI docstrings ("mechanical rebase" → git-only then LLM rebase).
- Templates, mirroring the other LLM templates:
  - Linux: add `export MCP_TIMEOUT=30000`, `which claude && claude --version`,
    and `--mcp-config .mcp.json` on the `fix-conflict` line.
  - Windows: add `set MCP_TIMEOUT=30000` and `--mcp-config .mcp.json`.

## ALGORITHM

```
outcome = rebase_with_llm_fallback(project_dir, provider, mcp_config, settings_override)
logger.info("Rebase attempt result: %s", outcome.reason)
state = _poll_mergeable_state(project_dir, branch)
...existing verdict logic...
```

## DATA

Exit codes unchanged.

## Tests

- Parser accepts `--llm-method`, `--mcp-config`, `--settings`.
- CLI passes provider / mcp_config / resolved settings; without `--settings` passes
  `None` (no `.claude/settings.local.json` auto-detect even if the file exists).
- Workflow calls the helper with those args; failing outcome with `llm_detail` →
  failure comment contains `LLM rebase` and the detail.
- Both fix-conflict templates contain `--mcp-config .mcp.json` and `MCP_TIMEOUT=30000`;
  Linux contains `which claude && claude --version`.
