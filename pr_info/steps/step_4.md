# Step 4 — Claude provider: `bash_grants` + probe integration test

Read `pr_info/steps/summary.md` first. Spec: issue #1196, Scope 1 and 10
(provider part only; no session uses it yet).

## LLM prompt

> Implement Step 4 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_4.md`: add an optional `bash_grants` parameter from
> `prompt_llm` / `prompt_llm_stream` down to `build_cli_command`, and pin the
> probe in a `claude_cli_integration` test (TDD — unit tests first). Run the
> code-quality checks from CLAUDE.md and make exactly one commit.

## WHERE

- `src/mcp_coder/llm/providers/claude/claude_code_cli.py` — `build_cli_command`, `ask_claude_code_cli`.
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` — `ask_claude_code_cli_stream`.
- `src/mcp_coder/llm/interface.py` — `prompt_llm`, `prompt_llm_stream`.
- Tests: the existing `build_cli_command` / interface test modules under
  `tests/llm/` (find them with `search_files` for `build_cli_command`), and new
  `tests/llm/providers/claude/test_bash_grants_integration.py`.

## WHAT

```python
def build_cli_command(..., settings_file: str | None = None,
                      bash_grants: Sequence[str] | None = None) -> list[str]
def ask_claude_code_cli(..., bash_grants: Sequence[str] | None = None) -> LLMResponseDict
def ask_claude_code_cli_stream(..., bash_grants: Sequence[str] | None = None) -> Iterator[StreamEvent]
def prompt_llm(..., bash_grants: Sequence[str] | None = None) -> LLMResponseDict
def prompt_llm_stream(..., bash_grants: Sequence[str] | None = None) -> Iterator[StreamEvent]
```

## HOW

`build_cli_command`:
```
tools = CLAUDE_BUILTIN_TOOLS + (",Bash" if bash_grants else "")
command.extend(["--tools", tools])
... existing flags unchanged ...
if bash_grants: command.extend(["--allowedTools", *bash_grants])   # last: variadic flag, prompt is on stdin
```
- Without grants (`None` or empty) the command is identical to today.
- `ask_claude_code_cli` forwards to the streaming function; the streaming
  function forwards to `build_cli_command`; `prompt_llm` / `prompt_llm_stream`
  forward on the Claude branch only (Copilot / Langchain branches ignore it).
- Docstrings: "Exact `Bash(...)` grants; enables the Bash tool only when non-empty."

## Integration test (`test_bash_grants_integration.py`, `@pytest.mark.claude_cli_integration`)

```
repo = tmp_path / "repo"; execute_command(["git", "init"], cwd=repo)
mcp = tmp_path / "mcp.json" with {"mcpServers": {}}
cmd = build_cli_command(None, claude_exe, str(mcp), use_stream_json=True,
                        bash_grants=["Bash(git config probe.a 1)", "Bash(git config probe.c 3)"])
prompt: run, each as a separate Bash call, `git config probe.a 1`, `git config probe.b 2`,
        `git config probe.a 1 --file extra.cfg`, `git config probe.c 3`
run with execute_subprocess(cmd, CommandOptions(cwd=str(repo),
         input_data=format_stream_json_input(prompt), env_remove=["CLAUDECODE"],
         timeout_seconds=300))   # both from mcp_coder.utils.subprocess_runner
parse stdout NDJSON; take the "result" line's permission_denials
```
Assertions (no assertion on model text):
- `.git/config` contains `probe.a` and `probe.c` values; no `probe.b`; `repo/extra.cfg` absent.
- `permission_denials` commands include `git config probe.b 2` and
  `git config probe.a 1 --file extra.cfg`.
- Skip (`pytest.skip`) when the Claude executable is not found.
Use `execute_command` options as the existing integration tests do; never
import `subprocess` (`subprocess_isolation` covers tests).

## DATA

`build_cli_command` returns `list[str]`; grants appear once, after `--allowedTools`.

## Unit tests

- No grants / empty list → exactly today's command (`--tools ToolSearch`, no `--allowedTools`).
- Two grants → `--tools ToolSearch,Bash` and `--allowedTools g1 g2` at the end, also
  with `settings_file` and `mcp_config` set.
- `prompt_llm(provider="claude", bash_grants=[...])` forwards to `ask_claude_code_cli` (mock);
  `provider="copilot"` / `"langchain"` do not pass it.
- `prompt_llm_stream` forwards to `ask_claude_code_cli_stream` (mock).
