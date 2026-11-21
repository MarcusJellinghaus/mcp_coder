# Summary — #1199: Require a configured toolkit; make mcp-tools-py optional (breaking)

## Goal

mcp-coder stops assuming Python. A project must configure
`[tool.mcp-coder.toolkit]`; mcp-tools-py becomes the `python` extra. Required
MCP servers, `verify`'s toolkit rows and the implement check loop all derive
from the configured toolkit and its bindings. Nothing in `src/` hard-codes
Python or imports `mcp_tools_py` afterwards.

The issue text (#1199) is the specification. Where this summary and the issue
disagree, the issue wins; where the issue and the code disagree, the code wins.

## Architectural / design changes

| Area | Before | After |
|---|---|---|
| Toolkit config | No table, or a table without `toolkit` → `DEFAULT_TOOLKIT = "mcp-tools-py"` | Both raise `ValueError` with the two snippets and the `#configure-a-toolkit` link. `ToolkitConfig.source` is `str`. |
| Dependency | `mcp-tools-py` in `dependencies`; wrapper `mcp_coder/mcp_tools_py.py` re-exports `resolve_steps` | `python = ["mcp-tools-py"]` extra, included by `dev`. Wrapper deleted. `PythonToolkit` is reached only via the `mcp_coder.toolkits` entry point. |
| Missing extra | Generic "not registered" error | For `mcp-tools-py`: hint `pip install --upgrade "mcp-coder[python]"`, else reinstall the tool env. |
| Required MCP servers | Constant `MCP_SERVER_NAMES = ["mcp-tools-py", "mcp-workspace"]` | `required_mcp_servers(project_dir)` = `mcp-workspace` + `mcp__<server>__` prefixes of the toolkit's `llm_permissions` (union over all actions). One helper `mcp_servers_of(permissions)` in `utils/toolkit_runner.py`, shared with `rebase_settings`. |
| `claude mcp list` parsing | Filters to the constant; never sees a missing server | Takes the required list; a required server missing from the output gets status `"not listed"` (`ok=False`). The existing `all(s.ok ...)` exit logic makes `verify` fail for provider `claude` with no new code. Callers pass the resolved MCP config path. |
| icoder binary check | Checks every name in the constant | Fixed list: `mcp-workspace` only. |
| icoder display | Banner/event log/`/info` list only binary-checked servers | `RuntimeInfo` stores `required_mcp_servers` and `mcp_config`; banner, `session_start` (new key `required_mcp_servers`) and `/info` show the required list with its `claude mcp list` status. Old logs fall back to `mcp_servers` inside `format_runtime_banner`. |
| `verify` PROJECT section | Formatter row (`resolve_steps`), toolkit `verify(format)` only, hidden `formatter` item, `check_type_hints` row | New module `cli/commands/verify_toolkit_rows.py` owns every toolkit row: Toolkit row, global items, one group per action (items + depth rows), and the `check_type_hints` leftover row. Formatter row and `_uses_mcp_tools_py` deleted. |
| Implement check loop | `check_type_hints` filter; mypy-specific names | Bindings are the only switch. Neutral names: `check_and_fix`, stage "Final checks", session `step_{n}_check_{turn}`. |
| ENVIRONMENT row | Missing mcp-tools-py → `[ERR] not installed` | `[WARN] not installed (optional)`. |
| Launchers / templates | Stop when mcp-tools-py is missing; templates probe the binary | Launchers warn and continue (guarded `--version`). Templates drop the probe; Windows `verify` gets `--project-dir %WORKSPACE%\repo`. |

### `verify` toolkit rows — the rules (step 7)

- Requests = distinct `(action, depth)` pairs across non-empty bindings, each
  with the list of binding entries that request it. `commit` counts only while
  `format_code` is on.
- `verify_toolkit(loaded, project_dir, action)` is called once per requested
  action the toolkit declares. A raise → its own row in the action's group
  (error for `format`, warning for `check`/`test`); that action doesn't count
  for global items.
- Fewer than two actions returned → no global items, no downgrade: every item
  keeps its own severity in its action's group.
- Two or more returned → items equal in `(name, status, message)` across every
  returning action are global: shown once directly under the Toolkit row with
  their own severity. Every other `check`/`test` `error` item is shown as a
  warning; `format` items keep their severity.
- Depth row per request (via `resolve_depth`): action not declared → error;
  depth declared → no row; resolves to a lower standard depth → warning naming
  the depth that runs; otherwise → error. Each row names the requesting
  bindings.

Layout (indent 4 shown; items under an action header are at indent + 4):

```
    Toolkit              [OK]   mcp-tools-py
      environment        [OK]   ...                     <- global items
      format
        formatter        [OK]   ruff
      check
        ruff             [WARN] ...                     <- downgraded
        check@quick      [WARN] not declared; runs standard (requested by implement_task)
```

### Simplifications agreed in the plan review

- One helper `mcp_servers_of` serves both `rebase_settings` and the required
  list (same derivation, `mcp-workspace` first, the rest sorted).
- "Not listed" needs no new exit-code code: `ok=False` flows through the
  existing `claude_mcp_ok` computation, which only runs for provider `claude`.
- One module owns every toolkit row; one patch target
  (`mcp_coder.cli.commands.verify_toolkit_rows.verify_toolkit`) for fixtures.
- The global-item rule is a single `len(returned) >= 2` branch.

## Files created / modified / deleted

### Created
- `src/mcp_coder/cli/commands/verify_toolkit_rows.py`
- `tests/cli/commands/test_verify_toolkit_rows.py` (per-action, global, depth rows)
- `tests/cli/commands/test_verify_check_type_hints.py` (leftover row)
- `tests/cli/commands/test_verify_required_servers.py`
- `tests/icoder/test_required_servers.py`
- `tests/utils/test_no_toolkit_error.py`

### Deleted
- `src/mcp_coder/mcp_tools_py.py`
- `tests/test_mcp_tools_py.py`

### Modified — source
- `src/mcp_coder/utils/toolkit_runner.py` — no-toolkit error, `source: str`, `resolve_depth` public, `mcp_servers_of`, missing-extra hint
- `src/mcp_coder/utils/mcp_verification.py` — `required_mcp_servers`, `parse_claude_mcp_list(required_servers, ...)`, `verify_mcp_servers` mcp-workspace only
- `src/mcp_coder/utils/pyproject_config.py` — remove `ImplementConfig` / `get_implement_config`; add `get_leftover_check_type_hints`
- `src/mcp_coder/workflows/rebase_permissions.py` — use `mcp_servers_of`
- `src/mcp_coder/workflows/implement/{check_loop,core,task_processing,__init__}.py` — rename, retire `check_type_hints`
- `src/mcp_coder/cli/commands/verify.py` — pass config path + required list
- `src/mcp_coder/cli/commands/verify_sections.py` — delegate toolkit rows, delete Formatter row / `_uses_mcp_tools_py` / old `check_type_hints` row, ENVIRONMENT `[WARN]`
- `src/mcp_coder/cli/commands/coordinator/command_templates.py`
- `src/mcp_coder/icoder/env_setup.py`, `icoder/core/commands/info.py`, `icoder/core/event_log.py`, `icoder/ui/runtime_banner.py`
- `src/mcp_coder/llm/env.py` — docstring only

### Modified — config, CI, scripts
- `pyproject.toml` — extras, deptry ignore, markers, remove `[tool.mcp-coder.implement]`
- `.importlinter`, `tach.toml`
- `.github/workflows/upstream-compat-check.yml`
- `claude.bat`, `claude.sh`, `claude_local.bat`, `claude_local.sh`, `icoder_local.bat`
- `tools/reinstall_local.bat`, `tools/reinstall_local.sh`
- `tools/tach_docs.py`, `vulture_whitelist.py`

### Modified — tests (main ones)
- `tests/conftest.py` (`_resolvable_formatter`), `tests/cli/commands/conftest.py`
- `tests/cli/commands/test_verify_project_section.py`, `tests/cli/commands/test_verify.py`
- `tests/utils/test_mcp_verification.py`, `test_toolkit_config.py`, `test_toolkit_runner.py`, `test_pyproject_config.py`, `tests/test_pyproject_config.py`
- `tests/workflows/implement/**`, `tests/workflows/rebase/test_command_toolkit_binding.py`
- icoder tests for banner / event log / info / env_setup

### Modified — docs
- `docs/configuration/toolkits.md`, `docs/architecture/toolkit-interface.md`, `docs/migration/multi-language.md`
- `docs/architecture/architecture.md`, `docs/architecture/enforcement.md`, `docs/architecture/dependencies/dependency_graph.html`, `pydeps_graph.dot`, `pydeps_graph.html`
- `docs/processes-prompts/processes/05-implementation.md`
- `README.md`, `docs/getting-started/installation.md`, `docs/environments/environments.md`, `docs/configuration/config.md`, `docs/configuration/optional-dependencies.md`, `docs/repository-setup/python.md`, the `docs/repository-setup/` launcher pages

## Steps (one commit each)

1. Neutral names for the implement check loop
2. Retire `check_type_hints`; `verify` leftover row (creates `verify_toolkit_rows.py`)
3. `mcp_servers_of` helper; `rebase_settings` uses it
4. Required MCP servers: parsing, `verify`, icoder start-up and `/info`
5. icoder banner and event log show the required servers
6. Coordinator test templates
7. `verify` checks every binding
8. `python` extra; delete the wrapper
9. Messages for a missing mcp-tools-py (registry hint, ENVIRONMENT row)
10. Launchers, reinstall hints, `llm/env.py` docstring
11. No toolkit configured is an error
12. Docs: toolkits, toolkit interface, migration note, transitional-section links
13. Docs: install pages and remaining mentions

Every step ends with `run_format_code`, pylint, mypy, pytest (fast unit set
with `-n auto`), and where imports change, `run_lint_imports_check` and
`run_tach_check`. All must pass before the commit.
