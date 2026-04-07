# Plan Review Log — Issue #628

## Round 1 — 2026-04-07

**Findings**:
- C1: Plan dropped `core/autocomplete_state.py` required by issue spec
- C2: Step 1 tests referenced non-existent `/exit` command
- C3: Step 1 had two contradictory pseudocode blocks for `filter_by_input`
- C4: Step 3 accessed private `_core._registry` / `_core._event_log`
- C5: Step 3 Enter-branch pseudocode had broken variable scoping
- C6: `query_one(CommandAutocomplete)` could raise `NoMatches` on initial load
- C7: `InputArea.insert()` signature ambiguity vs `load_text` + cursor move
- I1: Step 3 too large — 4 concerns in one commit
- I2: `CommandSelected` message decision deferred to implementation time
- I3: `CommandAutocomplete` Static-wrapper over-engineered
- I4: Missing test for backspace within slash (filtered, not re-shown)
- I5: Missing test for typing past a complete match (`/clearx`)
- I6: Snapshot fixture compatibility after Step 5 compose changes unclear
- I7: Backward-compat claim for `InputArea()` no-args had no enforcing test
- I8: `_names` helper referenced but not defined

**Decisions**:
- C1 → Accept via Option D (frozen dataclass + pure `compute_next_state` function in `core/autocomplete_state.py`). User decision.
- C2, C3, C4, C5, C6, C7 → Accept (straightforward fixes)
- I1 → Accept: split Step 3 into 3 smaller commits (new Steps 3/4/5)
- I2 → Accept: drop `CommandSelected` (inline Tab handling in InputArea)
- I3 → Accept: `CommandAutocomplete` extends `OptionList` directly
- I4, I5, I6, I7 → Accept (missing test coverage, low-cost additions)
- I8 → Moot after C1 (event emission moved out of InputArea lambda)

**User decisions**:
- Q (state class shape): Option D — frozen dataclass `AutocompleteState` + pure function `compute_next_state(input_text, registry) -> AutocompleteState`. Caller diffs prev vs new to emit transition events. Chosen over mutable CommandHistory-style class because state is recomputed per keystroke, not accumulated.
- Q (Tab-insert format): `"/help "` with trailing space (standard autocomplete UX).
- Other user-recommended engineering calls (drop CommandSelected, extend OptionList, public AppCore properties) were accepted autonomously per skill guidance (simpler defaults, non-scope-changing).

**Changes**:
- Created `pr_info/steps/Decisions.md` logging all 5 resolved design decisions
- Fixed `step_1.md`: dropped `/exit`, unified pseudocode
- Rewrote `step_2.md`: OptionList-direct, dropped CommandSelected
- Split old `step_3.md` into new `step_3.md` (pure state module), `step_4.md` (InputArea wiring), `step_5.md` (ICoderApp + AppCore properties)
- Renamed old `step_4.md` → `step_6.md` (pilot tests, added I4/I5 tests)
- Renamed old `step_5.md` → `step_7.md` (snapshot tests, added I6 fixture check)
- Updated `summary.md` file list, step count, decisions table

**Status**: committed
