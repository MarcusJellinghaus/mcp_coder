# Summary — Issue #944: Set `MCP_TIMEOUT` and `alwaysLoad` across all Claude launch paths

## Goal

When mcp-coder workflows launch Claude CLI in print mode (`-p`), MCP servers can hit the default 5 s startup window and be reported as `failed`. Claude then emits fake `<tool_use>` XML as plain text, the session burns ~$0.15 doing nothing useful, and the issue gets labeled `status-03f:planning-failed`.

This change makes two corrections:

1. **`MCP_TIMEOUT=30000`** is set in **every** place mcp-coder launches Claude (Python choke point + 5 launcher scripts + VSCodeClaude template + coordinator templates).
2. **`alwaysLoad: true`** is added to `mcp-tools-py` and `mcp-workspace` in both `.mcp.json` and `.mcp.macos.json` (effective once Claude CLI ≥ 2.1.121 lands on runners; harmless on older versions).

`MCP_TIMEOUT` is the load-bearing fix. `alwaysLoad` is a forward-looking robustness layer.

## Architectural / Design Changes

| Aspect | Decision |
|---|---|
| **Python single source of truth** | New module `src/mcp_coder/llm/claude_settings.py` exposes `MCP_TIMEOUT_MS = "30000"`. Consumed by `prepare_llm_environment()` in `env.py`. (Positioned for future Claude env knobs but only one constant in this PR — `DISABLE_AUTOUPDATER`'s magic `"1"` stays in `env.py` for now.) |
| **Override semantics** | **Python (`env.py`)**: parent-env override pattern — `os.environ.get("MCP_TIMEOUT", MCP_TIMEOUT_MS)` — matches the existing `DISABLE_AUTOUPDATER` line. Lets advanced users / CI configs override per-shell. **Launcher scripts and templates**: hard-set, matching the existing `DISABLE_AUTOUPDATER=1` hard-sets in those files. |
| **Why redundancy across templates** | Workflow templates technically don't need it (they route through `mcp-coder` → Python), but adding it everywhere matches the existing `DISABLE_AUTOUPDATER` pattern in those same templates. **Test templates do need it** — they call `claude` directly, bypassing mcp-coder. |
| **`alwaysLoad`** | Direct JSON edits to both `.mcp.json` and `.mcp.macos.json` for `mcp-tools-py` and `mcp-workspace` only. No Python constant — it's a static JSON property. `obsidian-dev-wiki` is excluded (lookup-only, lazy load is fine). |
| **Timeout value** | 30000 ms (30 s). Generous margin over the 5 s default; revisit if failures continue. |
| **Out of scope** | Runner / agent host config; Claude CLI version upgrade; sibling-repo propagation. |

## Files to Create

| File | Purpose |
|---|---|
| `src/mcp_coder/llm/claude_settings.py` | Holds `MCP_TIMEOUT_MS` constant. |
| `pr_info/steps/summary.md`, `pr_info/steps/step_*.md` | This planning artifact (already part of `pr_info/`, not shipped). |

## Files to Modify

### Python
| File | Change |
|---|---|
| `src/mcp_coder/llm/env.py` | Import `MCP_TIMEOUT_MS`; add one line setting `env_vars["MCP_TIMEOUT"]` with parent-env override. |
| `tests/llm/test_env.py` | Add two tests mirroring the existing `DISABLE_AUTOUPDATER` pair (default value + parent-env override). |

### Launcher scripts (root)
| File | Change |
|---|---|
| `claude.bat` | `set "MCP_TIMEOUT=30000"` next to existing `set "DISABLE_AUTOUPDATER=1"`. |
| `claude_local.bat` | Same. |
| `icoder_local.bat` | Same. |
| `claude.sh` | `export MCP_TIMEOUT=30000` next to existing `export DISABLE_AUTOUPDATER=1`. |
| `claude_local.sh` | Same. |

### Templates
| File | Change |
|---|---|
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | In `VENV_SECTION_WINDOWS`, add `set "MCP_TIMEOUT=30000"` (this template does **not** currently set `DISABLE_AUTOUPDATER` — only `MCP_TIMEOUT` is added). |
| `src/mcp_coder/cli/commands/coordinator/command_templates.py` | Add `MCP_TIMEOUT=30000` next to each existing `DISABLE_AUTOUPDATER=1` line in all 8 templates: `DEFAULT_TEST_COMMAND`, `CREATE_PLAN_COMMAND_TEMPLATE`, `IMPLEMENT_COMMAND_TEMPLATE`, `CREATE_PR_COMMAND_TEMPLATE`, plus their `_WINDOWS` counterparts. |

### MCP config
| File | Change |
|---|---|
| `.mcp.json` | Add `"alwaysLoad": true` to `mcp-tools-py` and `mcp-workspace`. |
| `.mcp.macos.json` | Same two servers (leave `obsidian-dev-wiki` untouched). |

### Documentation
| File | Change |
|---|---|
| `docs/environments/environments.md` | Add an `MCP_TIMEOUT` row to the Environment Variables Reference table, sibling to `DISABLE_AUTOUPDATER`. |

## Step Map

Each step = one commit. Each step is independent of every other step (Python is the only one with tests).

| # | Title | Touches |
|---|---|---|
| 1 | Python core: `claude_settings.py`, wire into `env.py`, tests | `src/mcp_coder/llm/claude_settings.py` (new), `src/mcp_coder/llm/env.py`, `tests/llm/test_env.py` |
| 2 | Launcher scripts | `claude.bat`, `claude.sh`, `claude_local.bat`, `claude_local.sh`, `icoder_local.bat` |
| 3 | VSCodeClaude template | `src/mcp_coder/workflows/vscodeclaude/templates.py` |
| 4 | Coordinator templates | `src/mcp_coder/cli/commands/coordinator/command_templates.py` |
| 5 | `alwaysLoad` in MCP configs | `.mcp.json`, `.mcp.macos.json` |
| 6 | Docs table row | `docs/environments/environments.md` |

## Acceptance Criteria Mapping

| AC from issue | Step |
|---|---|
| `MCP_TIMEOUT_MS` constant exists; consumed by `prepare_llm_environment()` with parent-env override | 1 |
| Two tests mirroring `DISABLE_AUTOUPDATER` pattern | 1 |
| Hard-set in 5 launcher scripts | 2 |
| Hard-set in `VENV_SECTION_WINDOWS` | 3 |
| Set in every coordinator template | 4 |
| `alwaysLoad: true` in both `.mcp.json` files (excluding `obsidian-dev-wiki`) | 5 |
| Doc table row | 6 |
| Sibling-repo chore items drafted | Out of this PR's scope (issue says drafts only, propagation separate). |

## Quality gates (each step)

After every commit run all three:
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
- `mcp__tools-py__run_mypy_check`

All must pass before moving to the next step. Pre-commit: run `./tools/format_all.sh`.
