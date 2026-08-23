# Step 2 — Unknown-key hints: rename table + "did you mean"

After step 1 a stale `endpoint = "..."` becomes an unknown key. Edit distance
will **not** connect `endpoint` to `base_url` (Decision 16), so the rename needs
an explicit hint; every other section benefits from a generic near-miss
suggestion (Decision 7).

## WHERE

- **New:** `src/mcp_coder/utils/config_hints.py`
- **New:** `tests/utils/test_config_hints.py`
- Modified: `src/mcp_coder/utils/user_config.py` — `_verify_section` unknown-key
  branch only (the file is at 721 lines, so the logic lives in the new module).
- Modified: `tests/utils/test_verify_config.py`

## WHAT

```python
# config_hints.py
_RENAME_HINTS: dict[tuple[str, str], str] = {
    ("llm.langchain", "endpoint"): "renamed to base_url",
}

def suggest(name: str, candidates: Iterable[str]) -> str | None:
    """Return the closest candidate to *name*, or None when nothing is close."""

def unknown_key_hint(section: str, key: str, known_keys: Iterable[str]) -> str | None:
    """Return an explanatory suffix for an unknown config key, or None."""
```

## HOW

`user_config._verify_section` already emits
`{"label": f"[{section_name}]", "status": "warning", "value": f"unknown key: {key}"}`.
Append the hint when one is available:

```python
from .config_hints import unknown_key_hint
...
hint = unknown_key_hint(section_name, key, fields.keys())
value = f"unknown key: {key}" + (f" — {hint}" if hint else "")
```

`suggest()` is also reused by step 11 (`--check-models` near-misses), so keep it
free of config-specific knowledge.

## ALGORITHM

```
unknown_key_hint(section, key, known):
    if (section, key) in _RENAME_HINTS: return _RENAME_HINTS[(section, key)]
    match = suggest(key, known)
    return f"did you mean {match}?" if match else None

suggest(name, candidates):
    hits = difflib.get_close_matches(name, list(candidates), n=1, cutoff=0.6)
    return hits[0] if hits else None
```

## DATA

`unknown_key_hint` returns `str | None`. Rendered output:

```
  [llm.langchain]
                 [WARN] unknown key: endpoint — renamed to base_url
                 [WARN] unknown key: modell — did you mean model?
```

Status stays `"warning"` → exit-neutral.

## TDD

1. `test_config_hints.py`: `suggest("modell", ["model", "backend"]) == "model"`;
   `suggest("zzz", [...]) is None`; `unknown_key_hint("llm.langchain", "endpoint", [...])`
   returns the rename text and does **not** consult edit distance;
   near-miss path for an unrelated section (e.g. `("github", "tokenn")`).
2. `test_verify_config.py`: a config with `[llm.langchain] endpoint = "x"`
   produces a warning entry whose value contains `renamed to base_url`; a config
   with a typo'd key in another section produces `did you mean`.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`.
> Implement step 2: add `src/mcp_coder/utils/config_hints.py` with `suggest()`
> and `unknown_key_hint()`, including a per-section rename table mapping
> `("llm.langchain", "endpoint")` to `"renamed to base_url"`. Wire it into the
> unknown-key branch of `user_config._verify_section` so warnings carry the hint.
> Keep the warning exit-neutral. Write tests first (TDD).
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
