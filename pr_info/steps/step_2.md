# Step 2 — Guard both langchain entry points (+ docs)

**Goal:** an explicitly requested session id with no history file raises `ValueError` from
both `ask_langchain` and `ask_langchain_stream`, so the CLI exits 1 instead of silently
answering from a blank conversation — proven end-to-end at the CLI boundary, and recorded
in the three docs that describe langchain session resumption.

**Depends on:** step 1 (`require_langchain_history`).

Read [summary.md](./summary.md) first.

---

## WHERE

| File | Action |
| --- | --- |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Import the helper; add `_resolve_session_id()`; swap two call sites; update two docstrings |
| `tests/llm/providers/langchain/conftest.py` | Add an **opt-in** (non-autouse) fixture that neutralises the guard |
| `tests/llm/providers/langchain/test_langchain_*.py` | Request that fixture in the unit tests that resume a synthetic id (4 files) |
| `tests/llm/providers/test_langchain_session_guard.py` | **New file** — real-filesystem guard tests, deliberately one directory *above* the langchain conftest |
| `tests/cli/commands/test_prompt.py` | One CLI-boundary test asserting `execute_prompt` returns 1 |
| `docs/architecture/architecture.md`, `docs/cli-reference.md`, `docs/configuration/config.md` | Three short additions (2f) |

The new test file must live at `tests/llm/providers/`, **not** in
`tests/llm/providers/langchain/`. That directory has no conftest of its own, so the
guard-disabling fixture is not even visible there and the tests see the real guard. No
`__init__.py` is needed — the directory already has one.

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
  so the id-resolution logic itself always runs for real even in tests that opt out of the
  guard.
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

Roughly 14 call sites across 5 files in that directory pass an explicit `session_id` into
`ask_langchain` / `ask_langchain_stream`. Eleven of them (4 files) are unit tests that patch
`load_langchain_history` at module level; those patches do not cover the new symbol, so they
would start raising. The remaining three are the `langchain_integration` resume tests, which
pass with the guard live and are left alone. (The other `session_id=` sites in that directory
call private helpers such as `run_agent` and `_ask_agent_stream` directly, below the guard,
and are unaffected.)

Absorb them with one function-scoped **opt-in** fixture — `patch` and `Generator` are
already imported in that file:

```python
@pytest.fixture
def skip_langchain_history_guard() -> Generator[None, None, None]:
    """Neutralise the resume guard for tests that use synthetic session ids.

    Opt-in on purpose: an autouse version would also disable the guard for
    the langchain_integration resume tests in test_langchain_integration.py,
    which are the only end-to-end path where a real history file is written
    and then resumed. Those tests must run with the guard live.
    """
    with patch("mcp_coder.llm.providers.langchain.require_langchain_history"):
        yield
```

**Not autouse, no marker.** Add `skip_langchain_history_guard` as a parameter to each unit
test that calls `ask_langchain` / `ask_langchain_stream` with an explicit `session_id` —
eleven sites across four files:

- `test_langchain_agent_mode.py` (`:157`)
- `test_langchain_multi_turn.py` (`:137`, `:222`, `:287`, `:331`, `:387`)
- `test_langchain_provider.py` (`:262`, `:326`)
- `test_langchain_streaming.py` (`:113`, `:138`, `:260`)

Deliberately **not** applied to `tests/llm/providers/langchain/test_langchain_integration.py`
(`:90`, `:195`, `:229`): those `langchain_integration` tests resume ids whose history files
were really written by the preceding turn, so they pass with the guard live — and they are
the only place the guard is exercised end-to-end against a genuine resume.

A missed site fails loudly with the step-1 `ValueError`, so the list above is a starting
point, not a contract: add the fixture wherever the suite reports the guard firing.

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

### 2e. CLI boundary — `tests/cli/commands/test_prompt.py`

The issue's first acceptance item is *"exits 1"*. `cli/commands/prompt.py:238-243` catches
bare `Exception` and returns 1, so no plumbing is needed — but nothing currently ties the
guard to that exit code. Add one test that does, rather than relying on the boundary
implicitly:

`test_langchain_continue_from_non_session_stem_exits_1` — build an
`argparse.Namespace(prompt=..., continue_session_from=<tmp>/response_2025-01-01T00-00-00.json,
llm_method="langchain", mcp_config=None, settings=None, project_dir=None)` and assert
`execute_prompt(args) == 1`.

- Follow the existing patch set in that file: `resolve_llm_method` (returning
  `("langchain", "cli argument")`), `prepare_llm_environment`, `resolve_mcp_config_path`,
  and `mlflow_conversation` as in `test_continue_from_success`.
