# Decisions

## 2026-10-26 — whole-suite baseline (after implementation run blocked at step 1)

Context: build 2444 blocked because the whole suite collected 6587, not the planned 6463. The
per-file (55) and directory (193) counts matched.

1. **No source line numbers in the plan.** Raised by Marcus ("should we remove line numbers and
   work with symbol names?"). The plan already identifies everything by symbol name and moves it
   with `move_symbol`, so no change was needed.
2. **Drop the hard-coded whole-suite count (6463).** It drifts as `main` moves, and this PR
   cannot change it. Step 1 records the actual count, and step 4 checks it is unchanged.
   Agreed by Marcus by running `/plan_update` on this proposal.
3. **Keep the fixed per-file and directory counts** (55 → 18/21/6/8/2, directory 193). They only
   change if these test files change, and they prove that no test was lost or duplicated.
   Part of the same proposal.
