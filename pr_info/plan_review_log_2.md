# Plan review log 2 — issue #1045 (I3.2 Runtime approval engine + two-loop bridge)

Run 2. Run 1 (`plan_review_log_1.md`) completed 5 rounds.
Branch rebased onto `main` at `268eff9` before this run.

**Environment note:** `pytest` and `pylint` are not importable in `.venv`; `mypy` times out.
`black`/`isort` work. Review is static only — no probes were runnable this run.

---

## Round 1 — 2026-08-30 (static review at `d706f73`, rebased onto `main` `268eff9`)

Verified by reading source at HEAD: `llm/providers/langchain/__init__.py::_ask_agent_stream`,
`agent.py::run_agent_stream`, `icoder/permissions/{gateway,resolver,model}.py`,
`icoder/core/app_core.py`, `icoder/ui/app.py`, `llm/formatting/{stream_renderer,render_actions}.py`,
`llm/{types,interface}.py`, `icoder/services/llm_service.py`, `cli/commands/icoder.py`,
`.importlinter`, `.large-files-allowlist`, `.github/workflows/ci.yml`,
`tests/llm/providers/langchain/conftest.py`.

**Findings**

`pr_info/steps/step_5.md:51` — high — Step 5 cannot leave CI green: the file-size gate.
`src/mcp_coder/llm/providers/langchain/__init__.py` is **739** lines against the CI-enforced
750-line limit (`.github/workflows/ci.yml:107`, `mcp-coder check file-size --max-lines 750
--allowlist-file .large-files-allowlist`), and it is **not** in `.large-files-allowlist`. Step 5
adds the bridge parameter and its docstring, the guarded attach/detach `finally`, `_sync_pause`,
`_elapsed`, the `pause_epoch` snapshot/re-wait logic, `except asyncio.CancelledError` in `_run`,
and the mandated D9 rationale comments — conservatively +60 lines, i.e. ~800. No step plans a
split, and `check_file_size` appears in no step's CHECKS nor in summary §5's standing constraints.

`pr_info/steps/step_7.md:90` — high — same gate on `src/mcp_coder/icoder/ui/app.py`, at **740**
lines and also not allowlisted. Step 6 (`_open_tool_units` rework), Step 7 (`approval_request`
branch + `_DENY_NO_UI` + `TODO(#1046)` comments + cancel channel) and Step 8 (`on_unmount` +
`_call_from_thread_if_running` + rerouting ~10 `call_from_thread` call sites) all add to it —
roughly +50 across the three commits. Steps 7 and 8 as written both break the gate.

`pr_info/steps/step_2.md:204` — medium — internal contradiction with the round-2 fix. The HOW
section (`step_2.md:79-82`) and summary §2.2/§2.10 now state that `detach()` runs **before**
`thread.join(timeout=5)`; the LLM PROMPT still says "`attach`/`detach` on the consumer thread
**after a join that may expire**". The prompt is what dictates the mandated `ApprovalEngine`
docstring, so the implementation would ship the superseded rationale.

`pr_info/steps/step_1.md:67` — medium — Step 1's harness/probe mechanics collide with two repo
checks and have no precedent here. (a) A **module-level** `pytest.importorskip` is used nowhere in
this repo, and CI runs `isort --check --profile=black --float-to-top`, which floats imports above
module-level statements — so the guard would end up *below* the `approval_harness` import and an
absent langchain would produce a collection `ImportError` instead of a skip. (b) `class
FakeChatModel(BaseChatModel)` at module scope fails `mypy --strict` in the CI mypy job, which
installs only `.[typecheck]` (no langchain), so `BaseChatModel` is `Any` and
`disallow_subclassing_any` fires. The working precedent is
`tests/icoder/test_icoder_permission_wiring.py:511-543`: in-function `importorskip`, in-function
langchain imports, `# type: ignore[misc]` on the subclass, `# pylint: disable=import-error`.

`pr_info/steps/step_3.md:28` — medium — unchanged since rounds 3-5, verified still present against
`resolver._resolve_config` at HEAD. `authored_never` triggers on *any* matching authored `never`,
including a broad one that would lose the specificity contest. With `"never": ["mcp__s__*"]` plus
`"ask": ["mcp__s__t"]`, a `scope=session` grant on `mcp__s__t` is silently discarded (runtime group
skipped, authored `ask` then wins on `Policy.rank`) and the user is re-prompted every turn. Key the
bound on an authored `never` that would actually win.

