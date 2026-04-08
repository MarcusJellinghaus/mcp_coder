# Issue #724: Absorb `icoder.bat` Setup Logic into `mcp-coder icoder`

## Goal

Make `mcp-coder icoder` self-sufficient — no wrapper script needed. Delete `icoder.bat`. `icoder_local.bat` stays as-is (dev edition with editable-install check).

## Architecture / Design Changes

### Before
```
icoder.bat (batch script)
  ├── Discovers tool env (PATH scan, VIRTUAL_ENV check)
  ├── Activates project .venv
  ├── Verifies MCP binaries exist
  ├── Prints versions
  ├── Sets MCP_CODER_* env vars
  └── Calls: mcp-coder icoder
```

### After
```
mcp-coder icoder (Python)
  ├── icoder/env_setup.py          # iCoder-specific setup orchestration
  │     ├── Tool env from sys.prefix (no PATH scanning needed)
  │     ├── Project venv from <project_dir>/.venv (fallback: sys.prefix)
  │     ├── Respects pre-set MCP_CODER_* env vars
  │     └── Returns RuntimeInfo dataclass
  ├── utils/mcp_verification.py    # Generic cross-platform MCP binary verification
  │     ├── _get_bin_dir(venv_root) → Scripts (Win) / bin (POSIX)
  │     ├── _exe_name(name) → appends .exe on Windows
  │     └── verify_mcp_servers() → checks existence + captures --version
  └── llm/env.py                   # Adds MCP_CODER_VENV_PATH (latent bug fix)
```

### Key Design Decisions

1. **`sys.prefix` for tool env in `env_setup.py` only** — Python *is* the tool env. No PATH gymnastics. Does NOT change `llm/env.py` precedence (`VIRTUAL_ENV` → `CONDA_PREFIX` → `sys.prefix`).
2. **Respect pre-set env vars** — `icoder_local.bat` may set `MCP_CODER_*` before Python starts. Only compute vars that are missing from `os.environ`. Log at DEBUG if computed differs from pre-set.
3. **`MCP_CODER_VENV_PATH` added to `prepare_llm_environment()`** — Fixes latent bug: `.mcp.json` references it but only `.bat` launchers set it. Now all Python callers get it.
4. **`RuntimeInfo` injected into `AppCore` via constructor** — Prepares for future `/info` command (#741). `session_start` event emitted to `EventLog`.
5. **No stdout banner** — Startup info displayed as first entry in TUI output log (not printed before `app.run()`).
6. **Cross-platform from day one** — `mcp_verification.py` uses `sys.platform` to pick `Scripts`/`bin` and `.exe`/no-suffix.

## Files to Create

| File | Purpose |
|------|---------|
| `src/mcp_coder/utils/mcp_verification.py` | Generic cross-platform MCP server binary verification |
| `src/mcp_coder/icoder/env_setup.py` | iCoder-specific environment setup + `RuntimeInfo` dataclass |
| `tests/utils/test_mcp_verification.py` | Tests for MCP verification utility |
| `tests/icoder/test_env_setup.py` | Tests for iCoder env setup |

## Files to Modify

| File | Change |
|------|--------|
| `src/mcp_coder/llm/env.py` | Add `MCP_CODER_VENV_PATH` to returned dict |
| `tests/llm/test_env.py` | Add tests for `MCP_CODER_VENV_PATH` |
| `src/mcp_coder/icoder/core/app_core.py` | Add optional `runtime_info` constructor param + property |
| `src/mcp_coder/cli/commands/icoder.py` | Call `env_setup`, inject `RuntimeInfo`, emit `session_start` event |
| `src/mcp_coder/icoder/ui/app.py` | Display startup info in `on_mount()` |
| `tests/icoder/conftest.py` | Update `app_core` fixture for new param |
| `tests/icoder/test_app_core.py` | Add test for `runtime_info` |
| `tests/icoder/test_cli_icoder.py` | Update for env_setup integration |

## Files to Delete

| File | Reason |
|------|--------|
| `icoder.bat` | Replaced by Python-native setup |

## Documentation Files to Update

| File | Change |
|------|--------|
| `docs/environments/environments.md` (line 63) | Remove `icoder.bat` from launcher-scripts note |
| `docs/repository-setup/claude-code.md` (line 122) | Remove `icoder.bat` from env-vars launcher list |
| `docs/repository-setup/README.md` (line 78) | Change `icoder.bat / icoder_local.bat` → `icoder_local.bat` |
| `docs/repository-setup/internal.md` (line 16) | Delete the `icoder.bat` table row |
| `icoder_local.bat` (line 5) | Drop "Same two-env discovery as icoder.bat" from comment |
| `repo_architecture_plan/mcp_monorepo_plan.md` (line 114) | Update row to reflect `icoder.bat` retirement |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Add `MCP_CODER_VENV_PATH` to `prepare_llm_environment()` | `feat(llm): add MCP_CODER_VENV_PATH to prepare_llm_environment` |
| 2 | New `utils/mcp_verification.py` — cross-platform MCP binary verification | `feat(utils): add cross-platform MCP server verification` |
| 3 | New `icoder/env_setup.py` — RuntimeInfo + environment setup | `feat(icoder): add env_setup module with RuntimeInfo` |
| 4 | Wire env_setup into `execute_icoder()`, `AppCore`, and TUI | `feat(icoder): integrate env_setup into icoder command` |
| 5 | Delete `icoder.bat` + update all documentation | `chore: retire icoder.bat, update docs` |

## Out of Scope

- `DISABLE_AUTOUPDATER=1` — tracked in #740
- `/info` command — tracked in #741 (this PR stores `RuntimeInfo` + emits `session_start` only)
