# Decisions

Decisions taken outside the step files, in the order they were made.

## 2026-08-30 — plan review round 3 (tech lead)

### D-A1 — Preparatory extraction commits, not the allowlist

`ui/app.py` (740) and `llm/providers/langchain/__init__.py` (739) are within 11 lines of the CI
`--max-lines 750` file-size gate, and this plan adds ~50 and ~60 lines to them. **Decided: add two
behaviour-neutral extraction steps at the front of the plan rather than adding either file to
`.large-files-allowlist`** — the allowlist is grandfathering to be reduced (#353), not an escape
hatch. The file-size gate is also added to the standing constraints and to the CHECKS of every
step that touches those files; it was absent from the whole plan.

Extraction targets chosen while writing the plan (the tech lead named the consumer loop and
`_stream_llm` as candidates and left the final choice to a read of the source):

* **Step 1 — `llm/providers/langchain/_setup.py`**, holding `_build_system_messages`,
  `_BACKEND_ERROR_PARAMS`, `_auth_errors_for_backend`, `_handle_provider_error`,
  `_load_langchain_config`, `_create_chat_model`, `_resolve_session_id`. *Not* `_ask_agent_stream`:
  the consumer loop is the file's top layer and calls two of those helpers, so a module holding it
  would have to import its own parent package back. Moving the bottom layer has no cycle and frees
  ~220 lines instead of ~130. Call sites stay in `__init__.py` so the 21 test modules that patch
  `…langchain._load_langchain_config` / `._create_chat_model` keep working unchanged. (See D-F1 for
  the two *consumed* names that re-export does not cover.)
* **Step 2 — `icoder/ui/stream_view.py`**, holding `_stream_llm`, `_handle_stream_event` and the
  output-unit helpers between them, as `StreamViewApp`, a **base class** of `ICoderApp`. A base
  class rather than free functions plus delegators, because `ui/replay.py` and the pilot tests
  reach seven of those members by name and delegator stubs would eat the headroom back.

### D-A2 — The resolver's runtime short-circuit is bounded by the *winning* authored rule

`step_5.md` / summary §2.4 bounded the runtime group short-circuit on "any matching authored
`never`". **Decided: sort the authored candidates by the existing 4-key ordering and skip the
short-circuit only when the top one is `never`.** With "any", a config holding a broad
`"never": ["mcp__s__*"]` alongside a specific `"ask": ["mcp__s__t"]` skips the short-circuit, the
`ask` then beats a runtime `always` on `Policy.rank`, and the `scope=session` grant silently never
takes effect — contradicting the issue's own acceptance criterion. Test case 4b covers that shape.

### D-B — Applied fixes (no alternatives weighed)

1. `step_4.md`'s LLM PROMPT said `attach`/`detach` run "after a join that may expire"; corrected to
   "before the `thread.join(timeout=5)`, while the agent loop is still live". The prompt dictates
   the mandated `ApprovalEngine` docstring, so the wrong rationale would have shipped in code.
2. Step 3's harness mechanics rewritten onto the working precedent at
   `tests/icoder/test_icoder_permission_wiring.py`: `pytest.importorskip`, langchain imports and
   the `BaseChatModel` subclass all go **inside a function**. A module-level guard is defeated by
   CI's `isort --float-to-top`, and a module-scope subclass trips `disallow_subclassing_any` in the
   CI mypy job, which installs no langchain.
3. The engine's fail-closed deny carries its own `_DENY_UNAVAILABLE` reason, so the gateway does
   not report "denied by the user" for a call nobody was asked about.
4. Integration case 7 (`_DENY_NO_UI` wording asserted from an llm-layer test) removed as redundant
   — nothing on that path produces the UI auto-deny, and Steps 6/9 already cover
   `decision.reason`.
5. `detach()`'s `call_soon_threadsafe` is guarded against a closed loop: the `finally` it runs in
   must not raise, and a closed loop means nothing is parked.
6. Summary §2.3's premise that the consumer "stays suspended at `yield` for the entire open-modal
   window" corrected. `_handle_stream_event` is synchronous and `push_screen` returns immediately,
   so the window is a `call_from_thread` round-trip. The conclusion (`GeneratorExit` with an
   approval pending is reachable) stands, and the `break` on `_cancel_event` is a second way in.
7. Stale line anchors replaced with symbol references rather than refreshed numbers — Steps 1–2
   move ~440 lines, so any number re-verified today is wrong by the time those steps run. This
   matches the plan's own standing constraint.
8. `_TRANSIENT_EVENT_TYPES` renamed `TRANSIENT_EVENT_TYPES`: `AppCore` imports it cross-module.
9. Summary's modified-files table gained `tests/icoder/test_icoder_permission_wiring.py` and
   `tests/llm/test_types.py`.
10. Old Step 8 split into **Step 10** (shutdown hook + closed-app guard, 2 pilot tests) and
    **Step 11** (end-to-end integration test + spike deletion), per "one step = one commit".
    The spike deletion rides with Step 11 because it is only safe once every step meant to carry
    the `FINDINGS.md` rationale has landed.

## 2026-08-30 — plan review round 4 (tech lead)

### D-F1 — Step 1 re-points the two orphaned patch strings, and says so

Step 1's re-export protects patches on the symbols it *moves*, but not on the names those symbols
*consume*. Two are patched today and lose their only `__init__.py` consumer to `_setup.py`:
`require_langchain_history` (consumed by `_resolve_session_id`, patched by the
`skip_langchain_history_guard` fixture in `tests/llm/providers/langchain/conftest.py`) and
`get_config_values` (consumed by `_load_langchain_config`, patched at 5 sites in
`test_langchain_provider.py`).

Weighed: re-export those two names as well, versus re-point the ~6 patch strings at
`…langchain._setup.<name>`. **Decided: re-point.** Re-exporting is the worse failure of the two —
the patch still binds, but `_setup.py` resolves the name through its own globals, so both patches
silently no-op: the resume guard would really run against synthetic session ids and
`_load_langchain_config` would read the developer's real `config.toml`, with nothing failing loudly.
Deleting the names without re-pointing at least fails honestly, with `AttributeError`.

Consequence: Step 1's TESTS section no longer claims "no test edits". It enumerates these two files
as the only permitted edit — patch-target strings only — and keeps "no other test may need an edit"
as the purity check for everything else.

### D-B2 — Applied fixes (no alternatives weighed)

1. `_update_token_display` added to Step 2's moved set. `_handle_stream_event` calls it on the
   `StreamDone` branch, but it sits below the `_stream_llm`…`_show_error` run the step moved, so
   `StreamViewApp` would not have had the attribute and the step could not have reached green
   CHECKS. It reads only `self._core.token_usage` and `#status-tokens`, and that call is its sole
   caller in the tree.
2. `step_4.md` said the `layered_architecture` ignore entry "belongs in Step 7"; the CLI import
   first appears in **Step 9**, whose WHERE table owns `.importlinter`. Renumbering artifact —
   old step 7 was the wiring step.
3. `step_9.md` pointed at `step_10.md` "test 2" for the `AppCore.resolve_pending` monkeypatch that
   reaches the pending state; that is **test 1** (test 2 is the closed-app guard).
4. `step_8.md` twice named `ui/app.py` as the home of the "no open tool unit" WARN and of
   `_cleanup_orphan_tools`'s callers; after Step 2 both are in `ui/stream_view.py`, as the same
   step's DATA section already said.
5. `step_2.md`'s TESTS section gained `tests/icoder/ui/test_app.py`, which drives
   `_handle_stream_event` directly.
6. Step 1's "five test modules" recounted: **21** modules patch or import the moved names through
   the package namespace. Cosmetic — the re-export covers all of them.
