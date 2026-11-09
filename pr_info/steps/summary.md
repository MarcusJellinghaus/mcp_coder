# Summary — #1395 verify: three false warnings in the MCP section

## Goal

`mcp-coder verify` shows three MCP warnings on a correctly configured repo. All three are false.
This change removes them and makes LangChain's `${...}` resolution match Claude Code.

| # | Symptom | Root cause | Fix |
|---|---------|------------|-----|
| 1 | `MCP edit smoke test [WARN] edit not verified` | Test file `.mcp_coder_verify.md` is gitignored; mcp-workspace refuses ignored paths | Use `.scratch/mcp_coder_verify.md`; pre-check gitignore with mcp-workspace's own rule |
| 2 | `MCP CONFIG WARNINGS ... ${MCP_CODER_PROJECT_DIR}/src` | `_validate_mcp_config` warns on *every* `${...}` in `env` | Warn only for placeholders that don't resolve via `os.environ` / `env_vars` |
| 3 | `Unknown field 'alwaysLoad'` | LangChain MCP parser doesn't know this Claude Code field | Drop it silently (like `type`) via `_IGNORED_FIELDS` |
| 4 | (latent) LangChain `${VAR:-default}` / Windows casing | `_resolve_env_vars` used a plain merged dict, no default syntax | One shared resolver used by verify and LangChain |

## Architectural / design changes

- **New shared resolver `mcp_coder.utils.env_placeholders`** (infrastructure layer `mcp_coder.utils`).
  - `resolve_placeholders(value, env_vars=None, *, case_insensitive=None) -> tuple[str, list[str]]`.
  - Semantics follow Claude Code:
    - `${VAR}` is replaced by its value.
    - `${VAR:-default}` uses `default` only when `VAR` is unset (an empty value counts as set).
    - An unresolved `${VAR}` stays literal.
    - Single pass: the default text is not expanded.
  - Lookup order: `env_vars` first (it wins), then `os.environ`.
    - `os.environ` is queried directly; it is already case-insensitive on Windows (verified by a probe).
    - On Windows, `env_vars` keys are matched case-insensitively. The `case_insensitive` flag makes this explicit for tests.
  - Returns the names it could not resolve, so verify can print `${FOO} not set`.
  - Both `mcp_coder.cli` and `mcp_coder.llm` already depend on `mcp_coder.utils`, so `tach.toml` and `.importlinter` need no change for this module.
- **LangChain `_mcp_tools.py`**
  - `_resolve_env_vars` and the `merged_env` dict are removed, and `_load_mcp_server_config` calls the shared resolver.
  - New `_IGNORED_FIELDS = {"type", "alwaysLoad"}` is checked before the unknown-field warning, and the special `type` branch goes away.
  - `alwaysLoad` is deliberately *not* added to `_KNOWN_FIELDS`. Known fields are copied into the adapter config and would cause a `TypeError`.
- **Verify placeholder check:** `_validate_mcp_config(mcp_json_path, env_vars=None)` warns only on unresolved placeholders. A non-dict `env` is skipped. Warning text is e.g. `${A}, ${B} not set`.
- **Smoke test:**
  - The test file moves to `.scratch/mcp_coder_verify.md`.
  - A gitignore pre-check runs first, using `is_path_gitignored`. It is re-exported from the existing `mcp_coder.mcp_workspace` shim, so the rule is mcp-workspace's own: project-root `.gitignore` only, no global excludes.
  - Cleanup is surgical: delete only the test file, and remove `.scratch/` only if verify created it and it is empty.
  - `tach.toml` gets `mcp_coder.mcp_workspace` in `mcp_coder.cli`'s `depends_on`.

## Files

### Created
- `src/mcp_coder/utils/env_placeholders.py`
- `tests/utils/test_env_placeholders.py`

### Modified
- `src/mcp_coder/llm/providers/langchain/_mcp_tools.py` — uses the shared resolver; `_IGNORED_FIELDS`
- `tests/llm/providers/langchain/test_langchain_agent.py` — remove `TestResolveEnvVars` (moved to utils tests); add `alwaysLoad` and `${VAR:-default}` cases
- `src/mcp_coder/cli/commands/verify_sections.py` — `_validate_mcp_config(..., env_vars=None)`
- `src/mcp_coder/cli/commands/verify.py` — pass `env_vars` to `_validate_mcp_config`; smoke test in `.scratch/` with gitignore pre-check
- `tests/cli/commands/test_verify_mcp_orchestration.py` — placeholder tests rewritten
- `src/mcp_coder/mcp_workspace.py` — re-export `is_path_gitignored`
- `tests/cli/commands/test_verify_mcp_edit_smoke.py` — new path, cleanup and gitignore tests
- `tach.toml` — `mcp_coder.mcp_workspace` in `mcp_coder.cli` `depends_on`
- `.gitignore` — remove the stale `.mcp_coder_verify.md` line

## Steps (one commit each)

1. Shared resolver `mcp_coder.utils.env_placeholders` + tests
2. LangChain `_load_mcp_server_config` uses the resolver; remove `_resolve_env_vars`
3. LangChain: silently ignore `alwaysLoad` (`_IGNORED_FIELDS`)
4. Verify: warn only on unresolved `env` placeholders
5. Verify: smoke test in `.scratch/` with gitignore pre-check

## Checks after every step

- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"]`
- `mcp__mcp-tools-py__run_mypy_check`
- Steps 1, 2 and 5 also run `mcp__mcp-tools-py__run_lint_imports_check` and `mcp__mcp-tools-py__run_tach_check`.
- Run `mcp__mcp-tools-py__run_format_code` before committing.
