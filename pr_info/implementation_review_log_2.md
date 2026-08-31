# review-implementation review log 2

Issue #1045 — I3.2 Runtime approval engine + two-loop bridge.
Second review run (log 1 held rounds 1–3; round 3 ended dismissed with a rebase pending).

## Round 1 — 2026-08-31

**Findings**:
- `tests/llm/providers/langchain/test_approval_cancel_path.py:125` — medium — the gate wait uses the
  harness default 5.0s deadline, but the probe's measured cost in an idle serial run is 4.66s. Under
  `-n auto` it competes with every other worker and genuinely failed in a full-suite run
  (`AssertionError: the tool never reached its await`). Both R7 tests share `_run_cancel_probe`, so
  the acceptance gate for hard cancel is flaky.
- `src/mcp_coder/icoder/permissions/approval.py:381` — medium — `cancel_all()` calls
  `loop.call_soon_threadsafe` unguarded, while the structurally identical call in `detach()` is
  guarded with a comment documenting exactly this hazard. A Ctrl+C or quit landing between
  `asyncio.run` closing the agent loop and `detach()` nulling `_loop` raises
  `RuntimeError: Event loop is closed` on the Textual thread, uncaught.
- `src/mcp_coder/icoder/permissions/approval.py:303` — low — `_cancelled` is armed by every
  `cancel_all()`, including a cancel with nothing pending. A gated call reached in the gap before the
  consumer breaks its loop takes the fail-closed return and tells the model `_DENY_UNAVAILABLE`,
  inviting a re-plan around a refusal nobody made on a turn the user abandoned.
- `src/mcp_coder/llm/providers/langchain/__init__.py:350` — low — the pause window closes lazily, so
  `paused += now - pause_began` credits the whole wait rather than the real pause: up to 300s of
  over-credit per approval against the 3600s overall cap.
- `src/mcp_coder/icoder/core/app_core.py:40` — low — a module-level gateway import exists only for a
  constructor annotation, while the analogous imports in `llm_service.py` and `llm/interface.py` are
  deliberately under `TYPE_CHECKING`. `AppCore` has the widest import reach of the three.
- `tests/llm/providers/langchain/test_approval_stream_bridge.py` — low —
  `test_detach_runs_when_the_generator_is_closed` sleeps 5.0s, so the production
  `thread.join(timeout=5)` waits it out: 5.04s, the slowest test in the new set, paid on every run.

**Decisions**:
- Accept (flaky acceptance gate), accept (real uncaught `RuntimeError`, 3-line symmetric fix),
  accept (cancel is not a deny — the design says a cancelled turn unwinds), accept (trivial, and
  applied in the widest-reach module), accept (Boy Scout).
- **Skip** the lazy pause-window close: the direction is safe — the cap only loosens — and there is
  no user-visible failure. Precision nit against a safety net; YAGNI.

