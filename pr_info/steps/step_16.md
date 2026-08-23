# Step 16 — PROMPTS section: lengths, and configured-but-missing → error

The PROMPTS section (`verify.py:338-374`) already prints provenance for the
system prompt, project prompt and claude mode. Missing: char lengths, and the
configured-but-missing case, where it currently displays a path that was never
used with an `[OK]` marker.

## WHERE

- `src/mcp_coder/cli/commands/verify.py` — PROMPTS section
- `src/mcp_coder/cli/commands/verify_exit_code.py` — one new parameter
- `tests/cli/commands/test_verify_sections_orchestration.py`
- `tests/cli/commands/test_verify_exit_codes.py`

## WHAT

```python
# verify_exit_code.py
def _compute_exit_code(..., prompts_ok: bool = True) -> int: ...
```

The section itself stays inline in `execute_verify`; only its rows change.

## HOW

- `load_prompts(project_dir)` is already called at `verify.py:337` and returns
  the resolved content — use it for the lengths, no second read.
- Use `is_prompt_configured_but_missing()` (step 15) per prompt:
  - configured **and** missing → `[ERR]`, value
    `f"{configured} — configured but not found; shipped default used instead"`,
    and set `prompts_ok = False`.
  - configured and present → `[OK]`, `f"{configured} ({len} chars)"`.
  - not configured → `[OK]`, `f"(shipped default) ({len} chars)"`.
- Keep `_prompt_source()` for the "not configured" wording; keep the existing
  `Claude mode` row and the CLAUDE.md redundancy warning untouched.
- Exit wiring: `_compute_exit_code` gains `prompts_ok: bool = True` and returns 1
  when it is False. Provider-independent (Decision 8) — this is a new exit-1 path
  that affects claude users too, so call it out in the commit message.

## ALGORITHM

```
for label, configured, content in (("System prompt", cfg.system_prompt, sys_text),
                                   ("Project prompt", cfg.project_prompt, proj_text)):
    if configured and is_prompt_configured_but_missing(configured, project_dir):
        rows.append(row(label, ERR, f"{configured} — configured but not found; shipped default used instead"))
        prompts_ok = False
    else:
        rows.append(row(label, OK, f"{_prompt_source(configured, 'shipped default')} ({len(content)} chars)"))
```

## DATA

```
=== PROMPTS ===============================================================
  System prompt         [OK]   (shipped default) (3812 chars)
  Project prompt        [ERR]  docs/team-prompt.md — configured but not found; shipped default used instead
  Claude mode           [OK]   append
```

## TDD

1. Both prompts unconfigured → two `[OK]` rows with char counts; exit code
   unchanged.
2. `pyproject.toml` configures a system prompt that exists → `[OK]` with the path
   and its length.
3. Configured but missing → `[ERR]` row and `execute_verify` returns 1.
4. `_compute_exit_code(..., prompts_ok=False)` returns 1; default `True` keeps
   every existing exit-code test green.
5. The claude-only CLAUDE.md redundancy warning still appears when applicable.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_16.md`.
> Implement step 16: extend the PROMPTS section in `cli/commands/verify.py` with
> per-prompt char lengths (from the already-loaded content) and make a
> configured-but-missing prompt path an `[ERR]` row using
> `is_prompt_configured_but_missing()` from step 15. Wire it to exit 1 by adding
> a `prompts_ok: bool = True` parameter to `_compute_exit_code` in
> `verify_exit_code.py`. This is provider-independent. Leave the Claude mode row
> and the CLAUDE.md redundancy warning unchanged. Write tests first (TDD).
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
