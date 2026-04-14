# Step 4: Claude Provider — Accept and Inject System Prompts via CLI Flags

## References
- Summary: `pr_info/steps/summary.md`
- Depends on: Step 2 (interface passes prompts to Claude provider)

## WHERE

**Modified files:**
- `src/mcp_coder/llm/providers/claude/claude_code_cli.py` — `build_cli_command()` + `ask_claude_code_cli()` gain prompt params
- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py` — `ask_claude_code_cli_stream()` gains prompt param
- `src/mcp_coder/llm/interface.py` — import `is_claude_md` from `prompt_loader` + add prompt concatenation logic
- `tests/llm/providers/claude/test_claude_code_cli.py` — test CLI flag generation
- `tests/llm/providers/claude/test_claude_cli_wrappers.py` — test pass-through

## WHAT

### `build_cli_command()` — new parameters

```python
def build_cli_command(
    session_id: str | None,
    claude_cmd: str,
    mcp_config: str | None = None,
    use_stream_json: bool = True,
    append_system_prompt: str | None = None,     # NEW
    system_prompt_replace: str | None = None,     # NEW
) -> list[str]:
```

- `append_system_prompt`: value for `--append-system-prompt` flag (default/append mode)
- `system_prompt_replace`: value for `--system-prompt` flag (replace mode — mutually exclusive)

### `ask_claude_code_cli()` — new parameter

```python
def ask_claude_code_cli(
    question: str,
    ...,
    append_system_prompt: str | None = None,     # NEW
    system_prompt_replace: str | None = None,     # NEW
) -> LLMResponseDict:
```

### `ask_claude_code_cli_stream()` — same new parameters

```python
def ask_claude_code_cli_stream(
    question: str,
    ...,
    append_system_prompt: str | None = None,     # NEW
    system_prompt_replace: str | None = None,     # NEW
) -> Iterator[StreamEvent]:
```

### `interface.py` — prompt assembly for Claude

Add a private helper:
```python
def _build_claude_system_prompts(
    system_prompt: str | None,
    project_prompt: str | None,
    config: PromptsConfig,
    project_dir: str | None,
) -> tuple[str | None, str | None]:
    """Build append_system_prompt / system_prompt_replace for Claude CLI.
    Returns (append_system_prompt, system_prompt_replace)."""
```

## HOW

### `build_cli_command()` flag injection

```python
# After existing MCP config flags:
if append_system_prompt and system_prompt_replace:
    raise ValueError("Cannot specify both append_system_prompt and system_prompt_replace")
if append_system_prompt:
    command.extend(["--append-system-prompt", append_system_prompt])
if system_prompt_replace:
    command.extend(["--system-prompt", system_prompt_replace])
```

`build_cli_command()` must raise `ValueError` if both `append_system_prompt` and `system_prompt_replace` are provided — they are mutually exclusive.

### CLAUDE.md redundancy detection (in `interface.py`)

Note: `_is_claude_md` is defined in `prompt_loader.py` as the public function `is_claude_md` (see Step 1). Import it from there:

```python
from mcp_coder.prompts.prompt_loader import is_claude_md
```

```python
def is_claude_md(project_prompt_path: Path | None, project_dir: str | None) -> bool:
    """Check if project_prompt points to any known CLAUDE.md location.
    Checks root-level, .claude/ dir, and parent directories up to filesystem root."""
    if project_prompt_path is None or project_dir is None:
        return False
    try:
        resolved = project_prompt_path.resolve()
    except OSError:
        return False
    root = Path(project_dir).resolve()
    # Known locations within the project
    candidates = [
        root / "CLAUDE.md",
        root / ".claude" / "CLAUDE.md",
    ]
    # Walk parent directories up to filesystem root
    current = root.parent
    while current != current.parent:
        candidates.append(current / "CLAUDE.md")
        candidates.append(current / ".claude" / "CLAUDE.md")
        current = current.parent
    # Check filesystem root itself
    candidates.append(current / "CLAUDE.md")
    candidates.append(current / ".claude" / "CLAUDE.md")
    return any(_safe_resolve(c) == resolved for c in candidates)

def _safe_resolve(p: Path) -> Path | None:
    try:
        return p.resolve()
    except OSError:
        return None
```

### Prompt concatenation for Claude

When mode is "append" (default):
- Concatenate system + project prompt with section headers
- Skip project prompt if it's CLAUDE.md (redundancy)
- Pass as `append_system_prompt`

When mode is "replace":
- Same concatenation but pass as `system_prompt_replace`

```python
def _build_claude_system_prompts(system_prompt, project_prompt, config, project_dir):
    parts = []
    if system_prompt:
        parts.append(f"## System Prompt\n\n{system_prompt}")
    if project_prompt:
        # Skip if pointing at CLAUDE.md (Claude reads it natively)
        prompt_path = get_project_prompt_path(Path(project_dir) if project_dir else None)
        if not is_claude_md(prompt_path, project_dir):
            parts.append(f"## Project Prompt\n\n{project_prompt}")
    combined = "\n\n".join(parts) if parts else None
    if config.claude_system_prompt_mode == "replace":
        return (None, combined)
    return (combined, None)
```

## ALGORITHM

```python
# build_cli_command() addition:
if append_system_prompt:
    command.extend(["--append-system-prompt", append_system_prompt])
if system_prompt_replace:
    command.extend(["--system-prompt", system_prompt_replace])

# ask_claude_code_cli() passes params through:
command = build_cli_command(session_id, claude_cmd, mcp_config,
                           append_system_prompt=append_system_prompt,
                           system_prompt_replace=system_prompt_replace)
```

## DATA

No new data structures. String parameters threaded through existing call chain.

## TESTS

### `test_claude_code_cli.py`

1. **`test_build_cli_command_append_system_prompt`** — `--append-system-prompt` flag present with correct value
2. **`test_build_cli_command_system_prompt_replace`** — `--system-prompt` flag present with correct value
3. **`test_build_cli_command_no_system_prompt`** — neither flag present (backward compatible)
4. **`test_build_cli_command_both_prompts_raises`** — ValueError if both append and replace provided

### `test_interface.py` (additions)

5. **`test_build_claude_system_prompts_append_mode`** — returns `(combined, None)`
6. **`test_build_claude_system_prompts_replace_mode`** — returns `(None, combined)`
7. **`test_build_claude_system_prompts_skips_claude_md`** — project prompt skipped when pointing at CLAUDE.md
8. **`test_is_claude_md_true`** — matching path detected (including root-level CLAUDE.md and parent dirs)
9. **`test_is_claude_md_false`** — non-matching path passes through
10. **`test_is_claude_md_parent_dir`** — detects CLAUDE.md in parent directory

## LLM Prompt

```
Read pr_info/steps/summary.md for overall context, then implement Step 4.

Add append_system_prompt and system_prompt_replace parameters to build_cli_command(),
ask_claude_code_cli(), and ask_claude_code_cli_stream(). In build_cli_command(),
append the appropriate CLI flags (--append-system-prompt or --system-prompt).

In interface.py, add _build_claude_system_prompts() helper and import is_claude_md from prompt_loader.
Wire them into the Claude path in prompt_llm() and prompt_llm_stream() so that
loaded prompts are assembled and passed to the Claude provider.

Write tests for flag generation and redundancy detection.
All quality checks must pass.
```
