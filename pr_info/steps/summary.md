# Summary — Issue #1138: langchain resume silently starts a blank conversation

## Problem

`load_langchain_history` returns `[]` for a missing history file
(`llm/storage/session_storage.py:209-222`), and both langchain entry points echo the
requested session id straight back (`llm/providers/langchain/__init__.py:306`, `:638`).

A resume with an id that has no history file therefore **exits 0**, answers from a blank
conversation, stores the id, and a later `--continue-session` chains off it. The user
believes they are continuing a conversation and are talking to a blank one.

Reachable via:

- `--session-id <id>` naming an id with no history file
- `--continue-session-from <path>` pointing at a *claude* response file while the provider
  is langchain — the stem becomes `response_2025-...`, which has no history file
- the history file deleted, or `~/.mcp_coder/sessions/langchain/` cleaned between runs

Not reachable via plain `--continue-session` / `--continue-session-from` on a langchain
file: those derive the id from an existing file's stem, so the file exists by construction.

## Fix

Raise `ValueError` when a session id was **explicitly requested** and its history file does
not exist. The message names the requested id and the expected history path.

## Architectural / design changes

### 1. New public storage helper: `require_langchain_history()`

`llm/storage/session_storage.py` gains one public function:

```python
def require_langchain_history(session_id: str, base_dir: str | None = None) -> None
```

It raises `ValueError` when the history file is absent, and returns `None` otherwise.

**Design decision — one helper, not two.** An earlier shape exposed a public path accessor
*plus* an existence predicate, so the provider could format the path into the message. That
required promoting the private `_langchain_session_path` to public API. Instead the check
*and* the message live together in the storage module, which is the only place that knows
the path layout. `_langchain_session_path` stays private and unmoved.

**Design decision — message lives in the storage layer.** The message is entirely about a
storage artifact (`Expected history file: <path>`). Exporting a path accessor purely so the
provider could re-derive a string that storage already has would be a larger API surface for
no gain. The raised type and the resulting CLI exit code are unaffected by where it is
raised.

The `base_dir` parameter mirrors `load_langchain_history(session_id, base_dir=None)` so
tests can point at a tmp directory. **Production never passes `base_dir`.**

### 2. New provider-private helper: `_resolve_session_id()`

`llm/providers/langchain/__init__.py` gains:

```python
def _resolve_session_id(session_id: str | None) -> str
```

It mints a fresh UUID when no id was requested, and validates the history file when one was.
Both entry points call it, replacing the bare `sid = session_id or str(uuid.uuid4())` at
`:306` (`ask_langchain`) and `:638` (`ask_langchain_stream`).

**Design decision — guard at id-resolution, not at history-load.** There are four
`load_langchain_history` call sites (`:358` text, `:424` agent, `:536` agent-stream, `:685`
text-stream) but only two id-resolution points, and each resolution point dominates two load
sites. Guarding the two resolution points covers all four with half the code.

**Design decision — both entry points, not just the blocking one.** The streaming path is
what `icoder` and `--stream` use, so guarding only `ask_langchain` would leave the bug where
it bites most.

**Design decision — guard only when `session_id` was explicitly supplied.** langchain mints
a fresh UUID for every new session; an unguarded existence check would fire on every first
turn. The `if not session_id` short-circuit preserves today's behaviour exactly, including
for the empty-string case.

### 3. Error surfacing (no new plumbing)

| Boundary | Behaviour | Change needed |
| --- | --- | --- |
| `cli/commands/prompt.py:238-243` | catches bare `Exception`, logs, returns 1 | none |
| `icoder/ui/app.py:293` | catches, finalises the turn, shows the error | none |

`ask_langchain_stream` is a generator, so its guard **raises lazily** on first `next()`, not
at call time — consistent with the existing "backend not configured" raise in the same
function.

### 4. Test-fallout strategy

An unconditional function-scoped autouse fixture in
`tests/llm/providers/langchain/conftest.py` neutralises the guard for that directory, which
already uses the autouse pattern for `_mock_langchain_modules`.

