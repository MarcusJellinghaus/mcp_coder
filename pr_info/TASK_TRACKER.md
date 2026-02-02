# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Extend labels.json with vscodeclaude Metadata
See [step_1.md](./steps/step_1.md) for details.

- [x] Add vscodeclaude object to `status-01:created` label in labels.json
- [x] Add vscodeclaude object to `status-04:plan-review` label in labels.json
- [x] Add vscodeclaude object to `status-07:code-review` label in labels.json
- [x] Add vscodeclaude object to `status-10:pr-created` label in labels.json (with null commands)
- [x] Add schema validation test in test_types.py (`TestLabelsJsonVscodeclaudeMetadata`)
- [x] Run pylint and fix any issues
- [x] Run pytest and verify tests pass
- [x] Run mypy and fix any type errors
- [x] Prepare commit message for Step 1

### Step 2: Update issues.py - Numeric Prefix Sorting
See [step_2.md](./steps/step_2.md) for details.

- [x] Add `import re` to issues.py
- [x] Remove import of `VSCODECLAUDE_PRIORITY` from types.py
- [x] Add `_get_status_priority()` helper function
- [x] Add `_get_vscodeclaude_config()` shared helper function
- [x] Update `_filter_eligible_vscodeclaude_issues()` sorting logic to use numeric prefix
- [x] Add `TestNumericPriorityExtraction` test class in test_issues.py
- [x] Run pylint and fix any issues
- [x] Run pytest and verify tests pass
- [x] Run mypy and fix any type errors
- [x] Prepare commit message for Step 2

### Step 3: Update workspace.py - Config-Based Lookups
See [step_3.md](./steps/step_3.md) for details.

- [x] Remove imports of `HUMAN_ACTION_COMMANDS`, `STATUS_EMOJI` from types.py
- [x] Import `_get_vscodeclaude_config` from issues.py
- [x] Remove `_get_stage_short()` function
- [x] Update `create_workspace_file()` to use config for stage_short
- [x] Update `create_startup_script()` to use config for emoji and commands
- [x] Update `create_status_file()` to use config for emoji
- [x] Update test mocks in test_workspace.py
- [x] Run pylint and fix any issues
- [x] Run pytest and verify tests pass
- [x] Run mypy and fix any type errors
- [x] Prepare commit message for Step 3

### Step 4: Update helpers.py - Config-Based Display Names
See [step_4.md](./steps/step_4.md) for details.

- [x] Remove import of `STAGE_DISPLAY_NAMES` from types.py
- [x] Import `_get_vscodeclaude_config` from issues.py
- [x] Update `get_stage_display_name()` to use config lookup
- [x] Update test mocks in test_helpers.py
- [x] Run pylint and fix any issues
- [x] Run pytest and verify tests pass
- [x] Run mypy and fix any type errors
- [x] Prepare commit message for Step 4

### Step 5: Clean Up types.py and __init__.py
See [step_5.md](./steps/step_5.md) for details.

- [x] Remove `VSCODECLAUDE_PRIORITY` from types.py
- [x] Remove `HUMAN_ACTION_COMMANDS` from types.py
- [x] Remove `STATUS_EMOJI` from types.py
- [x] Remove `STAGE_DISPLAY_NAMES` from types.py
- [x] Remove 4 constant exports from __init__.py
- [x] Verify no remaining imports of removed constants in src/
- [x] Run pylint and fix any issues
- [x] Run pytest and verify tests pass
- [x] Run mypy and fix any type errors
- [x] Prepare commit message for Step 5

### Step 6: Final Test Cleanup and Verification
See [step_6.md](./steps/step_6.md) for details.

- [x] Remove constant assertion tests from test_types.py
- [x] Remove unused constant imports from test_helpers.py
- [x] Verify all vscodeclaude tests pass
- [x] Verify no remaining imports of removed constants in tests/
- [x] Verify module exports work correctly
- [x] Verify removed exports raise ImportError
- [x] Run full pytest suite
- [x] Run pylint and fix any issues
- [x] Run mypy and fix any type errors
- [x] Prepare commit message for Step 6

---

## Pull Request

- [ ] Review all acceptance criteria are met
- [ ] Verify labels.json contains vscodeclaude object for all 4 human_action labels
- [ ] Verify types.py no longer has hardcoded label lists
- [ ] Verify constants removed from __init__.py exports
- [ ] Verify all vscodeclaude functionality works identically
- [ ] Verify adding a new human_action label only requires updating labels.json
- [ ] Prepare PR summary
- [ ] Create Pull Request
