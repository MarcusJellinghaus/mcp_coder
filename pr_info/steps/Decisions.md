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
  ~220 lines instead of ~130. Call sites stay in `__init__.py` so the five test modules that patch
  `…langchain._load_langchain_config` / `._create_chat_model` keep working unchanged.
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
