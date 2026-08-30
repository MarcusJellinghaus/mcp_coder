# Step 1 — Prep: extract the langchain setup helpers out of the provider `__init__`

**Depends on:** nothing. **Behaviour-neutral — pure move, no new feature.**

`src/mcp_coder/llm/providers/langchain/__init__.py` is **739** lines and CI runs
`mcp-coder check file-size --max-lines 750`. Step 7 adds roughly +60 lines to `_ask_agent_stream`
and `ask_langchain_stream`, so that job would fail. The file is **not** in
`.large-files-allowlist` and must not be added to it: the allowlist is grandfathering to be
reduced (#353), not an escape hatch. This step buys the headroom by moving a cohesive block out.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/llm/providers/langchain/_setup.py` | **create** — the moved block |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | **modify** — delete the block, re-export it |
| `tests/llm/providers/langchain/conftest.py` | **modify** — re-point the `require_langchain_history` patch |
| `tests/llm/providers/langchain/test_langchain_provider.py` | **modify** — re-point the `get_config_values` patches |

## WHAT

Move these seven module-level symbols, **unchanged**, into `_setup.py`:

```
_build_system_messages      _BACKEND_ERROR_PARAMS      _auth_errors_for_backend
_handle_provider_error      _load_langchain_config     _create_chat_model
_resolve_session_id
```

They form one unit: *turn user config into a ready `BaseChatModel`, a session id and system
messages, and map backend exceptions to `LLMAuthError` / `LLMConnectionError`.* All four call
paths (text, text-stream, agent, agent-stream) sit above them and none of them calls anything
defined later in `__init__.py`, so the move is strictly downward.

`_AGENT_OVERALL_TIMEOUT` stays in `__init__.py` — it belongs to the consumer loop, not to setup.

## HOW

* **Direction matters.** The *consumer loop* (`_ask_agent_stream`) is the obvious thing to move,
  and it is wrong here: it is the file's **top** layer and calls `_create_chat_model` and
  `_handle_provider_error`, so a `_agent_stream.py` would have to import its own parent package
  back and would read a half-initialised module. Moving the **bottom** layer has no cycle.
* **Re-export, and keep the call sites in `__init__.py`.** `__init__.py` gains
  `from ._setup import _build_system_messages, _create_chat_model, _handle_provider_error,
  _load_langchain_config, _resolve_session_id` (plus the two remaining names if anything reads
  them). This is load-bearing, not cosmetic: **21** test modules patch or import
  `mcp_coder.llm.providers.langchain._load_langchain_config` / `…._create_chat_model` through the
  package namespace. Because every caller stays in `__init__.py` and resolves the name through
  that module's globals, those patches keep working **unchanged**. Do not move a call site into
  `_setup.py`. (The separate `…langchain.verification._load_langchain_config` patches bind a name
  in `verification`'s own globals and are unaffected either way.)
* **Two *consumed* names are patched too, and the re-export does not save them.** The re-export
  protects patches on the moved symbols; it does nothing for the names those symbols *call*, whose
  only consumer moves to `_setup.py`:

  | Patched name | Sole consumer | Patch sites |
  |---|---|---|
  | `require_langchain_history` | `_resolve_session_id` | `tests/llm/providers/langchain/conftest.py`, the `skip_langchain_history_guard` fixture |
  | `get_config_values` | `_load_langchain_config` | `tests/llm/providers/langchain/test_langchain_provider.py`, 5 sites |

  **Re-point those ~6 patch strings at `…langchain._setup.<name>`.** Re-exporting them from
  `__init__.py` instead is the trap: the patch then succeeds and **silently no-ops**, because
  `_setup.py` resolves the name through its own globals. Nothing fails loudly — the resume guard
  really runs against synthetic session ids, and `_load_langchain_config` reads the developer's
  real `config.toml`. Deleting them without re-pointing at least fails honestly, with
  `AttributeError`.
* Move the imports the block needs (`uuid`, `Mapping`, `get_config_values`,
  `require_langchain_history`, `validate`, the `._exceptions` names, the `TYPE_CHECKING`
  `BaseChatModel`) and delete the ones `__init__.py` no longer uses. `_setup.py` gets its own
  `logger = logging.getLogger(__name__)` — `_load_langchain_config`'s warning is the only user.
* **Do not** rename anything, change a signature, reflow a docstring, or "improve" the moved code.
  A reviewer must be able to diff the two halves and see a move.

## DATA

No behaviour, no types, no public API change. `__init__.py` lands at roughly **525** lines, so it
is still under 600 after Step 7's additions.

## TESTS

**None new,** and exactly two files edited — the re-pointed patch strings from HOW:

* `tests/llm/providers/langchain/conftest.py` — `require_langchain_history` →
  `…langchain._setup.require_langchain_history` (one string; it feeds the
  `skip_langchain_history_guard` fixture, which 9 tests across `test_langchain_agent_mode.py`,
  `test_langchain_multi_turn.py`, `test_langchain_provider.py` and `test_langchain_streaming.py`
  request — none of those files changes).
* `tests/llm/providers/langchain/test_langchain_provider.py` — the 5 `get_config_values` patch
  strings → `…langchain._setup.get_config_values`.

No assertion, fixture body or test name changes; only the patch target string. **No other test may
need an edit** — if one does, the move was not pure, so revert and rethink rather than fixing the
test.

## CHECKS

`run_pylint_check`, `run_mypy_check`, `run_pytest_check` (fast selection),
`run_lint_imports_check`, **and the file-size gate**
(`check_file_size(max_lines=750)` must not list `llm/providers/langchain/__init__.py`) — all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§4 and §5) and `pr_info/steps/step_1.md`, then implement Step 1
> only.
>
> Create `src/mcp_coder/llm/providers/langchain/_setup.py` and move `_build_system_messages`,
> `_BACKEND_ERROR_PARAMS`, `_auth_errors_for_backend`, `_handle_provider_error`,
> `_load_langchain_config`, `_create_chat_model` and `_resolve_session_id` into it **verbatim**.
> Re-export them from `__init__.py` and leave every call site there, so the existing
> `mcp_coder.llm.providers.langchain._load_langchain_config` / `._create_chat_model` patches in 21
> test modules keep working.
>
> Two *consumed* names the re-export cannot protect are patched today, because their only consumer
> moves: **re-point** `require_langchain_history` (`tests/llm/providers/langchain/conftest.py`) and
> the five `get_config_values` strings
> (`tests/llm/providers/langchain/test_langchain_provider.py`) at `…langchain._setup.<name>`.
> Re-exporting those two instead makes both patches silently no-op against the real guard and the
> real `config.toml` — see step_1.md HOW. Those two patch strings are the **only** permitted test
> edit; anything else means the move was not pure.
>
> Otherwise this is a pure move: no rename, no signature change, no new tests, no behaviour change.
>
> The point is the CI file-size gate (`--max-lines 750`): the file is at 739 and Step 7 adds ~60.
> Do **not** add it to `.large-files-allowlist`.
>
> Use MCP tools only. Finish with `run_pylint_check`, `run_pytest_check`, `run_mypy_check`,
> `run_lint_imports_check` and `check_file_size(max_lines=750)` all green, then one commit.