- Do **not** patch `prompt_llm` / `prompt_llm_stream` — the point is to run the real path
  down into `ask_langchain_stream`. Patch
  `mcp_coder.llm.providers.langchain._load_langchain_config` with a truthy `"backend"` so
  the pre-existing "backend not configured" error cannot produce a false pass, and
  monkeypatch `Path.home()` to `tmp_path` so the expected history path is missing by
  construction.
- Assert on `caplog` that the logged failure names the requested id
  (`response_2025-01-01T00-00-00`), so a future unrelated exception cannot keep this test
  green.

This is the langchain stem-resolution path from `prompt.py:107-111`: the file's stem becomes
the session id, which is why a stored-response filename never has a history file.

### 2f. Documentation

Record the new behaviour where the three docs already describe langchain session
resumption. Match each file's existing style, keep each addition to 1-3 lines, add no new
sections or headings, and do not restate the error message verbatim (it is asserted in
tests and would drift).

**`docs/architecture/architecture.md`** — under the existing
`**Session storage**: history persisted to ~/.mcp_coder/sessions/langchain/` bullet
(line ~253), alongside the "Stored history is **system-free**" sub-bullet, add one
sub-bullet: an explicitly requested `session_id` with no history file raises `ValueError`
rather than starting a blank conversation; both `ask_langchain` and `ask_langchain_stream`
are guarded at id resolution; a new session (no id) is unaffected.

**`docs/cli-reference.md`** — line 169 currently reads:

```
- `--session-id ID` - Direct session ID for continuation (overrides file-based options)
```

Extend it to note that for `--llm-method langchain` the id must already have a stored
history file, and that an unknown id is an error rather than a new conversation. Keep the
one-line-per-option style; no example block.

**`docs/configuration/config.md`** — at the end of the "Session Continuity" subsection
(after line 511), add a short paragraph: resuming a langchain session id with no history
file at the documented path is an error naming the id and the expected path; a blank
conversation is never silently started.

Then state the `--continue-session-from` consequence **accurately**. The problem is *not*
limited to claude response filenames: for langchain, `prompt.py:107-111` derives the id from
the *filename stem* via `extract_langchain_session_id`, so any file whose stem is not itself
a langchain session id resolves to a bogus id — including a langchain file written by
`--store-response`, whose stem is `response_<ts>`. Say plainly that under
`--llm-method langchain` the documented `--store-response` → `--continue-session-from`
workflow now **exits 1** instead of silently starting a blank conversation, and that
`--continue-session` (which discovers a real file under
`~/.mcp_coder/sessions/langchain/`) or an explicit `--session-id` is the working route.

## CHECKS

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check   (extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

The whole `tests/llm/providers/langchain/` suite must stay green — that is the point of the
fixture in 2c. Also confirm `tests/llm/test_interface.py` and the *existing*
`tests/cli/commands/test_prompt.py` tests still pass: they mock at `prompt_llm` /
`prompt_llm_stream` / `resolve_llm_method` and never reach the guard, so no fallout is
expected there (only the new 2e test runs the real provider path).

The `langchain_integration` tests in `test_langchain_integration.py` are excluded by the
marker filter above; run them separately with `markers=["langchain_integration"]` when the
optional backend is available, since they are the ones that now exercise the guard live.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`, then implement step 2 only.
> Step 1 (`require_langchain_history` in `session_storage.py`) is already done.
>
> Work test-first: create `tests/llm/providers/test_langchain_session_guard.py` with the four
> tests described under 2d and the CLI test from 2e in `tests/cli/commands/test_prompt.py`,
> watch them fail, then implement `_resolve_session_id()` in
> `src/mcp_coder/llm/providers/langchain/__init__.py` and swap it into both entry points at
> lines 306 and 638 as specified under WHAT / ALGORITHM. Add the opt-in fixture from 2c to
> `tests/llm/providers/langchain/conftest.py` and request it in the affected unit tests so
> the existing suite in that directory stays green. Finish with the three documentation
> edits in 2f.
>
> Constraints: the new test file goes in `tests/llm/providers/`, NOT in
> `tests/llm/providers/langchain/` — being outside that conftest is what lets it see the real
> guard. The fixture must NOT be autouse: `test_langchain_integration.py` has to keep running
> with the guard live. Do not give `_resolve_session_id` a `base_dir` parameter. Remember
> `ask_langchain_stream` is a generator, so `pytest.raises` must consume the iterator. In 2f,
> do not repeat the inaccurate "claude response file" framing — a langchain
> `--store-response` file has the same problem.
>
> Use MCP tools for all file operations. When done, run `run_pylint_check`,
> `run_pytest_check` (with `-n auto` and the integration-marker exclusions from
> `CLAUDE.md`) and `run_mypy_check`, and fix everything they report. Then make exactly one
> commit for this step.
