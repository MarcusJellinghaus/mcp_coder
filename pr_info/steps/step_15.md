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

def get_system_prompt_path(project_dir: Path | None = None) -> Path | None:
    """Resolve the configured system prompt path (None when using the default)."""

def is_prompt_configured_but_missing(
    configured_path: str | None, project_dir: Path | None
) -> bool:
    """True when a path is configured but does not resolve to an existing file."""
```

## HOW

- **Factor, don't duplicate.** `_resolve_and_read` and `get_project_prompt_path`
  currently contain the same absolute/relative resolution logic. Extract it once
  into `_resolve_path` and have all callers use it — the new
  `get_system_prompt_path` then costs three lines instead of a third copy.
- `_resolve_and_read` logs a **WARNING** when `configured_path` is set but
  `_resolve_path` returns `None`. It does **not** raise: the shipped-default
  fallback is sane, and a typo must not brick every command (Decision 8).
- **Once per path per process** — module-level `set[str]` guard, so a per-turn
  workflow does not flood the log.
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

`_resolve_path` returns `Path | None`; `get_system_prompt_path` /
`get_project_prompt_path` return `Path | None` (unchanged for the latter);
`is_prompt_configured_but_missing` returns `bool` and is consumed by step 16.

## TDD

1. Configured path exists → content returned, **no** warning (use `caplog`).
2. Configured path missing → shipped default returned, one WARNING logged, no
   exception raised.
3. Same missing path read twice → still exactly one WARNING.
4. Two different missing paths → two WARNINGs.
5. `get_system_prompt_path` mirrors `get_project_prompt_path`: `None` when
   unconfigured, `None` when configured-but-missing, the `Path` when it exists.
6. Absolute and project-relative paths both resolve (regression on the
   extraction).
7. `is_prompt_configured_but_missing` is `False` when unconfigured.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_15.md`.
> Implement step 15: in `prompts/prompt_loader.py`, extract the shared
> absolute/relative path resolution into `_resolve_path()` and use it from
> `_resolve_and_read`, `get_project_prompt_path` and a new
> `get_system_prompt_path`. Make `_resolve_and_read` log a WARNING (once per path
> per process, via a module-level set) when a configured path does not exist,
> without raising, keeping the shipped-default fallback. Add
> `is_prompt_configured_but_missing()` for step 16. Public signatures must not
> change. Write tests first (TDD), using `caplog` to assert the dedupe.
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
