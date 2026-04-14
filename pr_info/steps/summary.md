# Issue #648: Support Standard Prompts (System Prompt + Project Prompt)

## Problem

The langchain LLM provider sends no system prompt — the LLM has zero context about its role, tools, or coding conventions. Claude Code has its own built-in prompt but no mechanism for custom project-level injection.

## Solution

Add system prompt and project prompt support to both LLM providers, configured via `pyproject.toml` with shipped defaults.

## Architectural / Design Changes

### New Module: `src/mcp_coder/prompts/prompt_loader.py`

A pure-function module that:
- Reads `[tool.mcp-coder.prompts]` config from a project's `pyproject.toml`
- Resolves prompt file paths (project-relative, absolute, or package-relative via `importlib.resources`)
- Returns loaded prompt strings
- Falls back to shipped defaults when config is missing or `project_dir` is None

This extends the existing pattern from `utils/pyproject_config.py` (which reads `[tool.mcp-coder.install-from-github]`).

### New Data Files: `src/mcp_coder/prompts/system-prompt.md` and `project-prompt.md`

Shipped default prompt files. Already covered by the existing `prompts/*.md` glob in `pyproject.toml` package-data.

### Interface Layer Change: `llm/interface.py`

`prompt_llm()` and `prompt_llm_stream()` gain a `project_dir: str | None` parameter. When provided:
1. `prompt_loader` loads system + project prompts
2. Resolved prompt strings are passed down to providers

The loading happens **once** in the interface layer — providers receive strings, never call `prompt_loader`.

### Langchain Provider Change: `llm/providers/langchain/__init__.py`

`ask_langchain()` and `ask_langchain_stream()` accept `system_prompt` and `project_prompt` string parameters. They build `SystemMessage` objects and pass them to the internal functions (`_ask_text`, `_ask_text_stream`, `_ask_agent`, `_ask_agent_stream`) which prepend them to the message list.

### Claude Provider Change: `llm/providers/claude/claude_code_cli.py`

`build_cli_command()` gains an `append_system_prompt: str | None` parameter (appended via `--append-system-prompt` flag). A separate `system_prompt: str | None` + `system_prompt_replace: bool` parameter pair handles the `replace` mode (uses `--system-prompt` instead). The interface layer handles prompt concatenation and CLAUDE.md redundancy detection before calling the provider.

### CLI Changes

- `prompt` command: new `--add-system-prompts` flag (opt-in)
- `verify` command: new section showing resolved prompt config
- iCoder `/info`: shows resolved prompt paths
- iCoder always injects prompts (same as `prompt` with the flag)

## Data Flow

```
CLI (prompt.py / icoder.py)
  ├── resolve project_dir
  └── call prompt_llm(project_dir=...) or prompt_llm_stream(project_dir=...)
        │
        ├── prompt_loader.load_prompts(project_dir)
        │     ├── read [tool.mcp-coder.prompts] from pyproject.toml
        │     ├── resolve paths (relative / absolute / package)
        │     └── return (system_prompt, project_prompt, config)
        │
        ├── langchain path:
        │     └── ask_langchain(system_prompt=..., project_prompt=...)
        │           └── prepend SystemMessage objects to message list
        │
        └── claude path:
              ├── detect CLAUDE.md redundancy (skip project_prompt if same file)
              ├── concatenate prompts with section headers
              └── ask_claude_code_cli(append_system_prompt=...)
                    └── build_cli_command(append_system_prompt=...)
```

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_coder/prompts/system-prompt.md` | Shipped default system prompt |
| `src/mcp_coder/prompts/project-prompt.md` | Shipped default project prompt |
| `src/mcp_coder/prompts/prompt_loader.py` | Config reading + path resolution + loading |
| `tests/prompts/__init__.py` | Test package |
| `tests/prompts/test_prompt_loader.py` | Tests for prompt_loader |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/interface.py` | Add `project_dir` param; load + pass prompts |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Accept + prepend system messages |
| `src/mcp_coder/llm/providers/langchain/agent.py` | Accept `system_messages` param in `run_agent`/`run_agent_stream` |
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | `build_cli_command` + `ask_claude_code_cli`: accept prompt params |
| `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` | `ask_claude_code_cli_stream`: accept + pass prompt param |
| `src/mcp_coder/cli/parsers.py` | Add `--add-system-prompts` to prompt parser |
| `src/mcp_coder/cli/commands/prompt.py` | Wire `project_dir` + flag to interface |
| `src/mcp_coder/cli/commands/verify.py` | New prompt config section |
| `src/mcp_coder/icoder/core/commands/info.py` | Show prompt paths |
| `src/mcp_coder/icoder/services/llm_service.py` | Accept + pass `project_dir` |
| `src/mcp_coder/cli/commands/icoder.py` | Pass `project_dir` to RealLLMService |
| `src/mcp_coder/utils/pyproject_config.py` | Add `get_prompts_config()` |
| `tests/llm/test_interface.py` | Update for new param |
| `tests/llm/providers/claude/test_claude_code_cli.py` | Update `build_cli_command` tests |
| `tests/llm/providers/langchain/test_langchain_provider.py` | Update for system messages |
| `tests/cli/commands/test_prompt.py` | Test `--add-system-prompts` |
| `tests/cli/commands/test_verify.py` | Test prompt section |
| `tests/icoder/test_info_command.py` | Test prompt paths in /info |

## Configuration Schema

```toml
[tool.mcp-coder.prompts]
system-prompt = "path/to/custom-system-prompt.md"       # optional
project-prompt = ".claude/CLAUDE.md"                     # optional
claude-system-prompt-mode = "append"                     # "append" (default) or "replace"
```

When absent, shipped defaults from `src/mcp_coder/prompts/` are used.
