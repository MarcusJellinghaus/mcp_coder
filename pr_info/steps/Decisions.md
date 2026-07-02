# Decisions

## Plan review follow-ups (issue #991) — approved 2026-07-02

Four approved changes from the completed plan review, applied to `step_1.md`:

1. **Test #2 assertion made specific.** `test_langchain_backend_no_warn_when_module_installed_claude_active`
   no longer asserts a global absence of `"[WARN]"` — that is flaky because the redundancy
   note, MCP config warnings, and MCP "health check skipped" rows also emit `[WARN]` on the
   claude-active path. It now asserts `"uses Claude CLI"` present and the specific langchain
   row absent (`"Langchain backend"`, `"configured but"`, `"not a recognized"` all absent).

2. **Existing claude-active test made deterministic.** Since the new helper calls the real
   `_load_langchain_config()` on every claude-active test, `test_claude_fallback_note_when_claude_active`
   must patch `_load_langchain_config` → `{"backend": None}`. Recommended a shared/autouse patch
   covering the other unpatched claude-active tests (`test_output_contains_status_symbols`,
   `test_active_provider_shown_in_output`, exit-code matrix claude cases). Replaced the earlier
   conditional wording with a firm instruction.

3. **Format command aligned to CLAUDE.md.** Replaced `./tools/format_all.sh` with the mandated
   `mcp__mcp-tools-py__run_format_code`.

4. **Fast-test marker list aligned to CLAUDE.md.** Expanded the `run_pytest_check` marker string
   to the canonical fast-test set (added `copilot_cli_integration`, `jenkins_integration`,
   `llm_integration`, `textual_integration`).
