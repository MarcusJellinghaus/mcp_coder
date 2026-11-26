# Summary — #1444 verify: FILE ACCESS section; shared render primitives and section formatters

Step 4 of epic MarcusJellinghaus/mcp-workspace#408. Upstream pieces are merged and installed:
`mcp_coder_utils.verify_render` (mcp-coder-utils#84), `mcp_workspace.cli.verify_formatting`,
`github_security_rows`, `_check_reference_projects` (mcp-workspace#409) and `verify_file_access` (#404).

## Goal

`mcp-coder verify` stops keeping local copies of code that now lives upstream and gains a
FILE ACCESS section with the same rows as `mcp-workspace verify`:

```
=== FILE ACCESS ===========================================================
  workspace              [OK]   absent - gitignore only
  mcp-workspace          [OK]   7 rules
  mcp-config             [WARN] path not found
  broken                 [ERR]  rejected: path not found
```

## Architectural / design changes

| Area | Before | After |
|---|---|---|
| Row/section primitives (`STATUS_SYMBOLS`, `Row`, `Line`, `SectionBuilder`, render) | local copies in `cli/commands/verify_formatting.py` + `cli/commands/verify_render.py` | one shim `mcp_coder.utils.verify_render` re-exporting `mcp_coder_utils.verify_render`; `cli/commands/verify_render.py` deleted. One `Row` class everywhere (label width depends on `isinstance(r, Row)`). |
| GIT / GITHUB rows | local `_format_section` branches + git/GitHub label entries | `format_git_section` / `format_github_section` from mcp-workspace (via `mcp_coder.mcp_workspace` shim). Local `_format_section` keeps only the generic loop for Claude, LangChain, MLflow, Jenkins, MCP. |
| GITHUB SECURITY | local YAML scan + API row mapping in `verify_sections.py` (PyYAML) | `github_security_rows(project_dir)` (via `mcp_coder.mcp_workspace_github`) + `format_github_security_section`. PyYAML leaves runtime deps (moves to test extra). |
| `.mcp-file-access` check | one PROJECT row, workspace only | new FILE ACCESS section between PROJECT and GIT: workspace + reference projects from the mcp-workspace server args in the resolved `.mcp.json` |
| Old-mcp-workspace fallback | `FILE_ACCESS_SUPPORTED` + stand-ins behind `try/except ImportError` | deleted; shims use plain top-level imports (a stale sibling package fails with `ImportError`, fix = reinstall) |
| Exit code | PROJECT row fed `project_ok` | `_compute_exit_code(..., file_access_ok=True)`; any FILE ACCESS `[ERR]` → 1; `[WARN] path not found` neutral |
| `.mcp.json` resolution timing | `resolve_mcp_config_path` / `prepare_llm_environment` in the LLM PROVIDER block | moved right after PROJECT (FILE ACCESS needs them); `resolve_claude_settings_path` stays where it is |

### Key design decisions (KISS)

- **One reference helper:** `verify_sections._lookup_reference_projects(project_dir, mcp_json_path, env_vars)`
  loads `.mcp.json`, takes the `--reference-project` values of the `mcp-workspace` server
  (both `--reference-project X` and `--reference-project=X`), resolves `${…}` placeholders,
  calls upstream `_check_reference_projects`, and returns plain tuples:
  `([(name, path), ...], [(label, reason), ...])`. `ReferenceProject` (whose `url` keeps raw
  credentials) never leaves the helper.
- **FILE ACCESS printer lives in `verify.py`** (`_print_file_access_section`), so tests patch
  `mcp_coder.cli.commands.verify.verify_file_access` and `..._lookup_reference_projects`
  like every other orchestration mock.
- Any exception from the lookup (e.g. upstream `ValueError` on a URL mismatch) → one
  `[ERR]` row labelled `reference projects`, no partial reference rows, exit 1.
- Missing/malformed `.mcp.json` or no `mcp-workspace` server → workspace row only.
- `_validate_mcp_config` keeps its `(ok, message, warnings)` return; both it and the lookup
  read the file through one helper `_load_mcp_json`.
- Shims re-export the names, nothing more. Upstream private `_check_reference_projects` keeps
  its name in the shim.
- Tests that were ported upstream are deleted, not kept twice. Test layout constants are
  hardcoded (label width 22, marker slot 6, value column 32).

## Files

### Created
- `src/mcp_coder/utils/verify_render.py` — shim for `mcp_coder_utils.verify_render`
- `tests/utils/test_verify_render_shim.py` — shim re-exports the upstream objects
- `tests/cli/commands/test_verify_file_access_section.py` — FILE ACCESS rows, lookup, wiring

### Deleted
- `src/mcp_coder/cli/commands/verify_render.py`
- `tests/cli/commands/test_verify_format_pad.py`
- `tests/cli/commands/test_verify_sections_security.py`
- `tests/cli/commands/test_verify_github_security_probe.py`

### Modified (source)
- `src/mcp_coder/cli/commands/verify.py`
- `src/mcp_coder/cli/commands/verify_formatting.py`
- `src/mcp_coder/cli/commands/verify_sections.py`
- `src/mcp_coder/cli/commands/verify_exit_code.py`
- `src/mcp_coder/cli/commands/verify_setup.py`, `verify_toolkit_rows.py`, `verify_project_keys.py` (imports)
- `src/mcp_coder/cli/commands/init_file_access.py`
- `src/mcp_coder/mcp_workspace.py`
- `src/mcp_coder/mcp_workspace_github.py`

### Modified (tests)
- `tests/cli/commands/conftest.py`
- `tests/cli/commands/test_verify*.py` (import swaps; listed per step)
- `tests/cli/commands/test_verify_render.py`, `test_verify_format_section_basic.py`,
  `test_verify_github_security_section.py`, `test_verify_label_map.py`,
  `test_verify_project_section.py`, `test_verify_mcp_edit_smoke.py`, `test_verify_exit_codes.py`,
  `test_init_file_access.py`
- `tests/llm/providers/langchain/test_langchain_contract_rows.py`
- `tests/utils/test_no_toolkit_error.py`

### Modified (config / docs)
- `.importlinter` (`mcp_coder_utils_isolation`)
- `pyproject.toml` (`pyyaml` → `test` extra)
- `vulture_whitelist.py`
- `.claude/CLAUDE.md` (Shared Libraries table)
- `docs/architecture/architecture.md` (shims row)
- `docs/cli-reference.md` (init fallback sentence; verify section list)
- `docs/repository-setup/repo.md` (PROJECT row → FILE ACCESS)

## Steps

1. [step_1.md](step_1.md) — shim `mcp_coder.utils.verify_render`; switch all users; delete local primitives
2. [step_2.md](step_2.md) — GIT / GITHUB / GITHUB SECURITY from mcp-workspace; drop PyYAML from runtime deps
3. [step_3.md](step_3.md) — remove the pre-f626cf8 `.mcp-file-access` fallback
4. [step_4.md](step_4.md) — FILE ACCESS section (workspace + reference projects), exit code, docs

Each step is one commit; all checks (pylint, pytest, mypy, ruff, lint-imports, tach, vulture,
deptry) pass at the end of every step.
