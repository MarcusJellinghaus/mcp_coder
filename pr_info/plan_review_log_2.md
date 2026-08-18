# review-plan review log 2

Supervised plan review for issue #1116 — LangChain backend: icoder multiple-system-message
bug + path convergence.

Context at start: CI green, branch up to date with `main`, task tracker not yet populated,
GitHub label `status-14f:plan-review-failed` (automated run in `plan_review_log_1.md`
exhausted its rounds at round 4 with verdict `tasks`).

## Round 1 — 2026-08-18

**Findings**:
- `pr_info/steps/step_6.md:58` — medium — the end-to-end icoder test's patch list is incomplete: with `tools=None`, `run_agent_stream` first calls `_load_mcp_server_config` (reads a real JSON file) and then `MultiServerMCPClient(...)`, so the test as written cannot run.
- `pr_info/steps/step_5.md:161` — medium — `test_langchain_agent_system_messages.py` instructions cover only the `ainvoke`→`astream_events` mock swap, but all three tests call `run_agent(...)` without `session_id` (which step 5 makes required → `TypeError`) and would then reach the now-internal real `store_langchain_history`, writing session JSON into the user's real app-data directory. Same `store_langchain_history` omission for `test_langchain_agent_usage.py`.
- `pr_info/steps/step_4.md:72` — medium — "Copy, do not move" duplicates ~45 lines for one commit purely to keep `run_agent` green, and pushes `agent.py` from 698 to ~737 against the enforced 750-line limit. Extracting `_summarize_messages` once and calling it from both paths achieves the same green-at-every-step property without duplication.
- `pr_info/steps/step_4.md:132-135` — low — the drainer-only argument used to strip `done["messages"]` at the `_ask_agent_stream` boundary applies equally to `done["stats"]`, whose `tool_trace` is re-persisted into `raw_response["events"]` and the icoder JSONL log alongside the existing `tool_result` events.
- `pr_info/steps/summary.md:198` — low — the Modified table row for `test_langchain_agent_system_messages.py` says "Merged assertions", contradicting `step_2.md:66` ("needs **no** change here") and `step_5.md:161-167` (mock-shape changes only).

Verified as correct (not findings): all of the plan's factual code claims, including every round-1/round-2 fix from `plan_review_log_1.md` (usage-source change, `accumulated_text` fallback, `messages` boundary strip, resume-path system stripping, timeout-scope change); `.importlinter` wildcards already cover `_messages.py`; pylint disables `R` checks so temporary duplication would not trip `duplicate-code`.

