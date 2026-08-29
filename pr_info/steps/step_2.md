# Step 2 — Guard both langchain entry points

**Goal:** an explicitly requested session id with no history file raises `ValueError` from
both `ask_langchain` and `ask_langchain_stream`, so the CLI exits 1 instead of silently
answering from a blank conversation.

**Depends on:** step 1 (`require_langchain_history`).

Read [summary.md](./summary.md) first.

---

## WHERE

| File | Action |
| --- | --- |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Import the helper; add `_resolve_session_id()`; swap two call sites; update two docstrings |
| `tests/llm/providers/langchain/conftest.py` | Add an unconditional autouse fixture that neutralises the guard |
| `tests/llm/providers/test_langchain_session_guard.py` | **New file** — real-filesystem guard tests, deliberately one directory *above* the langchain conftest |

The new test file must live at `tests/llm/providers/`, **not** in
`tests/llm/providers/langchain/`. That directory has no conftest of its own, so the autouse
fixture never applies there and the tests see the real guard. No `__init__.py` is needed —
the directory already has one.

## WHAT

### 2a. Provider helper

In `src/mcp_coder/llm/providers/langchain/__init__.py`, extend the existing import block
(currently lines 21-24):

```python
from mcp_coder.llm.storage.session_storage import (
    load_langchain_history,
    require_langchain_history,
    store_langchain_history,
)
```

Add, next to the other module-level private helpers:

```python
def _resolve_session_id(session_id: str | None) -> str:
    """Return the session id to use, validating an explicitly requested one.

    Args:
        session_id: Id the caller asked to resume, or None for a new session.

    Returns:
        The requested id, or a freshly minted UUID when none was requested.

    Raises:
        ValueError: If *session_id* was supplied but has no history file.
    """
```

### 2b. Both call sites

Replace, in `ask_langchain` (line 306) and in `ask_langchain_stream` (line 638):

```python
sid = session_id or str(uuid.uuid4())      # before
sid = _resolve_session_id(session_id)      # after
```

Extend the `Raises:` section of **both** public docstrings, e.g.:

```
    Raises:
        ValueError: If the langchain backend is not configured, or if
            *session_id* was supplied but has no history file.
```

## HOW

- `uuid` is already imported. No other new imports.
- Keep `_resolve_session_id` module-private; the conftest fixture patches
  `require_langchain_history` (the imported name in this module), not `_resolve_session_id`,
  so the id-resolution logic itself always runs for real.
- Do **not** add a `base_dir` parameter to `_resolve_session_id`. Production never needs one,
  and the tests reach the real path by monkeypatching `Path.home()`.
- Guard placement is at id resolution, not at the four `load_langchain_history` call sites
  (`:358`, `:424`, `:536`, `:685`) — each resolution point dominates two of them.

## ALGORITHM

```
if not session_id:          # None or "" -> new session, no filesystem touch
    return str(uuid.uuid4())
require_langchain_history(session_id)    # raises ValueError when absent
return session_id
```

The `if not session_id` form (rather than `is None`) preserves today's
`session_id or str(uuid.uuid4())` behaviour exactly, including the empty-string case.

## DATA

- **Returns:** `str` — always a usable session id.
- **Raises:** `ValueError`, message built in step 1's storage helper.
- **Laziness:** `ask_langchain_stream` is a generator, so its guard raises on the first
  `next()`, not at call time. Any `pytest.raises` around it **must consume the iterator**
  (`list(...)` or `next(...)`).

## TESTS (write first)

### 2c. Fallout fixture — `tests/llm/providers/langchain/conftest.py`

Roughly 14 call sites across 6 files in that directory pass an explicit `session_id` into
`ask_langchain` / `ask_langchain_stream` and patch `load_langchain_history` at module level;
those patches do not cover the new symbol, so they would all start raising. (The other
`session_id=` sites in that directory call private helpers such as `run_agent` and
`_ask_agent_stream` directly, below the guard, and are unaffected.)

Absorb them all with one function-scoped autouse fixture — `patch` and `Generator` are
already imported in that file:

