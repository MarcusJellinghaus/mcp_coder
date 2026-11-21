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

### Step 1: Neutral names for the implement check loop — [step_1.md](./steps/step_1.md)
- [x] Implementation (tests + production code)
- [x] Quality checks (format, pylint, mypy, pytest; lint-imports + tach where imports change) — fix all issues
- [x] Commit message prepared

### Step 2: Retire `check_type_hints`; `verify` leftover row — [step_2.md](./steps/step_2.md)
- [x] Implementation (tests + production code)
- [x] Quality checks (format, pylint, mypy, pytest; lint-imports + tach where imports change) — fix all issues
- [x] Commit message prepared

### Step 3: `mcp_servers_of` helper; `rebase_settings` uses it — [step_3.md](./steps/step_3.md)
- [x] Implementation (tests + production code)
- [x] Quality checks (format, pylint, mypy, pytest; lint-imports + tach where imports change) — fix all issues
- [x] Commit message prepared

### Step 4: Required MCP servers: parsing, `verify`, icoder start-up and `/info` — [step_4.md](./steps/step_4.md)
- [x] Implementation (tests + production code)
- [x] Quality checks (format, pylint, mypy, pytest; lint-imports + tach where imports change) — fix all issues
- [x] Commit message prepared

### Step 5: icoder banner and event log show the required servers — [step_5.md](./steps/step_5.md)
- [x] Implementation (tests + production code)
- [x] Quality checks (format, pylint, mypy, pytest; lint-imports + tach where imports change) — fix all issues
- [x] Commit message prepared

### Step 6: Coordinator test templates — [step_6.md](./steps/step_6.md)
- [x] Implementation (tests + production code)
- [x] Quality checks (format, pylint, mypy, pytest; lint-imports + tach where imports change) — fix all issues
- [x] Commit message prepared

### Step 7: `verify` checks every binding — [step_7.md](./steps/step_7.md)
- [x] Implementation (tests + production code)
- [x] Quality checks (format, pylint, mypy, pytest; lint-imports + tach where imports change) — fix all issues
- [x] Commit message prepared

### Step 8: `python` extra; delete the wrapper — [step_8.md](./steps/step_8.md)
- [x] Implementation (tests + production code)
- [x] Quality checks (format, pylint, mypy, pytest; lint-imports + tach where imports change) — fix all issues
- [x] Commit message prepared

### Step 9: Messages for a missing mcp-tools-py (registry hint, ENVIRONMENT row) — [step_9.md](./steps/step_9.md)
- [x] Implementation (tests + production code)
- [x] Quality checks (format, pylint, mypy, pytest; lint-imports + tach where imports change) — fix all issues
- [x] Commit message prepared

### Step 10: Launchers, reinstall hints, `llm/env.py` docstring — [step_10.md](./steps/step_10.md)
- [x] Implementation (tests + production code)
- [x] Quality checks (format, pylint, mypy, pytest; lint-imports + tach where imports change) — fix all issues
- [x] Commit message prepared

### Step 11: No toolkit configured is an error — [step_11.md](./steps/step_11.md)
- [ ] Implementation (tests + production code)
- [ ] Quality checks (format, pylint, mypy, pytest; lint-imports + tach where imports change) — fix all issues
- [ ] Commit message prepared

### Step 12: Docs: toolkits, toolkit interface, migration note, transitional-section links — [step_12.md](./steps/step_12.md)
- [ ] Implementation (docs changes)
- [ ] Quality checks (format, pylint, mypy, pytest) — fix all issues
- [ ] Commit message prepared

### Step 13: Docs: install pages and remaining mentions — [step_13.md](./steps/step_13.md)
- [ ] Implementation (docs changes)
- [ ] Quality checks (format, pylint, mypy, pytest) — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: review the full branch diff against the base branch and address findings
- [ ] PR summary prepared
