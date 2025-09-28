# Implementation Task: Add PR Summary Generation prompt to src/mcp_coder/prompts/prompts.md

## Prompt Sent to LLM:
Please look at `pr_info/TASK_TRACKER.md` and pick the next task that should be done.
Please let me know on which task you are working on.
Please implement!
Please verify your implementation running the various checks of the MCP server and by solving potential issues (and repeat).
Please do not invent extra complexity not mentioned in the project plan.
Please let me know in case you encounter any issues or need a decision.
Please provide a short concise commit message stating the step name in the title. Do NOT perform a commit!

Once you are done, please check again that task description on `pr_info/TASK_TRACKER.md` to ensure that everything is done.
Once everything is done, please mark the task as done.
Please work only on one task. Do not pick further tasks.

Please also take a look at the tests\readme.md and only run those tests that are required in your context -i.e. avoid slow integration tests.

Current task from TASK_TRACKER.md: Add PR Summary Generation prompt to src/mcp_coder/prompts/prompts.md

Please implement this task step by step.

## LLM Response:
I'll start by examining the TASK_TRACKER.md to understand the current task, then implement it step by step.Now I'll examine the detail file for Step 3 to understand what needs to be done:Let me check what files exist in the pr_info directory:Let me check the step 3 details in the steps folder:I'll work on Step 3: Add PR Summary Generation prompt to src/mcp_coder/prompts/prompts.md. Let me start by using the TodoWrite tool to track this task.Now let's examine the existing prompts.md file to understand its structure:Now let me update the TodoWrite to reflect I've reviewed the existing structure:Now I'll add the PR Summary Generation prompt to the prompts.md file. Based on the existing structure and the requirements from step 3, I'll create a well-structured prompt template:Good! I've successfully added the PR Summary Generation prompt template. Now let me update the todo and run the code quality checks:Now let's run pylint check:Now let's run pytest check focusing on unit tests (excluding integration tests):The test is failing because the prompt parser detected duplicate headers. The issue is that within my PR Summary Generation prompt template, I used markdown headers (##) in the example output, which are being interpreted as actual prompt headers. Let me fix this by escaping or modifying those headers in the template:I see the issue. The headers with ## inside the code block are being parsed as actual headers. Let me fix this by modifying the format to avoid using markdown headers inside the prompt:Good, I've fixed the duplicate header issue. Now let's run the pytest check again to make sure the tests pass:I see there's still a duplicate header issue. The problem is that I have two headers with "PR Summary Generation" - one at the section level (###) and one at the prompt level (####). Let me check the file and fix this:I see the issue - there's a duplicate "PR Summary Generation" header. The section header (###) and the prompt header (####) both have "PR Summary Generation". Let me fix this by renaming one of them:Good! Now let's run pytest again to see if the tests pass:Excellent! All pytest tests pass. Let me update the TodoWrite tool and run the mypy check:Perfect! All checks have passed. Let me update the todo list and then update the TASK_TRACKER.md to mark Step 3 as complete:Now let's update the TASK_TRACKER.md to mark all Step 3 tasks as complete:## Summary

I have successfully completed Step 3: Add PR Summary Prompt Template. Here's what was accomplished:

1. **Added PR Summary Generation prompt** to `src/mcp_coder/prompts/prompts.md` with:
   - Clear instructions for generating PR titles and descriptions from git diffs
   - Structured output format for easy parsing
   - Edge case handling for various diff types
   - Example output demonstrating expected format

2. **All quality checks passed**:
   - ✅ Pylint: No issues found
   - ✅ Pytest: All 392 tests passed
   - ✅ Mypy: No type errors

3. **Updated TASK_TRACKER.md** to mark all Step 3 tasks as complete.

## Commit Message

```
feat(prompts): add PR summary generation prompt template for step 3

Add comprehensive prompt template to generate pull request titles and
descriptions from git diffs, with structured output format and edge
case handling.
```

All CLAUDE.md requirements followed - used MCP tools exclusively for all operations.

---
Generated on: 2025-09-28T09:57:27.820243