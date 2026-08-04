# Step 6 — FINDINGS.md + CI-ignore confirmation + go/no-go

**Commit:** `spike(i3.1): FINDINGS — go/no-go, recommendations for I3.2`

Read `pr_info/steps/summary.md` first. This step writes the **deliverable**: `FINDINGS.md`. It
synthesises the demonstrated outcomes from Steps 1–5 into concrete recommendations for I3.2,
confirms CI ignores `spikes/` (D8), and records the go/no-go verdict (D10 fallbacks on a negative).
No new mechanic code — this is documentation synthesis, so its "test" is a content checklist, not
an `assert`.

## WHERE

- Create `spikes/i3-1-approval/FINDINGS.md`.

## WHAT — required sections (the acceptance checklist for the doc)

1. **Go/no-go verdict.** Positive if Tier C proved the interceptor coroutine runs on the agent
   loop (D6 identity) and a cross-thread resolve unblocked it. On a **negative**, name and rank the
   D10 fallbacks: (1) langgraph checkpointer + `interrupt()`; (2) `HumanInTheLoopMiddleware` via the
   `langchain` meta-package; (3) out-of-band approval before turn start.
2. **Loop-handle source.** State explicitly: call `asyncio.get_running_loop()` **inside the
   interceptor coroutine**; never reuse a build-time handle captured on the MCPManager daemon loop
   / at gateway construction (with the identity evidence from Steps 1 & 5).
3. **Pause vs keepalives (D1).** The pause mechanism (pending counter, `elapsed − paused`) works
   (Step 3); keepalives rejected because they *arm* the `_AGENT_OVERALL_TIMEOUT` cap (`:524` sits
   inside the consumer loop), pollute the session `.jsonl` / replay (`app_core.py:198`), and add
   interval tuning.
4. **Direct cancel channel (D2).** The three generic paths (`cancel_event`, TUI `_cancel_event`,
   `GeneratorExit`) are inert while blocked; the working unblock is the UI calling the engine
   **directly** to resolve/cancel the Future (pushed, not polled); generic paths work as a backstop
   afterwards. Note the real 5s `thread.join` leaves the thread dead (`is_alive()` False) only once
   the Future resolves.
5. **D7 plumbing shape.** The `ApprovalBridge` threaded
   `prompt_llm_stream → ask_langchain_stream → _ask_agent_stream`, attached/detached per stream in
   `try/finally`; parameter optional (non-iCoder CLI paths). The stale-`q` failure mode to guard
   against.
6. **Side-channel / replay consequence.** The `approval_request` `StreamEvent` reaches the
   interceptor through the existing `q`; every non-`raw_line` event is written to the session
   `.jsonl` at `app_core.py:198` and re-rendered by `ui/replay.py` — I3.2 must account for this.
7. **Textual thread directions for I3.3.** `call_from_thread` marshals *into* Textual;
   `call_soon_threadsafe` marshals *out* to the agent loop — opposite directions. State which thread
   the modal callback runs on so I3.3 does not reach for the wrong one.
8. **D8 consequence.** `spikes/` is neither linted nor type-checked, so anything I3.2 lifts into its
   fixtures must be rewritten to survive `mypy --strict`.
9. **D9 handoff.** I3.2 reads this file, carries the load-bearing rationale into its code
   (docstrings/comments), then deletes `spikes/i3-1-approval/`.

## HOW — CI-ignore confirmation (D8, confirmation only)

Confirm and record — no configuration change:
- `pyproject.toml` `[tool.pytest.ini_options] testpaths = ["tests"]` → `spikes/` never collected.
- CI passes `src tests` explicitly to black/isort/pylint/ruff/mypy (check `.github/workflows/`);
  import-linter/tach/vulture/pycycle run via `tools/*.sh` over `src`/`tests`.

## DATA

- Output is Markdown. Each in-scope gotcha (#1–#5) has a **demonstrated outcome** line
  (works / documented-impossible-with-rationale) — "de-risked" = every mechanic has an outcome,
  not "all green".

## Definition of done

- `spikes/i3-1-approval/FINDINGS.md` exists with all 9 sections populated from the real Step 1–5
  runs; go/no-go stated; CI-ignore confirmed by inspection.
- All five tier scripts still exit 0 (re-run once as a final smoke check).
- Standard `src`/`tests` fast unit suite still green.