```python
@pytest.fixture(autouse=True)
def _skip_langchain_history_guard() -> Generator[None, None, None]:
    """Neutralise the resume guard: these tests use synthetic session ids.

    Real-filesystem coverage of the guard lives one directory up, in
    tests/llm/providers/test_langchain_session_guard.py, which this
    fixture deliberately does not reach.
    """
    with patch("mcp_coder.llm.providers.langchain.require_langchain_history"):
        yield
```

Unconditional — no marker, no opt-out branch. It is harmless for the
`langchain_integration` tests in that directory, whose ids refer to files that really exist.

### 2d. New file — `tests/llm/providers/test_langchain_session_guard.py`

Four tests. A `monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))` fixture
redirects `~/.mcp_coder/sessions/langchain/` into `tmp_path`; this is the pattern already
used at `tests/llm/storage/test_session_storage.py:378-388`, and it is correct on every
platform because `get_user_app_data_dir` is `Path.home() / ".mcp_coder"`.

`_load_langchain_config` must be patched to return a dict with a truthy `"backend"`
(e.g. `{"backend": "openai", "model": "gpt-4o-mini", "api_key": "k", "base_url": None,
"api_version": None, "default_provider": None}`); otherwise the pre-existing "backend not
configured" `ValueError` fires first and the test would pass for the wrong reason.

1. `test_ask_langchain_raises_for_unknown_session_id` — `pytest.raises(ValueError)` around
   `ask_langchain("q", session_id="ghost-id")`; assert the message contains `"ghost-id"` and
   `"ghost-id.json"`, and that the reported path is under `tmp_path`.
2. `test_ask_langchain_stream_raises_for_unknown_session_id` — same, but wrap
   `list(ask_langchain_stream("q", session_id="ghost-id"))` so the generator is consumed.
3. `test_resolve_session_id_accepts_existing_history` — `store_langchain_history("known-id",
   [])` (no `base_dir`, so it lands under the patched home), then assert
   `_resolve_session_id("known-id") == "known-id"`. This is the *successful resume stays
   silent* case.
4. `test_resolve_session_id_mints_uuid_when_none_given` — `uuid.UUID(_resolve_session_id(None))`
   parses, and no file was created under `tmp_path`. This is the *new session is unaffected*
   case.

Tests 1 and 2 must not need langchain installed: the guard raises before
`_build_system_messages`, which is the first `langchain_core` import in that code path. Do
not patch `_create_chat_model` or drive a model — if a test in this file reaches the model,
the guard was placed too late.

## CHECKS

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check   (extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

The whole `tests/llm/providers/langchain/` suite must stay green — that is the point of the
fixture in 2c. Also confirm `tests/llm/test_interface.py` and `tests/cli/commands/test_prompt.py`
still pass: they mock at `prompt_llm` / `resolve_llm_method` and never reach the guard, so no
fallout is expected there.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`, then implement step 2 only.
> Step 1 (`require_langchain_history` in `session_storage.py`) is already done.
>
> Work test-first: create `tests/llm/providers/test_langchain_session_guard.py` with the four
> tests described under 2d, watch them fail, then implement `_resolve_session_id()` in
> `src/mcp_coder/llm/providers/langchain/__init__.py` and swap it into both entry points at
> lines 306 and 638 as specified under WHAT / ALGORITHM. Add the autouse fixture from 2c to
> `tests/llm/providers/langchain/conftest.py` so the existing suite in that directory stays
> green.
>
> Constraints: the new test file goes in `tests/llm/providers/`, NOT in
> `tests/llm/providers/langchain/` — being outside that conftest is what lets it see the real
> guard. Do not add a pytest marker or any opt-out logic to the fixture. Do not give
> `_resolve_session_id` a `base_dir` parameter. Remember `ask_langchain_stream` is a
> generator, so `pytest.raises` must consume the iterator.
>
> Use MCP tools for all file operations. When done, run `run_pylint_check`,
> `run_pytest_check` (with `-n auto` and the integration-marker exclusions from
> `CLAUDE.md`) and `run_mypy_check`, and fix everything they report. Then make exactly one
> commit for this step.
