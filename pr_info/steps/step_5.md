# Step 5 — Migrate `execute_verify` Inline Rows (CONFIG, PROMPTS, LLM PROVIDER, Test prompt)

> **Note on line numbers:** all `verify.py:NNN` references in this step
> point at the file at branch HEAD before Step 1 lands. Locate the target
> by function name when implementing.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Steps
> 1-4 are merged. Follow TDD: update tests first, then migrate the inline
> formatting in `execute_verify`. Produce exactly one commit.

## WHERE

* **Source:** `src/mcp_coder/cli/commands/verify.py` — `execute_verify`
  function.
* **Tests:** `tests/cli/commands/test_verify_command.py`,
  `tests/cli/commands/test_verify_integration.py`,
  `tests/cli/commands/test_verify_orchestration.py`,
  `tests/cli/commands/test_verify_exit_codes.py`,
  `tests/cli/commands/test_verify_exit_codes_github.py` — any string-pinned
  assertions on the migrated rows.

## WHAT

### CONFIG section (`verify.py:506-530` approximately)

The current code has three render branches for entries with a `[group]` parent:

```python
if _looks_like_key(first) and rest:
    print(f"    {first:<18s} {symbol} {rest}")            # (A) key/value
elif symbol.strip():
    print(f"    {symbol} {value}")                        # (B) marker + value
else:
    print(f"    {value}")                                 # (C) value only
```

Migration:

* (A) → `print(_format_row(first, symbol, rest, indent=4))`
* (B) → `print(_format_freeform_row(symbol, value, indent=4))`
* (C) → `print(_format_freeform_row("", value, indent=4))`

The top-level rows (Config file, Expected path, Hint, Parse error):
```python
print(f"  {label:<20s} {symbol} {value}")
```
→ `print(_format_row(label, symbol, value, indent=2))`

The `[group]` header line (`print(f"  {label}")`) stays unchanged — it is
a header, not a row.

### PROMPTS section (`verify.py:538-553`)

Replace the three (or four) `f"  {'<label>':<20s} ..."` strings appended to
`prompt_lines`:

```python
prompt_lines.append(_format_row(
    "System prompt", symbols["success"],
    _prompt_source(prompt_config.system_prompt, "shipped default"),
    indent=2,
))
# similar for "Project prompt", "Claude mode", optional "Redundancy"
```

### LLM PROVIDER — Active provider (`verify.py:582`)

```python
print(f"  {'Active provider':<20s} {symbols['success']} {active_provider} (from {source})")
```
→ `print(_format_row("Active provider", symbols["success"], f"{active_provider} (from {source})", indent=2))`

### Test prompt rows (`verify.py:718, 735`)

Both success and failure paths:

```python
print(f"  {'Test prompt':<20s} {symbols['success']} responded OK")
print(f"  {'Test prompt':<20s} {symbols['failure']} FAILED ({category})")
```
→ `print(_format_row("Test prompt", <marker>, <value>, indent=2))`

The diagnostic line `"  Run with --debug for detailed diagnostics."` stays
unchanged (it is a freeform sentence, not a tabular row).

### MCP servers — health-check skipped fallbacks (`verify.py:650-651, 666-668`)

When `langchain-mcp-adapters` is not installed, the MCP servers branch
emits a no-marker fallback row at two sites currently like:

```python
print(f"  server health check skipped (langchain-mcp-adapters not installed)")
```

These are tabular rows by intent (sit under the section's other rows) but
have no label and no marker — they are emitted as freeform indented
strings today. Migrate both sites to:

```python
print(_format_freeform_row(
    symbols["warning"],
    "server health check skipped (langchain-mcp-adapters not installed)",
    indent=2,
))
```

(Use `_format_freeform_row` because there is no label to render — the
marker plus message form a single freeform notice. If the existing code
emits these without any marker, keep the migration symmetric: pass
`marker=""` so the indent + value land in the same column geometry as
neighbouring rows.) This was missed in the original Step 5 scope and was
identified as F9 in plan-review round 1.

## HOW

* `_format_row` and `_format_freeform_row` are already in `verify.py`
  (Step 1).
* No new imports.
* No control-flow changes.

## ALGORITHM

Direct substitution per branch.

## DATA

`execute_verify` return type unchanged (`int` exit code).

## Tests

* Search the listed test files for substrings such as `"  System prompt"`,
  `"  Active provider"`, `"  Test prompt"`, `"  Config file"`, `"    "` +
  any 18-wide CONFIG row. Update each pinned string for the new layout.
* Be careful: many tests use `in` substring matches; those typically
  survive width changes. Tests that pin **exact** spacing (e.g. checking
  for two consecutive spaces between marker and value) need recalculation.
* The CONFIG section is the user-visible surface that shifts most (was
  18-wide, now 22-wide); expect the heaviest test churn there.

## Verification

Run pylint, pytest, mypy.
