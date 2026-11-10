# Step 6 — Zombie visibility: name the signal keeping it alive

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_6.md`), then implement Step 6 only. The `INVESTIGATE_ZOMBIE` reason names the winning signal, `status` renders `Running (zombie: <rule>)`, and the zombie wording in `session_restart.py`, `status.py` and the docs is updated. Write the tests first, then the implementation. Run the checks from the summary, then make one commit.

## WHERE / WHAT

**`src/mcp_coder/workflows/vscodeclaude/assessment.py`** (`_decide_unguarded`, zombie branch)
```python
if verdict.active and git_status == "Missing":
    alive = "window still open" if verdict.rule == LivenessRule.TITLE else "process alive"
    return Decision(SessionAction.INVESTIGATE_ZOMBIE, f"folder missing, {alive}", destructive=False)
```

**`src/mcp_coder/workflows/vscodeclaude/status.py`**
- VSCode column: `vscode_status = f"Running (zombie: {assessment.verdict.rule.value})"`.
- Comment at the closed-issue skip (~line 337): "UNLESS the session is still live (zombie state: an open window or a live process for a missing folder — surface it for diagnosis)."

**`src/mcp_coder/workflows/vscodeclaude/session_restart.py`** (active-skip block, ~line 272)
- Comment: drop "(it self-resolves to REMOVE_MISSING once the process exits)". Say that a zombie (window or process still live, folder gone) is kept tracked and warned, never restarted.
- Warning: log the decision reason instead of the hard-coded text:
  ```python
  logger.warning(
      "Zombie session for issue #%d: %s; keeping tracked, not restarting",
      session["issue_number"], assessment.decision.reason,
  )
  ```
- The function docstring ("kept tracked and warned, never restarted") stays.

**`docs/coordinator-vscodeclaude.md`** (Session States)
- One line: a live session whose folder is missing shows `Running (zombie: <rule>)`. With `title` it means the window is still open; close it.

## Tests (write first)

**`test_assessment_layers.py`**
- Zombie reason, parametrized:
  - `make_active(TITLE)` + `"Missing"` → `INVESTIGATE_ZOMBIE`, reason `"folder missing, window still open"`
  - `PID` / `CMDLINE` → `"folder missing, process alive"`
- Adapt any existing assertion on the old reason text.

**`test_status_display_zombie.py`**
- Exact assertion → `"Running (zombie: pid)"` or `"Running (zombie: title)"`, matching how each test builds the zombie.
- Negative assertions currently checking `"(zombie)"` → check `"zombie"`, so they still test something with the new text.

**`test_session_restart_closed_sessions.py`** (or wherever the zombie warning is asserted)
- The warning contains the assessment's decision reason.
- Adapt any assertion on "process alive but folder missing".

## Commit

`feat(vscodeclaude): show which signal keeps a zombie session alive`
