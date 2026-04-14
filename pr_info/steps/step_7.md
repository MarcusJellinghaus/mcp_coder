# Step 7: `verify` Command Prompt Check + iCoder `/info` Prompt Paths

## References
- Summary: `pr_info/steps/summary.md`
- Depends on: Step 1 (prompt_loader module)

## WHERE

**Modified files:**
- `src/mcp_coder/cli/commands/verify.py` — add prompt config section
- `src/mcp_coder/icoder/core/commands/info.py` — show prompt paths
- `tests/cli/commands/test_verify.py` — test new section
- `tests/icoder/test_info_command.py` — test prompt paths display

## WHAT

### `verify.py` — new prompt section in `execute_verify()`

After the config section and before the LLM provider section, add:

```python
# Prompt configuration section
from ...prompts.prompt_loader import load_prompts, get_project_prompt_path, is_claude_md

# Reuse the project_dir variable already resolved earlier in execute_verify()
# project_dir = Path(args.project_dir).resolve() if args.project_dir else Path.cwd()
system_prompt, project_prompt, prompt_config = load_prompts(project_dir)

lines = ["\n=== PROMPTS ==="]
lines.append(f"  {'System prompt':<20s} {symbols['success']} {_prompt_source(prompt_config.system_prompt, 'shipped default')}")
lines.append(f"  {'Project prompt':<20s} {symbols['success']} {_prompt_source(prompt_config.project_prompt, 'shipped default')}")
lines.append(f"  {'Claude mode':<20s} {symbols['success']} {prompt_config.claude_system_prompt_mode}")

# Show CLAUDE.md redundancy detection for Claude provider
if active_provider == "claude" and prompt_config.project_prompt:
    prompt_path = get_project_prompt_path(project_dir)
    if is_claude_md(prompt_path, str(project_dir)):
        lines.append(f"  {'Redundancy':<20s} {symbols['warning']} project prompt is CLAUDE.md (will skip for Claude)")
print("\n".join(lines))
```

Helper:
```python
def _prompt_source(configured: str | None, default_label: str) -> str:
    return configured if configured else f"({default_label})"
```

### `info.py` — show prompt paths in `/info`

In `_format_info()`, add a section after the environments block:

```python
from mcp_coder.prompts.prompt_loader import load_prompts

system_prompt, project_prompt, prompt_config = load_prompts(
    Path(runtime_info.project_dir) if runtime_info.project_dir else None
)
lines.append("")
lines.append("Prompts:")
lines.append(f"  System:  {prompt_config.system_prompt or '(shipped default)'}")
lines.append(f"  Project: {prompt_config.project_prompt or '(shipped default)'}")
lines.append(f"  Claude mode: {prompt_config.claude_system_prompt_mode}")
```

## HOW

- Both changes are purely display — they call `load_prompts()` read-only and format output
- `verify.py` imports `is_claude_md` from `prompt_loader.py` (public function defined in Step 1, moved from `interface.py` per Fix 5)
- No behavioral changes, just informational output
- `_prompt_source` is a simple inline helper

## ALGORITHM

```python
# verify.py addition:
system_prompt, project_prompt, config = load_prompts(project_dir)
print(f"  System prompt: {config.system_prompt or '(shipped default)'}")
print(f"  Project prompt: {config.project_prompt or '(shipped default)'}")
print(f"  Claude mode: {config.claude_system_prompt_mode}")

# info.py addition:
system_prompt, project_prompt, config = load_prompts(project_dir)
lines.append(f"  System: {config.system_prompt or '(shipped default)'}")
lines.append(f"  Project: {config.project_prompt or '(shipped default)'}")
```

## DATA

No new data structures. Display only.

## TESTS

### `test_verify.py`

1. **`test_verify_shows_prompt_section`** — mock `load_prompts`, verify "PROMPTS" section appears in output
2. **`test_verify_shows_shipped_defaults`** — when no custom config, shows "(shipped default)"
3. **`test_verify_shows_custom_paths`** — when custom config, shows the configured paths

### `test_info_command.py`

4. **`test_info_shows_prompt_paths`** — verify prompt section appears in /info output
5. **`test_info_shows_shipped_defaults`** — default config shows "(shipped default)"

## LLM Prompt

```
Read pr_info/steps/summary.md for overall context, then implement Step 7.

Add a PROMPTS section to the verify command in src/mcp_coder/cli/commands/verify.py
that shows resolved system prompt path, project prompt path, and Claude mode.
Show a warning when project prompt points at CLAUDE.md (redundancy detection).

Add prompt paths to the /info command in src/mcp_coder/icoder/core/commands/info.py.

Write tests for both display changes. All quality checks must pass.
```
