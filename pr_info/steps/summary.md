# Summary — I3.1 Feasibility spike: interceptor ↔ cross-thread Future (#1044)

## What this is

A **throwaway prototype** proving the in-band approval mechanics before I3.2 (#1045)
builds the production engine. The interceptor coroutine emits a pending-approval marker,
then `await`s a **cross-thread `asyncio.Future`** that a **simulated UI thread** resolves
via `loop.call_soon_threadsafe(...)`. Success is a written **`FINDINGS.md`** telling I3.2
which approach works and which gotchas bit.

**No production code ships from this issue.** Everything lives under `spikes/i3-1-approval/`.
I3.2 reads `FINDINGS.md`, carries the load-bearing rationale into its own code, then deletes
the directory (D9). The go/no-go the spike answers: *does the interceptor's `await future`
run on the agent's `asyncio.run(_run())` loop — distinct from the MCPManager daemon loop —
and can a bare thread resolve it?*

## Architectural / design changes

**There are no changes to production architecture.** This is a deliberate KISS decision:

- **Zero production edits.** The three shipped functions in the D7 chain
  (`prompt_llm_stream` → `ask_langchain_stream` → `_ask_agent_stream`) are **not** modified.
  The D7 approval-bridge seam is *modelled standalone* (Step 4) — D7 says "recorded as a
  recommendation; nothing ships", so a standalone model demonstrates the lifecycle + failure
  mode and yields the recommendation without touching shipped signatures.
- **The real bridge is reconstructed, not re-implemented from scratch.** Tier B (Steps 2–3)
  copies the thread+queue+`join(timeout=5)` consumer from `llm/providers/langchain/__init__.py:479-534`
  *verbatim* so the copy owns a thread handle we can assert `is_alive()` on (§10.3:
  "reconstruct the real join rather than a re-implemented bridge"). The copy is clearly
  labelled as a faithful reproduction of production line ranges (with "navigate by symbol, line
  numbers drift"), and lives in **exactly one place** — `spikes/i3-1-approval/_common.py`, imported
  by Steps 3 and 5. Its fidelity to production is load-bearing, so it is never duplicated.
- **The spike is invisible to CI (D8).** `pytest` is `testpaths = ["tests"]`; CI passes
  `src tests` explicitly to black/isort/pylint/ruff/mypy. So `spikes/` is neither linted nor
  type-checked. **Consequence carried into FINDINGS:** anything I3.2 lifts into its fixtures
  must be rewritten to survive `mypy --strict`.

### Design decisions this plan realises (from the issue)

| ID | Realised by |
|----|-------------|
| D1 pause > keepalives (demonstrated, not recorded) | Step 3 |
| D2 cancel-while-pending is a dedicated direct path | Step 2 |
| D3 three tiers A/B/C | Steps 1 / 2–3 / 5 |
| D4 throwaway FastMCP stdio server in spike dir | Step 5 |
| D5 registry probe (reverse-order, no cross-wiring) | Step 1 |
| D6 loop identity by object | Steps 1, 5 |
| D7 approval-bridge seam modelled standalone | Step 4 |
| D8 confirm CI ignores `spikes/` | Step 6 |
| D9 read-then-delete handoff contract | documented in Step 6 FINDINGS |
| D10 negative go/no-go names+ranks fallbacks | Step 6 FINDINGS |

## Conventions for every spike script

- **Runnable directly**: `python spikes/i3-1-approval/<file>.py`. Exits 0 on success, prints a
  `PASS: <mechanic>` line per demonstrated mechanic, raises `AssertionError` (non-zero exit) on
  failure. The embedded `assert`s **are** the tests (TDD: write the assertions defining success
  first, then the mechanic that satisfies them).
- **Deterministic & repeatable**: fixed sleeps and explicit ordering only; never depend on real
  LLM output or latency for a mechanic assertion.
- **Real installed libraries**: the scripts require the real `langchain` / `langgraph` /
  `langchain-mcp-adapters>=0.3.0` in the venv. **Do not** import the repo's test conftest — it
  swaps in *stub* langchain classes (`tests/llm/providers/langchain/test_langchain_agent_run.py:28`)
  that would silently void the loop-mechanics proof.
- **Loop handle rule (the whole point)**: always obtain the agent-loop handle with
  `asyncio.get_running_loop()` **inside the interceptor/tool coroutine** — never a build-time
  handle captured on the MCPManager daemon loop.

## "Checks passing" for spike steps

Because `spikes/` is outside CI (D8), a step's checks are: (1) the step's script runs to
completion with every `assert` green, deterministically on repeat; and (2) the standard
`src`/`tests` checks remain green — trivially true since **no production files are touched**.
Run the fast unit suite once per step to confirm (2):
`run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])`.

## Files created / modified

**Created (all new):**

```
spikes/                                  (new top-level dir; no prior convention)
spikes/i3-1-approval/
spikes/i3-1-approval/tier_a.py           Step 1 — pure-asyncio microscope
spikes/i3-1-approval/_common.py          Step 2 — shared harness: FakeChatModel, Gate +
                                                  blocking-tool factory, verbatim bridge copy
                                                  (imported by Steps 3 and 5)
spikes/i3-1-approval/tier_b_cancel.py    Step 2 — real bridge: cancel + 5s join
spikes/i3-1-approval/tier_b_pause.py     Step 3 — real bridge: dual timeout + pause
spikes/i3-1-approval/tier_d7_seam.py     Step 4 — D7 approval-bridge seam model
spikes/i3-1-approval/server.py           Step 5 — throwaway FastMCP stdio server
spikes/i3-1-approval/tier_c.py           Step 5 — real MCP + real tool_interceptors
spikes/i3-1-approval/FINDINGS.md         Step 6 — the deliverable
pr_info/steps/summary.md                 this file
pr_info/steps/step_1.md ... step_6.md    the plan
```

**Modified:** none (production code untouched by design).

## Steps at a glance

1. **Tier A** — loop-identity by object (D6), cross-thread Future round-trip, resolve/deny/cancel
   semantics, registry reverse-order probe (D5).
2. **Tier B cancel** — reconstructed real bridge + fake model + blocking tool: three generic
   cancel paths inert while blocked; direct resolve unblocks; the generic paths fire as a
   backstop once resolved; `thread.is_alive() is False` after the real 5s join (#3, D2).
3. **Tier B pause** — reconstructed bridge with pause-aware consumer: pending counter defeats both
   the inactivity `q.get` timeout and the `_AGENT_OVERALL_TIMEOUT` cap, plus a **negative control**
   showing the verbatim (non-pause) consumer dies under identical conditions; keepalives recorded
   as the rejected alternative (#4, D1).
4. **D7 seam** — standalone attach/detach lifecycle across two turns, demonstrating the stale-`q`
   failure mode; recommendation only (D7). Also emits a real `approval_request` event through an
   actual `queue.Queue` from inside the interceptor, proving the side channel is reachable (#2).
5. **Tier C** — throwaway FastMCP stdio server + real `tool_interceptors=[gate]`: assert the real
   interceptor coroutine fired, resume past the gate, deny returns `ToolMessage(status="error")`
   and the agent continues, and the post-`ToolNode` `tool_call_id` is really filled in (#5).
6. **FINDINGS.md** — synthesise works/gotchas/recommendations, confirm CI ignores `spikes/` (D8),
   record go/no-go verdict and, on a negative, name+rank the D10 fallbacks.
