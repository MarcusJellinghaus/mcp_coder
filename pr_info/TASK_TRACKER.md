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

### Step 1: Streaming core additions — `stream_file` + `reason` discriminator + text parity

See [step_1.md](./steps/step_1.md).

- [x] Implementation (tests + production code): `ResponseAssembler` captures `stream_file` into `raw_response`, adds text parity (strip + result-field fallback); `ask_claude_code_cli_stream` emits a first `stream_file` event and tags timeout/nonzero-exit error events with a `reason` discriminator
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Rewrite `ask_claude_code_cli` as the retry-free drain-wrapper

See [step_2.md](./steps/step_2.md).

- [x] Implementation (tests + production code): rewrite `ask_claude_code_cli` over `ask_claude_code_cli_stream` + `ResponseAssembler`; delete `create_response_dict_from_stream`, heartbeat constant, dead MCP guard/parse/file-write; migrate tests; update `docs/architecture/architecture.md`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Timeout sweep — inactivity budgets for every blocking caller

See [step_3.md](./steps/step_3.md).

- [x] Implementation (tests + production code): add `LLM_INACTIVITY_TIMEOUT_SECONDS = 600`, repoint the three tool-using sites, re-document all other blocking callers as inactivity budgets, lower `PROMPT_3_TIMEOUT` 900→600, retire `LLM_IMPLEMENTATION_TIMEOUT_SECONDS`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: `MCP_UNAVAILABLE` category + `mcp_unavailable` label + shared helper

See [step_4.md](./steps/step_4.md).

- [x] Implementation (tests + production code): add `FailureCategory.MCP_UNAVAILABLE`, `mcp_unavailable` label in `labels.json`, new `llm_failures.py` with `llm_failure_reason` + `REASON_TO_CATEGORY`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Categorize timeout / MCP-unavailable at implement + mypy-fix

See [step_5.md](./steps/step_5.md).

- [x] Implementation (tests + production code): categorize the two LLM exceptions in `process_single_task`; stop swallowing them in `check_and_fix_mypy`; add `mcp_unavailable` reason→category branch and wrap final-mypy call in `core.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 6: Categorize at CI sites — CI-analysis propagates, CI-fix absorbs

See [step_6.md](./steps/step_6.md).

- [x] Implementation (tests + production code): make `_run_ci_analysis` re-raise the two LLM exceptions; wrap `check_and_fix_ci` in `core.py` to categorize them; keep `_run_ci_fix` absorbing them (intent comment only)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] Address PR review feedback
- [ ] Write PR summary
