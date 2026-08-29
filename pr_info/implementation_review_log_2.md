# review-implementation review log 2

Issue #1138 — langchain resume silently starts a blank conversation.

Continues from `implementation_review_log_1.md` (4 rounds; run 1 ended on a rebase handoff).

## Round 1 — 2026-08-29

**Findings** (no critical issues; prior-round fixes from run 1 re-verified as sound):

- `docs/architecture/architecture.md:245` — low — the doc records the resume guard but not the larger contract the branch introduced: `run_agent_stream`'s `done` event is the single decision point for resumability, making `LLMResponseDict["session_id"]` nullable in langchain agent mode. Nothing in `docs/` anchors the `None` guards in `create_plan`, `review` and `rebase`.
- `tests/llm/providers/langchain/test_langchain_agent_stream_history.py:170`, `:240` — low — `test_cancel_done_carries_partial_text` and `test_no_terminal_event_done_carries_streamed_text` reach `langchain_history_exists("s1")` with `Path.home()` unpatched, reading the developer's real `~/.mcp_coder/`. Sibling tests at `:132`, `:255`, `:280` all patch it.
- `src/mcp_coder/llm/providers/langchain/agent.py:697` — low — the function-level `langchain_history_exists` import sits between the tool-stats comment block and the `done` dict that comment explains.
- `docs/cli-reference.md:172` — trivial — `--output-format json` is documented as "includes session_id"; an unrecorded langchain agent turn now emits `session_id: null`.
- `src/mcp_coder/llm/storage/session_storage.py:268-275` — trivial — `require_langchain_history` derives `_langchain_session_path` twice.

**Decisions**: all five accepted — each is bounded, sits in code this branch touched, and fixes either a documented-contract gap or real test isolation. Nothing escalated. The reviewer's scope note (the diff is wider than issue #1138, via rounds 1-3 of run 1) needs no action: it is recorded in `summary.md` under "Known consequences".

**Changes**:

- `docs/architecture/architecture.md` — `run_agent_stream` described as the resumability decision point; two bullets under **Session storage** covering the nullable `session_id` and the three workflow guards.
- `tests/llm/providers/langchain/test_langchain_agent_stream_history.py` — both tests now patch `Path.home` to `tmp_path`.
- `src/mcp_coder/llm/providers/langchain/agent.py` — import moved above the comment block. Kept function-level deliberately: `run_agent_stream` imports `store_langchain_history` locally at `:720` and many tests patch `mcp_coder.llm.storage.session_storage.*`, which only works because the import happens at call time (documented at `test_langchain_multi_turn.py:210`). Hoisting one of the two storage imports would split that convention.
- `docs/cli-reference.md` — qualifies `--output-format json`: an unrecorded langchain agent turn reports `"session_id": null`, which must not be chained into `--session-id`.
- `src/mcp_coder/llm/storage/session_storage.py` — path derived once.

**Quality checks**: pylint clean, mypy clean, ruff clean, pytest 5404 passed / 2 skipped, `check_file_size` within limits.

**Status**: committed

## Round 2 — 2026-08-29

**Findings** (no critical issues; run-1 and round-1 fixes re-verified as sound):

- `docs/architecture/architecture.md:257` — low — the bullet added in `34e1e2b` says all three call sites "keep the previous id and log a warning". Only `rebase.py:344-350` does; `create_plan/core.py:296-313` aborts with a `WorkflowFailure` and `review/core.py:375-405` fails the round. It is the only doc anchor for the nullable contract, so a fourth call site would copy the wrong pattern.
- `tests/llm/providers/langchain/test_langchain_agent_streaming.py:362` — low — `test_cancel_event_stops_stream` is a third instance of the isolation leak fixed in round 1: it stats the developer's real `~/.mcp_coder/sessions/langchain/s1.json` with `Path.home` unpatched.
- `src/mcp_coder/workflows/review/reviewer.py:232` — low — `current_sid = response["session_id"] or current_sid` is the fourth id-chaining site and the one where the rebase pattern fails: `_get_verdict` runs with `supervisor_sid=None` on round 1, so an unrecorded turn leaves `current_sid` `None` and the repair retry at `:236-239` sends `_REPAIR_PROMPT` into a blank conversation — the same silent-blank-continuation class this issue removes. Unlogged and untested.