`pr_info/steps/step_2.md:98` — medium — unchanged since rounds 3-5. The engine's fail-closed
`ApprovalDecision("deny", "once")` carries no `reason`, so `gateway.py`'s `approved.reason or
_DENY_USER` (`step_4.md:84`) tells the model "Tool call denied by the user. Do not retry this
call…" although nobody was asked. Reachable after `cancel_all()` sets `_cancelled` while a parallel
tool call enters the interceptor with `is_attached()` still true.

`pr_info/steps/step_8.md:99` — medium — unchanged since rounds 3-5. Integration case 7 asserts the
`ui/app.py` `_DENY_NO_UI` wording from a `tests/llm/providers/langchain/` module that drives
`_ask_agent_stream` with no UI in the loop, so it can only restate "the gateway honours
`decision.reason`" (already Step 4 test 2b and Step 7 test 8) while pulling `icoder.ui.app` into an
llm-layer test.

`pr_info/steps/step_2.md:135` — low — `detach()` calls `loop.call_soon_threadsafe(entry.future.cancel)`
with no guard against a closed loop. On abnormal teardown (the agent thread's `asyncio.run` closing
while the consumer detaches with a non-empty registry) this raises `RuntimeError: Event loop is
closed` out of the `finally` that summary §2.10 requires cannot raise. Wrap it.

`pr_info/steps/summary.md:97` — low — the claim that under I3.3 the consumer stays suspended at the
`yield` "for the entire open-modal window" is unverified and probably false: `_handle_stream_event`
is synchronous, so it would `push_screen(modal, callback)` and return at once. The conclusion it
supports (GeneratorExit *is* reachable while pending, via an exception in the UI handler) holds
regardless — only the premise is wrong.

`pr_info/steps/step_5.md:52` — low — stale line anchors after the rebase: `q` is at
`__init__.py:549` and the `try:` at `:581` (not 557/590); `_cancel_event` is checked at
`ui/app.py:292`, not `:290` (`step_7.md:13`). `ui/app.py:313` and `output_log.py:528` still hold.
The 33-line gap is now 32.

`pr_info/steps/step_5.md:25` — low — `_TRANSIENT_EVENT_TYPES` is underscore-private yet imported
across modules by `AppCore` (`step_7.md:75`). Drop the underscore.

`pr_info/steps/summary.md:294` — low — unchanged since round 1: the modified-files table still
omits `tests/icoder/test_icoder_permission_wiring.py` (`step_7.md:30`) and `tests/llm/test_types.py`
(`step_5.md:19`).

`pr_info/steps/step_8.md:1` — low — Step 8 still bundles three unrelated concerns in one commit
(shutdown hook + closed-app guard; seven integration tests plus two pilot tests; the spike
deletion). The spike deletion is cleanup that would make a clean separate commit.

**Not findings (verified sound):** acceptance-criteria coverage is essentially complete across the
eight steps; no step ships a broken intermediate state (Steps 3-6 are behaviour-neutral without the
Step 7 wiring); R6's layering argument holds (`llm/types.py` has no third-party imports, so
`approval_bridge` reaches no `langchain_*`); R12 is satisfied by the existing autouse `_tmp_home`
fixture in `tests/llm/providers/langchain/conftest.py`; R18's premise about `tool_call_id` is
confirmed at `agent.py:599` vs `:613`; no new `pyproject.toml` dependency is required.

## Round 1 — 2026-08-30

**Findings**:
- high — `step_5.md:51` / `step_7.md:90`: CI runs `check file-size --max-lines 750`. `ui/app.py` is 740 lines and `langchain/__init__.py` 739, neither allowlisted; the plan adds ~+60 and ~+50. Steps 5, 7 and 8 would each fail. The gate appears nowhere in the plan.
- medium — `step_2.md:204`: the LLM PROMPT still says attach/detach run "after a join that may expire", contradicting the corrected `detach()`-before-join rationale. The prompt dictates the mandated `ApprovalEngine` docstring.
- medium — `step_1.md:67`: module-level `pytest.importorskip` is defeated by isort `--float-to-top`, and module-scope `class FakeChatModel(BaseChatModel)` fails `mypy --strict` in the CI typecheck env (no langchain → `Any` → `disallow_subclassing_any`).
- medium — `step_3.md:28`: `authored_never` triggers on any matching authored `never`, including one that loses the contest, silently voiding a `scope=session` grant. Raised in rounds 3–5 of run 1, never applied.
- medium — `step_2.md:98`: engine fail-closed deny carries no `reason`, so the gateway reports "denied by the user" when nobody was asked. Raised rounds 3–5 of run 1.
- medium — `step_8.md:99`: integration case 7 asserts UI wording from an llm-layer test with no UI in the loop; redundant with Step 4 test 2b and Step 7 test 8.
- low — `step_2.md:135` unguarded `call_soon_threadsafe` in a `finally` that must not raise; `summary.md:97` false "suspended at yield" premise; stale post-rebase anchors; `_TRANSIENT_EVENT_TYPES` private but imported cross-module; modified-files table omissions; Step 8 oversized.

**Decisions**:
- Escalated the file-size gate and the `authored_never` bound to the user; accepted the other ten as straightforward fixes.

**User decisions**:
- **D-A1 — file-size gate: option A.** Add preparatory extraction commits rather than allowlist entries (#353 treats the allowlist as grandfathering to be reduced).
- **D-A2 — `authored_never` bound: option A.** Key the bound on the *winning* authored candidate, not any match, so a broad `never` beside a specific `ask` no longer voids a session grant.

**Changes**:
Plan renumbered to 11 steps: two prep extractions added at the front (`langchain/_setup.py`, `icoder/ui/stream_view.py`), old Step 8 split into shutdown-hook and integration/cleanup steps. File-size gate added to §5 and to per-step CHECKS. A2 implemented via a lifted `_rule_sort_key` plus test 4b. All ten straightforward fixes applied. New `pr_info/steps/Decisions.md` records D-A1/D-A2.

Engineer deviations from the instructions, both accepted:
- Step 1 extracts the config/model/error block, not the consumer loop — `_ask_agent_stream` calls two symbols defined above it, so the consumer loop would import its own parent package back. The chosen block is cycle-free and frees ~220 lines instead of ~130.
- Step 2 is a base-class split rather than free functions plus delegators; `ui/replay.py` and the pilot tests reach seven moved members by name, and delegators would return the headroom.

**Status**: committed

## Round 2 — 2026-08-30

Reviewed at `8b298c3`, aimed hardest at the two prep-extraction steps added in round 1 — the only
unreviewed work in the plan.

**Findings**:
- high — `step_1.md:43-49`, `:66-68`: the "no test edits" promise is false. The re-export protects the *moved* symbols but not the names they **consume**. `require_langchain_history` (consumed by `_resolve_session_id`) and `get_config_values` (consumed by `_load_langchain_config`) are both patched today and lose their consumer in `__init__.py`. Deleting them raises `AttributeError`; re-exporting them makes the patches silently no-op — the history guard really runs and the developer's real config is read. The step's "if a test needs an edit, revert and rethink" line would then send the implementer into a revert loop on a sound move.
- high — `step_2.md:29-38`: `_handle_stream_event` calls `self._update_token_display()`, which sits outside the moved range, so `StreamViewApp` would lack the attribute — `mypy --strict` and pylint `no-member` both fail and the step cannot reach green CHECKS.
- low — `step_4.md:80` names Step 7 for the `layered_architecture` entry; the CLI import appears in Step 9 (renumbering artifact). An unmatched `ignore_imports` entry can fail the run.
- low — `step_9.md:128` points at `step_10.md` test 2; the pending-state monkeypatch is test 1.
- low — `step_1.md:46-49` undercounts the affected test modules.
- low — `step_8.md:63` still says `ui/app.py` for the "no open tool unit" WARN; after Step 2 it is `ui/stream_view.py`.
- low — `step_2.md:67-69` omits `tests/icoder/ui/test_app.py` from TESTS.

Verified sound: both extractions are cycle-free; the headroom is real (both files land ~510-520 and stay
under 750 through Step 10); Step 2's base-class choice is right (`ui/replay.py` reaches exactly the seven
members claimed); the resolver, renderer, `.importlinter` and R5/R16 premises all hold at HEAD; the
renumbering is otherwise clean across all 13 files.

**Decisions**:
- Escalated F1 to the user; accepted the other six as straightforward fixes.

**User decisions**:
- **D-F1 — option A.** Re-point the ~6 patch strings at `…langchain._setup.<name>` and amend Step 1's
  TESTS section to enumerate the two expected edits, rather than shrinking the move to preserve a
  "no test edits" promise. Patch targets are part of what a move relocates; the alternative shapes
  module boundaries around test-patch convenience and would leave the config loader outside `_setup`.

**Changes**:
Step 1 gains the consumed-name table, the re-point instruction, an explicit statement of the
silent-no-op failure mode, and an enumerated TESTS exception. Step 2 moves `_update_token_display`.
Steps 4, 8, 9 and `summary.md` corrected. `Decisions.md` records D-F1.

Engineer corrections to the review's own numbers, all verified against source: the history-guard fixture
is used by **9** tests, not 10; **21** modules reach the moved names through the package namespace, not
5 or 11 (and four of the listed hits patch `verification._load_langchain_config`, a different binding);
and `_update_token_display` has exactly one caller, so leaving it behind would have stranded dead code
rather than merely failing mypy.

**Status**: committed
