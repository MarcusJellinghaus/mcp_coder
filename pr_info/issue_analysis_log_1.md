# Issue #979 Analysis Log — Run 1

**Issue**: Add --settings flag (originally --claude-settings) to specify .claude/settings.local.json (mirror --mcp-config)
**Started**: 2026-05-19
**Supervisor**: Claude Code

---

## Round 1 — 2026-05-19

**Engineer findings:**
- Verified: all 7 `--mcp-config` subparser lines in `cli/parsers.py` (111, 210, 258, 303, 465, 546, 658).
- Verified: `resolve_mcp_config_path` at `cli/utils.py:160` with documented precedence.
- Verified: `build_cli_command` at `claude_code_cli.py:260`, `ask_claude_code_cli` at `:452`, single production call site in `llm/interface.py:250`.
- Verified: `[mcp]` section exists in `user_config.py:337-340`; `[claude]` would be new.
- Discrepancy: `resolve_mcp_config_path` includes env var `MCP_CODER_MCP_CONFIG` step. Issue silently dropped env var support.
- Discrepancy: `prompt_llm_stream` (`interface.py:280`) + `ask_claude_code_cli_stream` (`claude_code_cli_streaming.py:73`) is a separate plumbing path used by icoder. Issue named only the non-streaming pair.
- Discrepancy: Copilot already reads `.claude/settings.local.json` itself (`copilot_cli.py:230-259, :317`) from `execution_dir`. Same bug class.
- Q: env var support? JSON parseability check? Copilot in scope? `.local.json` vs `.json` precedence ambiguous? Log resolved path?
- Tests: `tests/cli/test_utils.py::TestResolveMcpConfigPath` has ~14 methods to mirror. `build_cli_command` test files use `in cmd` style → forward-compatible with appended `--settings`.
- Docs: `docs/cli-reference.md`, `docs/configuration/config.md`, `docs/repository-setup/claude-code.md` need updates.
- Recommendation: proceed with 3-5 clarifications.

**Triage:**
- Autonomous: env var support (yes, mirror `MCP_CODER_*` pattern); no JSON parseability check (mirror `--mcp-config`); `.local.json` wins over `.json` (no merging); `FileNotFoundError` on missing explicit path; debug-log resolved path; streaming pair in scope; ~14 unit-test parity; docs updates listed.
- Escalate: Copilot in scope (real scope decision).

**User decisions:**
- Q: Copilot in scope? → **B. Defer to follow-up issue.** Keep #979 tight on Claude path.
- Q: Flag name? Discussion of file contents (file holds permissions, MCP server enablement, hooks, env, model, outputStyle, plugins — full Claude Code settings schema, not just permissions). → **`--settings`** (exact parity with Claude's flag).

**Accumulated decisions:**
- Flag renamed: `--claude-settings` → `--settings`.
- Env var: `MCP_CODER_CLAUDE_SETTINGS` (kept "CLAUDE" in env-var name for ops clarity, even though CLI flag dropped it).
- Resolver precedence: CLI flag → env var → `config.toml [claude] default_settings_path` → auto `<project_dir>/.claude/settings.local.json` → auto `<project_dir>/.claude/settings.json` → none.
- Missing explicit path → `FileNotFoundError` mirroring `cli/utils.py:202-208`.
- No JSON parseability validation (let Claude error).
- `.local.json` precedence over `.json`; no merging.
- Resolved path logged at debug level.
- Streaming pair in scope: `prompt_llm_stream`, `ask_claude_code_cli_stream`, `claude_code_cli_streaming.py:build_cli_command_stream` (or equivalent).
- Test parity with `TestResolveMcpConfigPath` (~14 cases).
- Docs updates included.
- Issue framing broadened from "permissions" to "Claude Code settings schema" (the file controls hooks/env/model/MCP enablement too).
- Copilot deferred to a separate follow-up issue (B).

**Issue updated**: yes — major rewrite (rename, broaden framing, add env var, streaming pair, AC additions, copilot note).

**Status**: continuing — Round 2 will verify the updated issue is internally consistent and that `--settings` doesn't collide with any existing CLI flag.

## Round 2 — 2026-05-19

**Engineer findings:**
- Flag-name `--settings`: free (no collision in any subparser in `cli/parsers.py`).
- Env var `MCP_CODER_CLAUDE_SETTINGS`: free (no in-use match in src/ or tests/; no conflict with Claude's own `CLAUDE_*` or langchain's `ANTHROPIC_*`).
- `prompt_llm_stream` at `llm/interface.py:280`: confirmed exact.
- `ask_claude_code_cli_stream` at `claude_code_cli_streaming.py:73`: confirmed exact.
- **Correction**: `build_cli_command` is defined once in `claude_code_cli.py:260` and re-used by the streaming module (`claude_code_cli_streaming.py:19, :106`). Issue text "its `build_cli_command` equivalent" was misleading.
- `[claude]` section is new — `_CONFIG_SCHEMA` in `user_config.py:32-80` has `github`, `jenkins`, `mcp`, `llm`, `coordinator`, `vscodeclaude`, `mlflow` but no `[claude]`. `default_settings_path` lands as a clean first key.
- **Correction**: env var should be declared via `FieldDef(env_var="MCP_CODER_CLAUDE_SETTINGS")` in `_CONFIG_SCHEMA` and read via `get_config_values`, not `os.environ.get` in the resolver. Keeps env-var handling centralized.
- Recommendation: proceed to finalize after applying the two text corrections.

**Triage:**
- Both findings are technical text corrections — autonomous decisions, no user input needed.

**User decisions:** none (no escalations this round).

**Accumulated decisions (delta):**
- Wiring clarification: edit the shared `build_cli_command` in `claude_code_cli.py` once; the streaming module re-uses it automatically. Streaming module needs `settings_file` threaded through `ask_claude_code_cli_stream` only.
- Env var registered via `_CONFIG_SCHEMA` `FieldDef(env_var=...)`; resolver uses `get_config_values`.

**Issue updated**: yes — two targeted bullet corrections in the Wiring section.

**Status**: no new questions, no scope changes → finalize.

---

## Final Status

- **Rounds run:** 2
- **Open questions:** 0
- **User decisions made:** 2 (Copilot deferred to follow-up issue; flag name `--settings`).
- **Autonomous decisions made:** ~10 (env var, streaming pair, precedence rules, error handling, logging, test parity, docs updates, schema wiring, two text corrections).
- **Base branch:** not specified in issue (defaults to `main`).
- **Validation:** requirements clear; wiring sites verified; flag and env-var names confirmed free; no contradictions in final body.
- **Next action:** launch issue-approver agent for #979.
- **Follow-up:** file separate issue for Copilot's parallel cwd-discovery bug (`copilot_cli.py:_read_settings_allow`, `:230-259`, `:317`).

## Post-finalization

- **2026-05-19**: `/issue_update` applied — restructured #979 body to the cleaner skill format (Summary / Implementation Approach / Constraints & Rationale / Decisions table / ACs). No content lost; just consolidated.
- **2026-05-19**: Filed follow-up issue #980 for the Copilot cwd-discovery bug (deferred from #979 round 1). Depends on #979.