**Decisions**: all three accepted. #1 is a factual error in the line added last round; #2 completes a fix that missed a sibling; #3 is in scope because it is the defect class the issue targets, at the only chaining site rounds 2-3 of run 1 did not reach. Nothing escalated.

**Changes**:

- `docs/architecture/architecture.md` — the bullet is now a nested list giving each site's actual treatment and why it differs, with a fourth entry for `review/reviewer.py`.
- `tests/llm/providers/langchain/test_langchain_agent_streaming.py` — `Path.home` patched to `tmp_path`.
- `src/mcp_coder/workflows/review/reviewer.py` — module logger added; the blanket `or current_sid` split in two. With a previous id in hand (later rounds) it is kept and a warning logged — the supervisor conversation is genuinely still resumable, so failing would be over-aggressive. With no id at all (round 1, turn not recorded) it logs an error naming the provider and round and returns `(None, None)` before the repair loop, landing on the existing `verdict is None` branch at `core.py:249-259`. That skips the blind retry and stops a parseable-but-sessionless round-1 verdict threading `None` through every later round, with no new plumbing.
- `tests/workflows/review/test_reviewer.py` — three tests: round 1 with no id and an unparseable verdict returns `(None, None)` after exactly one `prompt_llm` call (proving the retries were skipped) and logs the cause; round 1 with no id but a parseable verdict is still abandoned; an unrecorded later turn keeps `supervisor_sid` and returns its verdict.

**Quality checks**: pylint, mypy, ruff, black/isort clean; pytest 5407 passed / 2 skipped; `check_file_size` within limits.

**Status**: committed

## Round 3 — 2026-08-29

**Findings** (no critical issues; the round-2 `reviewer.py` fix re-verified in detail — `current_sid is None` is reachable only on round 1, since a round-1 `(_, None)` always carries `verdict is None`, which `review/core.py:249` turns into an immediate `_fail`, so no later round can enter with `supervisor_sid=None`):

- `tests/llm/providers/langchain/test_langchain_agent_streaming.py` (~10 tests) and `test_langchain_agent_streaming_tool_output.py` (~7 tests) — low — the isolation class rounds 1 and 2 each patched one test at a time is still present in bulk: any test feeding `run_agent_stream` an event list with no `on_chain_end` reaches `langchain_history_exists("s1")` at `agent.py:710` with `Path.home` unpatched. Inert today (read-only stat, no test asserts on `done["session_id"]`), but patching per-test as assertions appear is whack-a-mole.
- `pr_info/implementation_review_log_2.md` untracked while `_log_1.md` is committed — low.

**Decisions**: finding 1 accepted — one autouse fixture closes the class permanently, and it does not disable the resume guard, so it does not hit the objection that ruled out an autouse guard-skip fixture. Finding 2 skipped: the log is committed at the end of the review process by design; the per-round "Status: committed" refers to the code.

**Changes**:

- `tests/llm/providers/langchain/conftest.py` — autouse function-scoped `_tmp_home` fixture pointing `Path.home()` at the test's own `tmp_path`. **`langchain_integration`-marked tests are exempted.** An unconditional redirect would have broken them, but not via history storage: `_require_langchain_config()` → `_load_langchain_config()` reads `~/.mcp_coder/config.toml`, and `get_user_app_data_dir()` resolves `Path.home()` at call time, so `backend`/`model` would come back `None` and every test in `test_langchain_integration.py` would silently `pytest.skip` — disabling the only end-to-end suite that writes and resumes real history. Exempting the marker (rather than scoping the fixture to the two streaming modules) also covers the `langchain_integration` tests in `test_agent_dependencies.py` and `test_mcp_health_check.py`.
- `tests/llm/providers/langchain/test_langchain_agent_stream_history.py` — five per-test `Path.home` patches removed (the two from round 1 plus three originals), leaving one mechanism. `test_no_terminal_event_omits_unresumable_session_id` keeps `tmp_path` for its `rglob` assertion.
- `tests/llm/providers/langchain/test_langchain_agent_streaming.py` — both patches and the now-unused `Path` import removed.

Verified with a throwaway probe (since deleted): `Path.home() == tmp_path` for an unmarked test, `!=` for a marked one, and `require_langchain_history("no-such-session-id")` still raises. `skip_langchain_history_guard` is unchanged and still opt-in; `tests/llm/providers/test_langchain_session_guard.py` is one directory up and out of scope.

