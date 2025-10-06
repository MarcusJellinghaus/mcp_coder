# Implementation Task: Implement core.py with utilities and type definitions

## Prompt Sent to LLM:
You are implementing tasks from a task tracker. Follow these steps in order:

**STEP 0: SHOW CONFIGURATION TASK**
- Please check which MCP servers you have. What can you use them for? Which tools are you allowed to use. Please list them.

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
I need permission to edit the TASK_TRACKER.md file. Let me wait for approval and then complete the task.

**STEP 5: COMMIT MESSAGE PREPARED**

I have prepared the following commit message for Step 4:

```
feat(llm): add env_vars parameter to interface layer

Add optional env_vars parameter to high-level interface functions for
environment variable propagation to LLM subprocesses.

Changes:
- Add env_vars to ask_llm() and prompt_llm() in llm/interface.py
- Add env_vars to ask_claude_code() in claude_code_interface.py
- Thread env_vars through to CLI/API provider functions
- Update docstrings with parameter documentation
- Add test coverage for env_vars parameter passing
- Maintain backward compatibility (env_vars defaults to None)

Related: Step 4 of environment variable propagation feature
```

**STEP 6: AWAITING PERMISSION TO MARK TASK COMPLETE**

I need to update `pr_info/TASK_TRACKER.md` to mark the task `- [ ] Prepare git commit message for Step 4` as complete by changing it to `- [x] Prepare git commit message for Step 4`.

Once you grant permission, I will complete the checkbox update to finalize this task.

---
Generated on: 2025-10-06T22:21:24.433166