**Design decision — the real-filesystem test lives one directory up.** A blanket
always-passes mock would hide exactly the kind of path bug the guard depends on, so at least
one test must exercise `_langchain_session_path` for real. Rather than adding a registered
pytest marker plus opt-out logic inside the autouse fixture, the real-filesystem test is
placed at `tests/llm/providers/test_langchain_session_guard.py` — **outside** the langchain
conftest's directory, so the autouse fixture never applies to it. That directory has no
conftest of its own and is already used this way by `test_provider_structure.py`.

This works because the guard raises *before* any langchain import: `ask_langchain` runs
config → backend check → `_resolve_session_id` → raise, and `_build_system_messages` (the
first `langchain_core` import) is never reached. The new test file therefore needs neither
langchain installed nor the sys.modules mocks.

## Known consequences (accepted, not regressions)

- `--session-id` can no longer *create* a langchain session under a caller-chosen id. A
  separate flag if that is ever wanted.
- After a failed resume in `icoder`, `LLMService._session_id` keeps the bad id (it only
  updates from `done` events, `llm_service.py:116-120`), so every later turn raises the same
  error until `/clear`. Auto-reset was considered and rejected: it needs a distinguishable
  exception type, and retrying is sometimes what the user wants.
- `agent.py:672-694` already logs *"history not stored (the turn is not recorded)"* when no
  terminal graph event matches, yet still yields `done` carrying the session id. In `icoder`
  that id is adopted, so the **next** turn now raises instead of blank-starting. This is the
  correct signal — the turn genuinely was not recorded — but it is a new failure mode not
  listed in the issue.
- Custom-path resume (`--continue-session-from /some/copy/abc.json`) now errors where it
  previously blank-started. Naming the *expected* path in the message avoids claiming the id
  "does not exist" when the user is looking at a file with that name.

## Out of scope

- **Claude** — ruled out by probe in #1134: an unrecognised id is exit 1 already.
- **Copilot** (`llm/providers/copilot/copilot_cli.py:216`) — unverified, separate issue.

## Files created / modified

### Created

| Path | Purpose |
| --- | --- |
| `tests/llm/providers/test_langchain_session_guard.py` | Real-filesystem guard tests, outside the langchain conftest |
| `pr_info/steps/summary.md` | This document |
| `pr_info/steps/step_1.md` … `step_3.md` | Step details |

### Modified

| Path | Change | Step |
| --- | --- | --- |
| `src/mcp_coder/llm/storage/session_storage.py` | Add `require_langchain_history()`; add to `__all__` | 1 |
| `tests/llm/storage/test_session_storage.py` | Two tests for the new helper via tmp `base_dir` | 1 |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Import helper; add `_resolve_session_id()`; swap `:306` and `:638`; update two `Raises:` docstrings | 2 |
| `tests/llm/providers/langchain/conftest.py` | Unconditional autouse fixture neutralising the guard | 2 |
| `docs/architecture/architecture.md` | Note the guard under LangChain session storage | 3 |
| `docs/cli-reference.md` | Note the `--session-id` restriction for langchain | 3 |
| `docs/configuration/config.md` | Note the guard under "Session Continuity" | 3 |

### Not modified (verified)

- `src/mcp_coder/llm/storage/__init__.py` — the package `__init__` does not re-export
  `load_langchain_history` / `store_langchain_history`; the provider imports directly from
  `.session_storage`. `require_langchain_history` follows the same pattern.
- `src/mcp_coder/cli/commands/prompt.py`, `src/mcp_coder/icoder/**` — both boundaries
  already catch `Exception`.
- `pyproject.toml` — no new pytest marker is needed.

## Steps

1. **[step_1.md](./step_1.md)** — `require_langchain_history()` in the storage layer.
2. **[step_2.md](./step_2.md)** — `_resolve_session_id()` guard in both langchain entry
   points, plus the test-fallout fixture.
3. **[step_3.md](./step_3.md)** — Documentation.

## Acceptance (from the issue)

- [ ] An explicitly requested session id with no history file exits 1, naming the id and the
      expected path.
- [ ] Both `ask_langchain` and `ask_langchain_stream` are guarded.
- [ ] A new session (no id passed) is unaffected.
- [ ] A successful resume stays silent.
- [ ] One test exercises the real filesystem path via a tmp `base_dir`.
