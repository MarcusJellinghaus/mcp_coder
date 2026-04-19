# Copilot CLI Provider — Implementation Summary

**Issue:** #847 — Support Copilot as second CLI LLM interface

## Goal

Add GitHub Copilot CLI (`copilot`) as a third LLM provider alongside `"claude"` and `"langchain"`. The existing `prompt_llm()` / `prompt_llm_stream()` abstraction is extended with a `"copilot"` provider that invokes the Copilot CLI in non-interactive mode.

## Architectural / Design Changes

### 1. Provider constant centralisation

Currently `"claude"` and `"langchain"` are hardcoded in 8+ locations (parsers, utils, interface, resolver). A new `SUPPORTED_PROVIDERS` frozenset in `llm/types.py` becomes the single source of truth. All validation and `choices=` lists reference it.

### 2. Shared executable finder utility

A thin `find_executable(name, install_hint)` wrapper around `shutil.which()` is extracted to `utils/executable_finder.py`. The Claude finder calls it as a first-try step before its custom search paths. Copilot calls it directly — no separate finder module needed since Copilot relies solely on PATH (`shutil.which`).

### 3. New provider package: `llm/providers/copilot/`

Mirrors the Claude provider structure with 4 files:

| File | Responsibility |
|---|---|
| `__init__.py` | Exports `ask_copilot_cli`, `ask_copilot_cli_stream` |
| `copilot_cli.py` | Command builder, JSONL parser, settings.local.json tool converter, `ask_copilot_cli()` |
| `copilot_cli_streaming.py` | `ask_copilot_cli_stream()` → `Iterator[StreamEvent]` |
| `copilot_cli_log_paths.py` | Log paths for `logs/copilot-sessions/` |

### 4. Tool permission mapping

A converter function in `copilot_cli.py` reads `.claude/settings.local.json` `permissions.allow` entries and produces two output buckets for Copilot CLI flags:

- **`--available-tools`** (flat hyphen format): `mcp__workspace__read_file` → `workspace-read_file`
- **`--allow-tool`** (parentheses format): `Bash(git diff:*)` → `shell(git diff:*)`
- **Skipped with warning**: `Skill(...)`, `WebFetch(...)` — no Copilot equivalent

### 5. Interface dispatch

`interface.py` gains a `"copilot"` branch in both `prompt_llm()` and `prompt_llm_stream()`. Key differences from Claude:
- **Input**: `-p "<text>"` as CLI arg (not stdin) — subject to ~8KB Windows limit
- **System prompt**: prepended to `-p` text (no `--system-prompt` flag); skipped on `--resume`
- **Project prompt**: skipped (Copilot reads `CLAUDE.md`/`AGENTS.md` natively)
- **Tool sandboxing**: `--available-tools` whitelist + `--allow-all-tools` (not `--tools ""`)

### 6. JSONL stream mapping

Copilot emits different JSONL types than Claude. The streaming module maps:
- `assistant.message` → `text_delta` / `tool_use_start`
- `tool.execution_complete` → `tool_result`
- `result` → `done` (with `sessionId`, usage)
- `session.info` unknown-tool warnings → `error` StreamEvent + WARNING log
- All other types (ephemeral) → skipped

## Files Created

| File | Purpose |
|---|---|
| `src/mcp_coder/utils/executable_finder.py` | Shared `find_executable()` utility |
| `src/mcp_coder/llm/providers/copilot/__init__.py` | Package exports |
| `src/mcp_coder/llm/providers/copilot/copilot_cli.py` | Core: command builder, JSONL parser, tool converter, `ask_copilot_cli()` |
| `src/mcp_coder/llm/providers/copilot/copilot_cli_streaming.py` | `ask_copilot_cli_stream()` |
| `src/mcp_coder/llm/providers/copilot/copilot_cli_log_paths.py` | Log path generation for `copilot-sessions/` |
| `tests/llm/providers/copilot/__init__.py` | Test package |
| `tests/llm/providers/copilot/conftest.py` | Canned JSONL fixtures |
| `tests/llm/providers/copilot/test_copilot_cli.py` | Unit tests: command builder, JSONL parser, tool converter |
| `tests/llm/providers/copilot/test_copilot_cli_streaming.py` | Unit tests: streaming + event mapping |
| `tests/utils/test_executable_finder.py` | Unit tests: shared executable finder |

## Files Modified

| File | Change |
|---|---|
| `src/mcp_coder/llm/types.py` | Add `SUPPORTED_PROVIDERS` constant |
| `src/mcp_coder/llm/session/resolver.py` | Add `"copilot"` + use `SUPPORTED_PROVIDERS` |
| `src/mcp_coder/cli/parsers.py` | Replace 8× hardcoded `choices` with `SUPPORTED_PROVIDERS` |
| `src/mcp_coder/cli/utils.py` | Replace `_VALID_PROVIDERS` with `SUPPORTED_PROVIDERS` |
| `src/mcp_coder/llm/log_utils.py` | New — extracted shared log utilities (sanitize_branch_identifier, DEFAULT_LOGS_DIR) |
| `src/mcp_coder/llm/logging_utils.py` | Moved from `providers/claude/logging_utils.py` — shared LLM logging |
| `src/mcp_coder/llm/providers/claude/claude_code_cli_log_paths.py` | Update imports to use `llm.log_utils` |
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | Update imports to use `llm.logging_utils` |
| `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` | Update imports to use `llm.logging_utils` |
| `src/mcp_coder/llm/interface.py` | Add `"copilot"` dispatch in `prompt_llm()` and `prompt_llm_stream()` |
| `pyproject.toml` | Add `copilot_cli_integration` marker |
| `tests/llm/test_interface.py` | Update unsupported-provider tests |
| `tests/llm/session/test_resolver.py` | Add `"copilot"` tests |
| `tests/cli/test_parsers.py` | Test `"copilot"` in choices |
| `tests/cli/test_utils.py` | Test `"copilot"` in resolve_llm_method |

## Implementation Steps

1. **`SUPPORTED_PROVIDERS` constant + update consumers** — types.py, resolver.py, parsers.py, utils.py + tests
2. **Shared executable finder** — `utils/executable_finder.py` + refactor Claude finder + tests
3. **Copilot log paths** — `copilot_cli_log_paths.py` + tests
4. **Copilot JSONL parser + tool converter** — `copilot_cli.py` parsing/conversion functions + tests
5. **Copilot command builder + `ask_copilot_cli()`** — command construction, main entry point + tests
6. **Copilot streaming** — `copilot_cli_streaming.py` + tests
7. **Interface integration** — wire copilot into `prompt_llm()` / `prompt_llm_stream()` + tests
