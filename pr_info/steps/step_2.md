# Step 2 — `[coordinator] dispatch_delay_seconds` config

## LLM prompt

> Read `pr_info/steps/summary.md` (section "Configuration") and this file, then implement Step 2
> only. Write the tests first, then the implementation. Run pylint, mypy and the fast unit tests
> (see `.claude/CLAUDE.md`), run the formatter, and make exactly one commit:
> `feat(config): add [coordinator] dispatch_delay_seconds`.

## WHERE

- `src/mcp_coder/utils/user_config.py`
  - `_CONFIG_SCHEMA["coordinator"]`: add `"dispatch_delay_seconds": FieldDef(int)`.
  - New function `get_dispatch_delay_seconds()` directly after `get_cache_refresh_minutes()`.
  - New module constant `DEFAULT_DISPATCH_DELAY_SECONDS = 15` next to it.
- `tests/utils/test_user_config_dispatch_delay.py` — **new** test file.

## WHAT

```python
DEFAULT_DISPATCH_DELAY_SECONDS = 15


def get_dispatch_delay_seconds() -> int:
    """Seconds the coordinator waits after starting a build, before the next dispatch.

    Must be longer than the Jenkins quiet period (5 s by default), otherwise the
    capacity re-check misses the build just started.

    Returns:
        The configured value, or 15 when unset or not positive.

    Raises:
        ValueError: If the TOML value is not an integer (schema type check).
    """
```

## HOW

- Reads via `get_config_values([("coordinator", "dispatch_delay_seconds", None)])`. The schema
  entry makes `get_config_values` raise `ValueError` for a wrong TOML type (string, float, bool);
  this function does not catch it.
- Do **not** copy `get_cache_refresh_minutes`' string-to-int branch (unreachable; no env var).

## ALGORITHM

```
value = get_config_values([...])[("coordinator", "dispatch_delay_seconds")]
if value is None: return DEFAULT
if not isinstance(value, int) or value <= 0:   # isinstance narrows for mypy; schema already rejected non-int
    logger.warning("Invalid dispatch_delay_seconds value '%s' (must be a positive integer), using default 15", value)
    return DEFAULT
return value
```

## DATA

- Returns `int` (> 0).

## Tests (write first) — `test_user_config_dispatch_delay.py`

Patch `mcp_coder.utils.user_config.load_config` (so the real `get_config_values` and its schema
check run) — never read the real user config.

1. Section/key absent → 15.
2. `{"coordinator": {"dispatch_delay_seconds": 30}}` → 30.
3. `0` and `-5` → 15 and a WARNING record mentioning `dispatch_delay_seconds`.
4. `"15"` (string) → `ValueError` containing `dispatch_delay_seconds`.
5. `true` (bool) → `ValueError`.
6. Schema: `_get_field_def("coordinator", "dispatch_delay_seconds")` is not None and has
   `field_type is int` (so `mcp-coder verify` does not report an unknown key).
