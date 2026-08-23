# Step 14 — Surface `MCP_CODER_LLM_PROVIDER` in `verify`

Decision 23: the same treatment redirect env vars get, applied to provider
selection. After step 12 the variable no longer silently wins, but a user whose
`--llm-method` overrode an exported value should still see that it is set.

## WHERE

- `src/mcp_coder/cli/commands/verify.py` — the LLM PROVIDER section
- `tests/cli/commands/test_verify_sections_orchestration.py`

## WHAT

No new function required — a few lines beside the existing `Active provider` row:

```python
print(_format_row("Active provider", symbols["success"],
                  f"{active_provider} (from {source})", indent=2))
```

## HOW

`resolve_llm_method` already returns `(provider, source)` where `source` is one
of `"cli argument"`, `"env MCP_CODER_LLM_PROVIDER"`, `"config default_provider"`,
`"default"`. Three cases:

| env set? | `source` | row |
|---|---|---|
| no | any | nothing extra |
| yes | `env MCP_CODER_LLM_PROVIDER` | `[OK]` — it *is* the source; no extra row needed beyond the existing one |
| yes | anything else | `[WARN]` — set but overridden |

The warning row must **not** call the variable "the source" when `--llm-method`
won. Exit-neutral: printed only, never fed into the exit code.

## ALGORITHM

```
env = os.environ.get("MCP_CODER_LLM_PROVIDER")
if env and source != "env MCP_CODER_LLM_PROVIDER":
    print(row("MCP_CODER_LLM_PROVIDER", WARN,
              f"set to '{env}' but overridden by {source} — using '{active_provider}'"))
```

## DATA

```
  Active provider       [OK]   langchain (from cli argument)
  MCP_CODER_LLM_PROVIDER [WARN] set to 'claude' but overridden by cli argument — using 'langchain'
```

The label exceeds `_LABEL_WIDTH` (22); pass an explicit `label_width` so the
value column stays aligned with the rows around it.

## TDD

1. Env set + `--llm-method langchain` → warning row printed; it does **not**
   contain the word "source"; exit code unchanged.
2. Env set + no CLI flag → `Active provider` row already says
   `(from env MCP_CODER_LLM_PROVIDER)`; **no** extra warning row.
3. Env unset → no extra row.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_14.md`.
> Implement step 14: in `cli/commands/verify.py`, print an exit-neutral `[WARN]`
> row when `MCP_CODER_LLM_PROVIDER` is set but did **not** decide the active
> provider, naming what overrode it. When it *is* the source, the existing
> `Active provider` row already says so — add nothing. Use an explicit
> `label_width` so the long label stays aligned. Write tests first (TDD) covering
> all three cases.
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