**Decisions**: All five findings accepted — every one is a technical correction (test cannot run / tests write to the user's real app data / avoidable duplication against a hard file-size limit / cross-file contradiction), none touches scope or the issue's Decisions table. No escalation to the user.
- Finding 1: engineer to verify the real `ask_langchain_stream` signature and prefer `tools=[]` if it short-circuits MCP loading, else explicit patches.
- Finding 3: accepted the extract-once form; duplication avoidance is an explicit repo principle and the size headroom argument seals it.
- Finding 4: decided **strip `done["stats"]` too**, in the same shallow copy as `messages` — nothing above the provider boundary reads it, `tool_trace` duplicates content already emitted as tool events, and one strip site for both keys preserves the "no per-consumer filtering" property this issue exists to establish.

**User decisions**: none — no design, scope or requirements question arose.

**Changes**:
- `pr_info/steps/step_4.md` — "Copy, do not move" replaced with "Extract once, call from both": `_summarize_messages` is extracted once and called from both `run_agent` and `run_agent_stream`, `stats` now carries `usage`, and `run_agent_stream` overrides it with its `on_chat_model_end` accumulator. Added the deferred-import split, removal of `run_agent`'s now-unused imports, and the intermediate `agent.py` size expectation (~700 vs ~737 against the 750 limit). `done` payload contract, DATA and the LLM prompt updated for the `stats` strip; test item 11 renamed to `..._strips_messages_and_stats_from_done`; new test item 13 pins extraction parity; store-patch note added to test item 12.
- `pr_info/steps/step_5.md` — deletion list corrected (step 4 already replaced the inline loop with a `_summarize_messages` call); `test_langchain_agent_usage.py` and `test_langchain_agent_system_messages.py` gained explicit `session_id=` and `store_langchain_history` patch instructions; added a step-wide storage-patch rule naming which files need it and which are exempt.
- `pr_info/steps/step_6.md` — end-to-end test now drives `ask_langchain_stream(tools=[])`, verified against the real call chain (`__init__.py:591` → `:494` → `agent.py:525`) to skip `_load_mcp_server_config` and `MultiServerMCPClient`; patch set pinned to exactly four; the nonexistent `/tmp/mcp.json` path removed; unit-level agent test gained a store-mock patch; a stale sentence claiming the text-path test does not exercise the merge corrected.
- `pr_info/steps/summary.md` — §3 and §6 rewritten to match (extract-once, boundary strips `messages` **and** `stats` while `result` deliberately crosses); KISS non-changes and Verified-unchanged blocks realigned; Modified-table rows corrected for `__init__.py`, `agent.py`, `test_langchain_agent_system_messages.py`, `test_langchain_agent_run.py`, `test_langchain_agent_usage.py`; `test_langchain_ollama_agent.py` and `test_langchain_agent_timeout.py` added to Verified-unchanged.
- `pr_info/steps/Decisions.md` — **new**, recording the five decisions from this round.

**Status**: committed (plan changed → another review round follows).

Round 1 commit: `b76d555` (pushed).

## Round 2 — 2026-08-18

**Findings**:
- `pr_info/steps/step_4.md:204` — medium — the step routes 7 new tests into `tests/llm/providers/langchain/test_langchain_agent_streaming.py`, already 656 lines at ~44 lines/test, landing it around 870–970 lines — past the **CI-enforced** 750-line gate (`.github/workflows/ci.yml:109`, and the file is not in `.large-files-allowlist`). Step 4 cannot exit green as written. The plan reasons about this same limit for `agent.py` but never for the test file.
- `pr_info/steps/step_5.md:116` — medium — contradiction introduced by the round-1 edits: the bullet says `TestRunAgentLaunchErrorWrap::test_run_agent_wraps_launch_errors` needs "no change at all", but the same file makes `session_id` a required `run_agent` parameter and states every call site needs it; the test calls `run_agent(...)` without it and would raise `TypeError` instead of `LLMMCPLaunchError`.
- `pr_info/steps/Decisions.md:24`, `pr_info/steps/step_4.md:91` — low — the stated rationale is factually wrong: `W0611 unused-import` **is** disabled in `pyproject.toml` and ruff selects only `D`/`DOC`, so no check would catch leftover imports. The instruction is still right as hygiene; only the "or pylint will fail" justification is false.
- `pr_info/steps/step_4.md:220` — low — the "Tests (write first)" list skips number 7 (jumps 6 → 8), an artifact of the round-1 edits; reads as a silently dropped item.
- `pr_info/steps/step_5.md:19`, `pr_info/steps/summary.md:218` — low — "docstrings only" understates the `tests/icoder/test_icoder_permission_wiring.py` edit: the stale "site 2" wording also appears in the `AssertionError` message body at line 298.

Verified as correct (not findings): every round-1/round-2/round-3 fix is genuinely applied; `tools=[]` really does short-circuit MCP loading (`__init__.py:591` → `:494` → `agent.py:525`); step 6's `get_user_app_data_dir` patch target resolves; `tests/conftest.py` has no app-data isolation fixture, confirming the storage-patch requirement; the langchain-tests `conftest` stub maps unknown types to `HumanMessage`, which is why step 1's filter-before-`messages_from_dict` is right.

**Decisions**: All five accepted — a CI-gate blocker, a self-contradiction, a false rationale and two consistency slips. None touches scope or the Decisions table, so no escalation. Two instructions widened beyond the reported finding: the file-size check must be applied to **every** test file the plan grows (not just the one caught), and the "or pylint will fail" pattern must be corrected wherever else it appears.

**User decisions**: none.

Round 2 commit: `fd651e1` (pushed).

## Round 3 — 2026-08-18

**Findings**:
- `pr_info/steps/step_5.md:~118` — medium — the prescribed `ainvoke` → `astream_events` mock conversion never says the mock **class** must change. Every affected test builds `mock_agent = AsyncMock()`, and `AsyncMock().astream_events(...)` returns a coroutine, which `async for` rejects (`TypeError: 'async for' requires an object with __aiter__`). The working reference `_patch_run_agent_stream` uses `MagicMock()`. Step 5 could not exit green as written.
- `pr_info/steps/step_5.md:~120` — medium — "keep every existing assertion, only the mock setup should change" is wrong for `test_prepends_session_history`, which asserts on `mock_agent.ainvoke.call_args` (`test_langchain_agent_run.py:293`); after the drainer collapse `ainvoke` is never called, so `call_args` is `None` and the test dies with `TypeError`. The step gives the correct `astream_events.call_args` instruction for the sibling file but not here.
- `pr_info/steps/step_4.md:140` — low — stale cross-reference left by the round-2 renumbering: "(see Tests, item 6)" now points at `test_error_persists_nothing`; the item pinning `TestRunAgentStreamUsage` is item 2.
- `pr_info/steps/step_5.md:~40` — low — the "site 2" wording sweep misses two source comments the same change falsifies: `agent.py:293` (`_convert_server_tools` docstring listing `run_agent` as a shared caller) and `agent.py:532` ("inline, same as run_agent").

Verified as correct (not findings): the newly added file-size sweep table — every "Now" number checked against the real files (`test_langchain_agent_streaming.py` 656, `test_langchain_agent_run.py` 493, `test_types.py` 491, `test_icoder_permission_wiring.py` 452, `test_langchain_agent_usage.py` 220, `agent.py` 698, `__init__.py` 685), and the 750-line gate confirmed real at `.github/workflows/ci.yml:106` with none of these files allowlisted. Round-4/5 fixes all landed coherently: step 4's list is contiguous 1–12 with the seven new tests routed to the new file, and `summary.md` / `Decisions.md` / step 4's WHERE agree on the split. `.importlinter` and `tach.toml` need no change for `_messages.py`.

**Decisions**: All four accepted — two would break step 5 at runtime, two are consistency slips. No escalation. Two instructions widened: the `MagicMock` requirement must be swept across **every** step that mocks `astream_events` (step 4 adds seven such tests), and the surviving-`ainvoke`-assertion check must cover all touched test files, not only the one found.

**User decisions**: none.

Round 3 commit: `074256d` (pushed).

## Round 4 — 2026-08-18

**Findings**:
- `pr_info/steps/step_4.md` (mock-class rule paragraph) — low — the scoping claim "tests 1 and 3–8 get this for free via `_patch_run_agent_stream`" does not hold for test 6 (`test_error_persists_nothing`). `_patch_run_agent_stream` hard-wires `astream_events.return_value` to an events **list** and cannot express "raises", so a test needing `astream_events` to raise must hand-roll its patch set the way `test_error_propagation` does with `_RaisingAsyncIter`. Test 6 lands in neither the "free" list nor the "apply explicitly" list, and the generic sentence is scoped to mocks whose `astream_events` returns `async_events(...)` — which test 6's does not.

Verified as correct (not findings), all measured against the real tree: the eleven cited `AsyncMock()` sites are real, complete and correctly attributed, and the two look-alike occurrences are correctly excluded (`test_langchain_agent_run.py:433` never reaches `astream_events` because tool loading raises first; `:364-365` are MCP session mocks). Decision 10's `ainvoke`-assertion list is complete — no other test in the tree asserts on `ainvoke`. The `test_prepends_session_history` retarget works (`call_args[0][0]["messages"]` is unchanged, and `_PATCH_FROM_DICT` is a source-module patch the deferred import picks up). Step 4's "keep passing unchanged" claims hold, including the three `TestRunAgentStreamUsage` tests landing in the no-terminal-event branch. Step 2's merge-safety audit list is complete — no other test asserts on two `SystemMessage`s. File-size sweep numbers re-measured and accurate. Circular-import safety holds; `tach.toml` needs no entry. No contradictions among the rules added in round 3.

**Decisions**: The single finding accepted despite the reviewer's `ready` verdict and its "self-correcting during implementation" argument. Reasoning: the fix is one sentence, whereas the failure it prevents costs an implementer a confusing mid-step failure plus rediscovery of the reference shape — and exiting the loop on a round with a known open finding is worse than paying for one more confirming round. Instruction widened slightly: the generic sentence scoping the rule to mocks returning `async_events(...)` is what let test 6 slip through, so it must be checked and widened to cover the raising case.

**User decisions**: none.

Round 4 commit: `23dc357` (pushed).

## Round 5 — 2026-08-18 (confirming)

**Findings**: none.

Confirmed the round-4 edit is correct and complete: step 4's three mock-class groups cover all twelve test items exactly once and mutually exclusively, and each membership was checked against real code — items 5 and 8 (cancel) are feasible with `_patch_run_agent_stream` because the cancel check sits at the top of the event loop, so the consuming `async for` can set the flag after the first `text_delta` and still get partial text into `accumulated_text`; item 6 genuinely cannot use the helper; item 11 hand-rolls because it must assert on `astream_events.call_args`; the exempt classification holds for 2, 9, 10 and 12. No contradiction between step 4's widened rule and steps 5/6's narrower restatements. `Decisions.md` and `summary.md` agree with `step_4.md`.

Whole-plan sanity pass re-verified every load-bearing claim against the source, including all of step 5's line-number claims (exact), the `_PATCH_FROM_DICT` source-module patch surviving the deferred import in `_messages.py`, `StreamEvent = dict[str, object]` making the three new `done` keys mypy-safe, step 6's `get_user_app_data_dir` patch target resolving, the re-measured file-size figures, and the module-level `pytestmark` that marks step 4's added integration test automatically.

**Decisions**: nothing to accept — zero plan changes this round, so the review loop exits.

**User decisions**: none.

**Status**: no changes needed.

---

## Final Status

**Plan is ready for approval.**

Five supervised rounds; four produced plan changes, the fifth confirmed zero. This follows three earlier
automated rounds recorded in `plan_review_log_1.md`, whose fixes were verified as genuinely applied.

| Round | Findings | Verdict | Commit |
|-------|----------|---------|--------|
| 1 | 5 (3 medium, 2 low) | tasks | `b76d555` |
| 2 | 5 (2 medium, 3 low) | tasks | `fd651e1` |
| 3 | 4 (2 medium, 2 low) | tasks | `074256d` |
| 4 | 1 (low) | ready, fixed anyway | `23dc357` |
| 5 | 0 | ready | — (log only) |

**The findings that mattered.** Three would have stopped an implementation step from exiting green:

* **Round 2** — step 4 routed seven new tests into `test_langchain_agent_streaming.py`, already 656 lines,
  landing it around 950 against the CI-enforced 750-line gate. The tests now go to a new
  `test_langchain_agent_stream_history.py`, and the plan gained a file-size sweep over every test file it
  grows (only that one was at risk).
* **Round 3** — step 5's `ainvoke` → `astream_events` conversion never specified the mock *class*. The
  affected tests build `AsyncMock()`, whose child call returns a coroutine that `async for` rejects, so
  every converted test would have died with `TypeError`. A `MagicMock()` rule is now anchored in step 4 and
  restated wherever a test hand-rolls its patch set.
* **Round 3** — `test_prepends_session_history` asserts on `mock_agent.ainvoke.call_args`, which is `None`
  after the drainer collapse; it was covered by a blanket "keep every existing assertion" instruction.

The remainder were consistency defects of one recurring kind: an edit applied in one place and not its
mirror — a stale table row, a cross-reference pointing at a renumbered item, a rationale citing a lint
rule that is actually disabled. Each round's fix tended to introduce the next round's slip, which is why
the loop ran to a clean confirming round rather than stopping at the first `ready`.

**No design or scope questions arose.** Every finding was a technical correction resolvable against the
issue's Decisions table or `pr_info/steps/Decisions.md`, so nothing was escalated to the user. Three
supervisor decisions were recorded in `Decisions.md` rather than deferred: strip `done["stats"]` alongside
`done["messages"]` at the `_ask_agent_stream` boundary; extract `_summarize_messages` once and call it from
both paths instead of copy-then-delete; and split step 4's new tests into a new file rather than
allowlisting an oversized one.

**Not yet done:** `pr_info/TASK_TRACKER.md` is still unpopulated (filled as step 0 of implementation), and
the GitHub issue still carries `status-14f:plan-review-failed` from the earlier automated run.