**Changes**:
- `approval.py` — `request_approval` now raises `asyncio.CancelledError` when the turn is already
  cancelled, and keeps the `_DENY_UNAVAILABLE` fail-closed deny only for a detached engine (verified
  first that the gateway's `AFTER_APPROVAL` branch propagates rather than swallows `CancelledError`);
  `cancel_all()`'s `call_soon_threadsafe` guarded against a closed loop as `detach()` already is.
- `app_core.py`, `llm_service.py` — gateway import moved under `TYPE_CHECKING` in both, so
  `permission_bridge` is off `AppCore`'s runtime path.
- Test timing — cancel-probe deadlines raised to 30s (production's `thread.join(timeout=5)`
  deliberately left alone, it is the acceptance criterion); generator-close sleep 5.0s → 0.2s.
- `tests/icoder/test_permissions_approval.py` — new `test_cancelled_turn_unwinds_instead_of_denying`
  pinning both halves of the split guard.
- `tests/workflows/vscodeclaude/test_assessment_issue_facts.py` — restored main's import formatting.

**Follow-ups found while fixing** (scoped out, recorded here):
- The `TYPE_CHECKING` rationale is weaker than the finding asserted. `src/mcp_coder/__init__.py:45`
  runtime-imports `.llm.providers.langchain.verification`, so the provider package `__init__` is
  executed eagerly regardless; and `permission_bridge` itself defers `langchain_core` into a function
  body. The edit removes one module from the path and its new comments claim only that. The older
  comments in `llm/interface.py` and `approval.py` still carry the disproven package-`__init__`
  rationale — worth correcting alongside whatever scopes `__init__.py:45`. *(Static trace, not
  executed — pytest is unavailable in this workspace.)*
- The isort drift in the vscodeclaude test **is** this branch's. Commit `d706f73` on this branch
  fixed it, calling it "the sole cause of the failing isort CI job"; `f545bac` re-introduced it.
  Now realigned with `origin/main`.

**Verification gap**: `run_pytest_check` reports *"pytest is not available in the configured Python
environment"* for `.venv\Scripts\python.exe` although pytest 8.4.2 is installed there, and
whole-project `run_mypy_check` / `run_pylint_check` time out or never return. Ruff, import-linter
(21/21 kept), file-size, black, and narrowly-scoped pylint/mypy all pass. **Nothing in this round has
been verified by test execution**, including the new test.

**Status**: committed

## Round 2 — 2026-08-31

**Findings**:
- `src/mcp_coder/icoder/permissions/approval.py:317` — medium — **regression introduced by round 1**.
  The new pre-await `raise asyncio.CancelledError` unwinds the turn exactly as cancelling a parked
  future does, but left `_turn_aborted` down. `AppCore.stream_llm`'s R16 gate reads that flag, so it
  did not fire and the turn wrote both `llm_request_end` and `store_session` — replaying with no
  `— Cancelled —` marker while the live UI drew one. That is the precise asymmetry R16 exists to
  forbid, plus a stray session-picker entry.
- `src/mcp_coder/icoder/permissions/approval.py:380` — low — `resolve_pending`'s
  `call_soon_threadsafe` was left as the only unguarded one of the three, after round 1 guarded
  `cancel_all()` and `detach()` had always been guarded.
- `tests/icoder/test_permissions_approval.py` — low — the new `test_cancelled_turn_unwinds_instead_of_denying`
  drives the coroutine with `coro.send(None)` outside any event loop, pinning guard *order* but not
  the raise's behaviour inside `ToolNode` / `astream_events` / `_run`. The R7 real-path probe covers
  only the at-await variant; the shape that now ships raises before any await.
- `tests/icoder/test_app_pilot.py:1704` — low — comment drift: "the real agent thread simply dies on
  the escaping `CancelledError`" stopped being true once `_run` began catching it.

**Decisions**: all four accepted. Skipped the note that `_run_cancel_probe` is paid twice (~4.7s
each) — cosmetic.

**Changes**: `_turn_aborted` set before the raise, with both affected docstrings corrected;
`resolve_pending` guarded to match its two siblings; `_run_cancel_probe` split into
`_drive_probe(tool, on_started=None)` so a new `_run_precancel_probe` could add a real-path
pre-await test; the `test_app_pilot.py` comment rewritten, plus two more instances of the same drift
found in the probe file. Swept every other unwind path for the missing flag — the `detach()`-race
branch correctly leaves it alone, since that teardown never reaches `AppCore`'s gate.

**Status**: committed (`b92ed37`)

## Round 3 — 2026-08-31

Findings came from a dedicated review of the four new approval test files (12 raised, 6 accepted).

**Findings (accepted)**:
- `tests/llm/providers/langchain/test_approval_stream_bridge.py:226,253,313` — medium — overall-cap
  margins of 0.5s/0.3s/0.5s, but production starts its clock before `attach()`, thread construction
  and the `asyncio.run` bootstrap, and that setup is never credited to `paused`. On a loaded box
  under `-n auto` one test dies outright and another raises the *overall* timeout, so its `match=`
  fails.
- `tests/llm/providers/langchain/test_approval_integration.py:701` — low — `assert elapsed < 5.0` is
  the provider's own `thread.join(timeout=5)` budget, so the bug it catches fails by a hair.
- `test_approval_integration.py:698-699` and `test_app_pilot.py:1816` — low — assertions running
  after `detach()` has unconditionally cleared the registry; no behaviour of the code under test can
  fail them, while their messages promise discrimination.
- `src/mcp_coder/icoder/permissions/approval.py:335-338` — low — the production comment claimed
  `cancel_all()` "schedules nothing at all when it reads `_loop` while it is still `None`", but
  `_loop` is bound two statements before the hooked `uuid4()`, so it does schedule.
- `test_approval_stream_bridge.py:111-118` — low — `_FakeBridge` emitted `{"tool"}` where production
  `_payload` emits `{"tool_name", …, "source"}`, documenting a contract that does not exist.
- `test_approval_integration.py:28-30` — medium (latent) — tmp-home isolation was real but
  *inherited*: `_tmp_home` returns early for `langchain_integration`-marked nodes, so adding that
  marker would silently start writing to the developer's real `~/.mcp_coder/`. Isolation is an
  explicit #1045 acceptance criterion.

**Decisions**: six accepted. **Skipped**: the ~5s of fixed sleeps and the restructure of
`test_pause_ending_mid_wait_restarts_the_inactivity_budget`, whose discriminating window is genuinely
fragile — rewriting timing-sensitive tests that cannot be executed locally risks turning green CI red
blind. **Skipped**: the `uuid4`-position coupling of the two race tests (speculative — only bites on
a future refactor). **Skipped**: the coverage gap where `_turn_aborted` inside the post-insert
re-check is never provably the sole writer.

**Changes**: caps widened to 1.5s and 0.9s — **not** the 2.0s/5.0s originally proposed, which the
engineer correctly showed would have made two tests vacuous, since each cap is bounded above by its
own scripted pause; the third (no bridge attached, so the cap participates in nothing) went to 5.0s.
Each docstring now records its ceiling. Threshold dropped to 2.0s; three dead assertions removed and
one `is_attached` check moved before the detach where it discriminates; the comment and its
mirroring test docstring corrected; fake payload aligned key-for-key; tmp-home enforced via a
`_REAL_HOME` assertion at the single choke point — an autouse fixture was tried first but pushed the
module past the 750-line CI gate.

**Status**: committed (`ce1e672`)

## Round 4 — 2026-08-31

**Findings**: none. Convergence round.

The reviewer re-derived and confirmed: the guard order in the `CancelledError`/`_DENY_UNAVAILABLE`
split (and that the detached-but-cancelled combination is unreachable, since `gateway.interceptor`
short-circuits on `not engine.is_attached()` before calling `request_approval`); that `_turn_aborted`
cannot get stuck across turns; that all three `RuntimeError` guards now cover the same hazard on
paths that must not raise; that **none of the three widened caps became vacuous** (`setup + pause`
exceeds each cap unconditionally); that the moved `is_attached` assertion now genuinely
discriminates; and that the `_REAL_HOME` guard is read at import, before any fixture, so it really
does guard the "someone adds the marker later" case.

**Changes**: none.

**Status**: no changes needed

## Final Status

**Converged after 4 rounds** (3 producing changes, round 4 clean). Run 2 of the review; log 1 holds
the earlier three rounds.

**Commits produced**
| SHA | Subject |
|---|---|
| `a9c609f` | Unwind cancelled turns instead of denying them |
| `b92ed37` | fix(approval): mark the turn aborted when a cancelled request raises |
| `ce1e672` | Harden approval tests against timing flakes and dead assertions |

The most consequential finding was in round 2: round 1's own fix introduced a regression. Making
`request_approval` raise `asyncio.CancelledError` on a cancelled turn was correct, but it skipped the
`_turn_aborted` bookkeeping its sibling cancel path performs, leaving R16's gate open so a cancelled
turn still wrote a session record. That is a direct #1045 acceptance-criterion violation, and it
existed only because of a review fix — a good argument for the loop running to convergence rather
than stopping at the first clean-looking round.

**Final checks**
| Check | Result |
|---|---|
| CI (at `ce1e672`) | **PASSED** — this is the authoritative run for tests and mypy strict |
| Rebase | UP_TO_DATE (merge base is `origin/main`'s tip) |
| `run_lint_imports_check` | 21 contracts kept, 0 broken — including the new `iCoder Permissions Leaf Isolation` and the `layered_architecture` CLI→approval entry |
| `run_vulture_check` | Clean, after two false-positive whitelist entries (`on_unmount`, a Textual lifecycle hook; `fake_deny_bridge`, a fixture requested by string via `usefixtures`) |
| `run_ruff_check` | No issues |
| `check_file_size(750)` | All 858 files within limit |
| `run_pylint_check` (scoped) | No issues |

**Local tooling gap — the significant caveat of this run.** Neither `run_pytest_check` nor
`run_mypy_check` could be executed at any point, by any agent:

* `run_pytest_check` reports *"pytest is not available in the configured Python environment"*, but
  pytest 8.4.2 **is** installed in `.venv`. Root cause: the venv has **no pip** (`python -m pip` →
  `No module named pip`), so the tool's availability probe returns a false negative. `python -m
  pytest --version` succeeds. Fix: `.venv/Scripts/python.exe -m ensurepip --upgrade`.
* `run_mypy_check` fails with *"Process timed out after 120 seconds"* — the MCP server's internal
  subprocess cap. Cold-cache mypy over this project exceeds it even with `target_directories`
  narrowed, since imported modules are still checked. Warming `.mypy_cache` once would likely
  restore it.

Consequence: every finding this run was verified by **reading, not execution**, and three agents were
killed by a stall watchdog while waiting on those two tools. **Green CI at `ce1e672` is what actually
verifies the tests and mypy strict**, including the four tests added during this run — among them the
real-path pre-await `CancelledError` probe, whose outcome was genuinely unknown when written (had
langgraph converted a non-suspending raise into an ordinary exception, it would have failed and been
a real finding).

**Recorded follow-ups — deliberately out of scope, not defects to fix here**
1. The lazy pause-window close in `llm/providers/langchain/__init__.py` over-credits up to 300s
   against the 3600s overall cap. Direction is safe (the cap only loosens), but it stops meaning
   "wall clock minus human time" as summary §2.3 states.
2. `src/mcp_coder/__init__.py:45` runtime-imports the langchain provider, so the provider package
   `__init__` runs eagerly regardless — making the package-`__init__` rationale in the older
   `TYPE_CHECKING` comments in `llm/interface.py` and `approval.py` inaccurate. Worth correcting
   together with whatever scopes that import.
3. `test_pause_ending_mid_wait_restarts_the_inactivity_budget` only exercises the `pause_epoch`
   branch when its `queue.Empty` lands inside a 0.7s window; if the consumer starts late it passes
   without testing anything. It cannot fail spuriously, but it can go green while the regression it
   guards is reintroduced. Plus ~5s of fixed sleeps in that module.
4. The two race tests in `test_permissions_approval.py` depend on `uuid4()` being called between the
   `_loop` binding and the registry insert; moving id generation would silently change what they
   exercise.
5. `_turn_aborted` inside the post-insert re-check is not provably the sole writer in any test —
   covering it needs a hook firing while `_loop` is still `None`.
6. `test_approval_integration.py` carries no marker, so six real `create_react_agent` turns run in
   the default fast suite.
