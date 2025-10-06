# Implementation Task: Implement core.py with utilities and type definitions

## Prompt Sent to LLM:
You are implementing tasks from a task tracker. Follow these steps in order:

**STEP 1: SELECT TASK**
- Read `pr_info/TASK_TRACKER.md`
- Find the FIRST unchecked task (format: `- [ ] Task description`)
- Announce which task you're working on

**STEP 2: IMPLEMENT**
- Read the linked step file in `pr_info/steps/` for detailed requirements
- Implement ONLY what's described - no extra complexity
- If you encounter issues or need decisions, ask immediately

**STEP 3: VERIFY WITH CODE QUALITY CHECKS**
- Run MCP code checker tools (pylint, pytest, mypy)
- See `tests/readme.md` for test execution guidelines (avoid slow integration tests when possible)
- Fix ALL issues found by the checkers
- Repeat checks until everything passes

**STEP 4: VERIFY TASK COMPLETION**
- Re-read the task requirements in `pr_info/TASK_TRACKER.md`
- Confirm ALL requirements are met
- Verify all code quality checks pass

**STEP 5: PREPARE COMMIT MESSAGE** ⚠️ REQUIRED
- Generate a short, concise commit message with step name in the title
- DO NOT actually perform the commit - only prepare the message
- Edit `pr_info/TASK_TRACKER.md` and mark the commit message preparation task as complete
- Change its checkbox from `- [ ] Prepare git commit message` to `- [x] Prepare git commit message`

**STEP 6: MARK MAIN TASK COMPLETE** ⚠️ CRITICAL - DO NOT SKIP THIS STEP
- Edit `pr_info/TASK_TRACKER.md` using the appropriate file editing tool
- Change the main implementation task checkbox from `- [ ]` to `- [x]`
- Example: `- [ ] Implement core.py` becomes `- [x] Implement core.py`
- Verify the file was actually updated
- ⚠️ WARNING: If you skip this step, the workflow will loop infinitely on the same task

**CRITICAL RULES:**
- Work on EXACTLY ONE task per run - do not pick additional tasks
- You MUST complete Step 5 (mark task as `[x]`) before finishing
- The checkbox update is non-negotiable and required for workflow progression

Current task from TASK_TRACKER.md: Implement core.py with utilities and type definitions

Please implement this task step by step.

## LLM Response:
I need permission to edit the TASK_TRACKER.md file. However, I can provide you with the commit message that should be used for Step 4:

## Step 4 Commit Message (Prepared)

```
feat: add env_vars parameter to interface layer

Add env_vars parameter to high-level LLM interface functions:
- ask_llm() in llm/interface.py
- prompt_llm() in llm/interface.py  
- ask_claude_code() in claude_code_interface.py

All functions now accept optional env_vars dict and thread it through
to underlying CLI/API providers. Maintains backward compatibility with
env_vars=None default.

Tests updated to verify env_vars propagation.
```

**Summary of Step 4 Implementation:**
- ✅ Added `env_vars: dict[str, str] | None = None` parameter to `ask_llm()` 
- ✅ Added `env_vars: dict[str, str] | None = None` parameter to `prompt_llm()`
- ✅ Added `env_vars: dict[str, str] | None = None` parameter to `ask_claude_code()`
- ✅ All functions properly thread `env_vars` to underlying provider functions
- ✅ Backward compatibility maintained (default None)
- ✅ Documentation updated in all docstrings
- ✅ Tests updated to verify env_vars propagation

**Next Action Required:**
Please grant permission to edit `pr_info/TASK_TRACKER.md` so I can mark the "Prepare git commit message for Step 4" task as complete by changing `- [ ]` to `- [x]`.

---
Generated on: 2025-10-06T21:13:35.339944