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

- [x] [Step 1: New `mlflow_db_utils.py` — `TrackingStats` dataclass and `query_sqlite_tracking()`](./steps/step_1.md)
- [x] [Step 2: Update `verify_mlflow()` — `since=` parameter and `tracking_data` DB check](./steps/step_2.md)
- [x] [Step 3: Move test prompt to `execute_verify()`; remove it from `verify_langchain()`](./steps/step_3.md)
- [x] [Step 4: Register `llm_integration` marker; remove deprecated test; add E2E integration test](./steps/step_4.md)
- [ ] [Step 5: Add MLflow logging to LangChain text mode (`_log_text_mlflow`)](./steps/step_5.md)
- [ ] [Step 6: Make verify test prompt log to MLflow; restore `since=`](./steps/step_6.md)
- [ ] [Step 7: Add per-server MCP health check to verify](./steps/step_7.md)
- [ ] [Step 8: Add MCP server integration test](./steps/step_8.md)

## Pull Request
