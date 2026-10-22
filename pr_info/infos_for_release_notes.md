# Release notes — #1166 enable ruff UP (pyupgrade)

## Fixed

- **LangChain agent mode returned empty replies with the Anthropic backend.**
  Anthropic returns message content as a list of text blocks; the agent's
  final-text extraction only accepted a plain string, so every agent-mode reply
  came back as `""`. Text blocks are now joined, matching the streaming path.

## Developer-facing

- **ruff `UP` (pyupgrade) is now enforced** on `src` and `tests`. New code must use
  the Python 3.11 forms: `X | None` instead of `Optional[X]`, builtin generics
  (`list[str]`), `collections.abc` imports, `datetime.UTC`, `OSError`/`TimeoutError`
  aliases, `StrEnum`. Existing code was converted (≈530 sites, mostly ruff
  autofix). `LivenessRule` and `SessionAction` are now `StrEnum`; values,
  equality and hashing are unchanged.
- **Integration tests repaired.** Several tests not run by GitHub CI had drifted
  from the code (missing `settings` / `settings_file` arguments, old cost key,
  an MLflow config patch that never took effect, Windows timing and temp-dir
  cleanup flakiness). They pass again.

## Known issues

- `test_v1_pending_server_self_heals_via_toolsearch` (claude_cli_integration)
  fails with Claude CLI 2.1.304: the CLI reports a slow-starting MCP server as
  `connected` at init instead of `pending`, so the cold-start scenario the test
  needs no longer occurs.
- `test_mcp_tool_usage` (copilot_cli_integration) depends on the local Copilot
  MCP configuration exposing `workspace-read_file`.
- GitHub CI does not run the `claude_cli`, `copilot_cli`, `llm` or `textual`
  markers, which is how the stale integration tests went unnoticed.