Not done: the now-redundant `Path.home` patches at `test_langchain_agent_mode.py:74` and `test_langchain_agent_run.py:196` are left in place — harmless no-ops redirecting to the same `tmp_path`, and removing them is cosmetic churn.

**Quality checks**: pylint, mypy, ruff, black/isort clean; pytest 5407 passed / 2 skipped (identical to the round-2 baseline); `check_file_size` within limits.

**Status**: committed

## Round 4 — 2026-08-29

**Findings**: none. The diff is clean.

The round-3 `_tmp_home` fixture was verified in detail rather than taken on trust:

- *Exemption correct* — `get_user_app_data_dir` resolves `Path.home() / ".mcp_coder"` at call time and is the sole home-resolution point for both `config.toml` and `sessions/langchain/`. No `expanduser` or `HOME` path bypasses the patch, confirming an unconditional redirect really would have turned `test_langchain_integration.py` into silent skips.
- *Exemption complete* — `langchain_integration` appears at three sites in the directory, module-level (`test_langchain_integration.py:25`), function-level (`test_agent_dependencies.py:43`) and class-level (`test_mcp_health_check.py:426`). All three shapes were probed against `request.node.get_closest_marker` and exempt correctly; no subdirectory inherits the conftest.
- *No non-integration test depended on the real home* — the only other `pytest.skip` calls gate on missing packages, not home; config-reading tests patch `get_config_values` / `load_config` / `get_user_app_data_dir` explicitly. Skip count unchanged at 2.
- *Guard unaffected* — `skip_langchain_history_guard` still patches `require_langchain_history` and stays opt-in; `test_langchain_session_guard.py` is one directory up and installs its own `home_dir` redirect. The `test_langchain_integration.py:216-219` seed is still needed and correct.

Spot-checks: `reviewer.py:241-269` — `(non-None verdict, None sid)` confirmed unreachable; `create_plan/core.py:270,296` — `session_id` is bound before anything that could raise past the `except` at `:286`; `agent.py:699-712` — the `done` event is the single decision point and `run_agent`'s 4-tuple relays it verbatim; `LLMResponseDict["session_id"]` is already `str | None`.

**Observation (no change made)**: `--output-format session-id` (`cli/commands/prompt.py:202-206`) is a fifth surface touched by the nullable id — an unrecorded langchain agent turn now logs "No session_id in response" and exits 1 where it previously printed a non-resumable id and exited 0. Strictly correct, code untouched by this branch, and `pr_info/` is removed later in the process, so it was not added to `summary.md`.

**Changes**: none.

**Status**: no changes needed — review loop closed.

## Final Status

**Rounds**: 4 in this run (run 1 contributed 4 more before the rebase handoff). No critical issues were found in any round of run 2; every finding was low or trivial, and no finding reopened an earlier one.

**Commits produced**:

| Commit | Content |
| --- | --- |
| `34e1e2b` | Document the nullable `session_id` contract; tidy the resume guard |
| `6ee18f0` | Fail the review round when the supervisor turn leaves no session |
| `6886886` | Redirect `Path.home` for the whole langchain provider test directory |
| (pins) | Pin `black==26.5.1` and `isort==9.0.1`; apply isort 9.0.1's reformat |

**Supervisor checks**:

- `run_lint_imports_check` — **PASSED**, 21 contracts kept, 0 broken. No architectural violations, nothing escalated.
- `run_vulture_check` — initially 14 hits, all pytest-fixture false positives introduced by this branch (`_tmp_home`, `skip_langchain_history_guard`, `configured_backend`). Added to `vulture_whitelist.py` following the file's existing convention; vulture now reports nothing. Vulture is not wired into CI.

**Out-of-scope work done on this branch, at the user's explicit request**: isort was unpinned at `>=5.12.0`, a range admitting mutually incompatible formatters (5.13.2, 8.0.1 and 9.0.1 each disagree about one test file). CI began running isort 9.0.1 mid-branch and failed on a file this branch never touched. Both formatters are now pinned exactly, both local environments (project `.venv` and the shared Jenkins tool env) were upgraded to isort 9.0.1, and isort 9.0.1's one-line reformat was applied. The black pin caused zero reformatting.
