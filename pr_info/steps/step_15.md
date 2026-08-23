# Step 15 — Prompt path resolver + runtime WARNING on a missing configured prompt

`_resolve_and_read` (`prompt_loader.py:37-52`) silently returns `None` when a
*configured* prompt path does not exist, so mcp-coder falls back to the shipped
default while `verify` displays the configured path as if it were used. This is
provider-independent — it affects claude users too.

## WHERE

- `src/mcp_coder/prompts/prompt_loader.py`
- `tests/prompts/test_prompt_loader.py`

## WHAT

```python
def _resolve_path(configured_path: str | None, project_dir: Path | None) -> Path | None:
    """Resolve a configured prompt path to an existing file, or None."""

def is_prompt_configured_but_missing(
    configured_path: str | None, project_dir: Path | None
) -> bool:
    """True when a path is configured but does not resolve to an existing file."""
```

**No `get_system_prompt_path()`.** An earlier draft added one to mirror
`get_project_prompt_path`, but step 16 — the only consumer in this PR — needs
`is_prompt_configured_but_missing()`, which covers the system prompt too. A
public resolver with no caller is dead code (YAGNI; `vulture` runs in this
repo), so it is dropped. `get_project_prompt_path` keeps its signature and is
refactored onto `_resolve_path`.

## HOW

- **Factor, don't duplicate.** `_resolve_and_read` and `get_project_prompt_path`
  currently contain the same absolute/relative resolution logic. Extract it once
  into `_resolve_path` and have both callers plus
  `is_prompt_configured_but_missing` use it.
- `_resolve_and_read` logs a **WARNING** when `configured_path` is set but
  `_resolve_path` returns `None`. It does **not** raise: the shipped-default
  fallback is sane, and a typo must not brick every command (Decision 8).
- **Once per path per process** — module-level `set[str]` guard, so a per-turn
  workflow does not flood the log.
- **Test isolation for that cache.** A module-level set survives for the whole
  pytest process, so warning-count assertions would otherwise depend on test
  order (and on which worker `-n auto` picks). Add an `autouse` fixture in
  `tests/prompts/test_prompt_loader.py` that clears it around every test:
  ```python
  @pytest.fixture(autouse=True)
  def _clear_prompt_warning_cache():
      prompt_loader._warned_paths.clear()
      yield
      prompt_loader._warned_paths.clear()
  ```
  Reaching into the private set is deliberate: it is the cheapest honest
  isolation, and it keeps the production API free of a test-only reset hook.
- `load_prompts`, `load_system_prompt`, `load_project_prompt` keep their exact
  signatures and return types; only the logging behaviour changes.

## ALGORITHM

```
_warned_paths: set[str] = set()

_resolve_and_read(configured, project_dir):
    if configured is None: return None
    path = _resolve_path(configured, project_dir)
    if path is None:
        if configured not in _warned_paths:
            _warned_paths.add(configured)
            logger.warning("Configured prompt path not found: %s — using the shipped default", configured)
        return None
    return path.read_text(encoding="utf-8")
```

## DATA

`_resolve_path` and `get_project_prompt_path` return `Path | None` (the latter
unchanged); `is_prompt_configured_but_missing` returns `bool` and is consumed by
step 16.

## TDD

1. Configured path exists → content returned, **no** warning (use `caplog`).
2. Configured path missing → shipped default returned, one WARNING logged, no
   exception raised.
3. Same missing path read twice → still exactly one WARNING.
4. Two different missing paths → two WARNINGs.
   (Cases 2–4 rely on the autouse cache-clearing fixture above; without it they
   are order-dependent.)
5. `get_project_prompt_path` behaviour unchanged after the extraction: `None`
   when unconfigured, `None` when configured-but-missing, the `Path` when it
   exists.
6. Absolute and project-relative paths both resolve (regression on the
   extraction).
7. `is_prompt_configured_but_missing` is `False` when unconfigured, `True` for a
   configured-but-missing path (absolute and relative), `False` when the file
   exists.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_15.md`.
> Implement step 15: in `prompts/prompt_loader.py`, extract the shared
> absolute/relative path resolution into `_resolve_path()` and use it from
> `_resolve_and_read` and `get_project_prompt_path`. Make `_resolve_and_read`
> log a WARNING (once per path per process, via a module-level set) when a
> configured path does not exist, without raising, keeping the shipped-default
> fallback. Add `is_prompt_configured_but_missing()` for step 16 — and **no**
> `get_system_prompt_path()`: nothing would call it. Public signatures must not
> change. Write tests first (TDD), using `caplog` to assert the dedupe and an
> autouse fixture that clears the module-level warning cache so the counts are
> not order-dependent.
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
