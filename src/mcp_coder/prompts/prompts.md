# Prompts

This file contains prompts for the mcp-coder project.

## Getting Started

Add your prompts below using the format shown in `prompt_instructions.md`.
You can mix documentation and prompts in this file. Only headers followed by code blocks will be treated as prompts.

### Example
```
My lengthy explanation of what this prompt does and when to use it.

Provide clear instructions here.
Include examples if helpful.
Use placeholders like [Insert code here] for variable content.

Expected output format: [describe the expected response]
```

## Prompts for standard commands

### Commit

Context: A git commit message should be generated. A `git diff` will be added. 
The respoonse will be used for committing the diff.  
If the response contains seeral lines, the second line is expected to be empty to separate header and commit message details.

#### Git Commit Message Generation
```
Analyze the provided git diff and status information to generate a concise, professional commit message following conventional commit format.

REQUIREMENTS:
1. Keep commit summary BRIEF - aim for under 50 characters when possible
2. Use conventional commit format: type(scope): description
   - Types: feat, fix, docs, style, refactor, test, chore, build, ci
   - Scope is optional but helpful for context
   - Description should be imperative mood ("add" not "adds" or "added")
3. Focus on WHAT changed, not implementation details
4. Only include body text if essential for context (1-2 sentences max)
5. Analyze both staged and unstaged changes if provided

ANALYSIS STEPS:
1. Review git status to understand file changes (new, modified, deleted)
2. Examine git diff to understand the nature of changes
3. Identify the primary purpose/type of the changes
4. Determine appropriate scope if multiple areas are affected
5. Craft a clear, concise description

OUTPUT FORMAT:
Provide the commit message in plain text format ready to use:

feat(auth): add user validation

Optional body text here if needed for context.

EXAMPLES:
- feat: add user authentication system
- fix(api): resolve null pointer in validation
- docs: update installation instructions
- refactor(db): simplify connection handling
- test: add unit tests for user service
- chore: update dependencies to latest versions

Expected output: A properly formatted conventional commit message ready to use with git commit.

Do NOT PROVIDE ANYTHING - just the commit message! NO WORDS BEFORE OR AFTER! 
```


## Prompts for task tracker based workflows

### Task Tracker Update

This prompt is used to populate or update the TASK_TRACKER.md file with implementation steps from the plan.

#### Task Tracker Update Prompt
```
Read implementation steps in `pr_info/steps/` and update/create `pr_info/TASK_TRACKER.md`:

**If file doesn't exist:** Generate complete task tracker with all steps.

**If file exists:** Add missing tasks only. PRESERVE all existing checked boxes `[x]` - do not modify completed tasks.

Each task should include:
- Step implementation 
- Quality checks: pylint, pytest, mypy - and work on all issues found
- Preparation of a git commit message
- put one [ ] for each task

Add "Pull Request" section at end with PR review and summary tasks.

Follow existing format in TASK_TRACKER.md or standard checkbox format.
```

### Implementation step

This is the actual step where could should be written or modified. The actual task comes from task tracker and its links to the task description.

#### Implementation Prompt Template using task tracker
```
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

**Always use the MCP tools**
```

### Mypy Type Fixes

This prompt is used to fix mypy type errors when they are detected during code quality checks.

#### Mypy Fix Prompt
```
Fix the mypy type errors shown in the output below.

Focus only on resolving the type errors - do not make unnecessary changes to the code.

For each error:
1. Understand the type mismatch or missing annotation
2. Add appropriate type hints or fix incorrect types
3. Use proper typing imports (List, Dict, Optional, etc.) from typing module
4. Ensure all function parameters and return types are properly annotated

Keep changes minimal and focused on type correctness.

Mypy output:
[mypy_output]

Expected output: Code changes that resolve all type errors while maintaining functionality.
```

### Pull Request Summary

This prompt is used to generate pull request titles and descriptions from git diff output.

#### PR Summary Generation
```
Generate a PR title and body from the git diff. Follow this EXACT format:

TITLE: [conventional_prefix]: [brief description]
BODY:
## Summary
[What this PR does and why]

## Changes
- [Change 1]
- [Change 2]
- [Change 3]

REQUIREMENTS:
- Title must start with: feat:, fix:, docs:, refactor:, test:, or chore:
- Title must be under 60 characters
- Use ## for markdown headings in body
- List specific changes as bullet points
- Be concise but informative

EXAMPLE OUTPUT:
TITLE: feat: add PR workflow automation
BODY:
\#\# Summary
Implements automated PR creation with LLM-generated summaries.

\#\# Changes
- Add create_PR.py workflow script
- Implement PR summary generation prompt
- Add error handling for prompt loading

Git diff to analyze:
[git_diff_content]

OUTPUT THE TITLE AND BODY EXACTLY AS SHOWN ABOVE - NO OTHER TEXT!
```

## Plan Generation Workflow

Three-prompt sequence for generating implementation plans from GitHub issues.

### Initial Analysis

```
## Discuss implementation steps
Please take a look at the existing solution, its files and its architecture documentation.
Do you understand the task below?
What are the implementation steps?
Do not yet modify any code!
```

### Simplification Review

```
Let's review the plan with simplicity in mind. Can we achieve the same goals with a simpler approach?
Consider KISS principle and maintainability. while preserving the issue's requirements.
Make sure to preserve the issue's requirements - only propose simplifications that preserve the requirements of the issue.
```

### Implementation Plan Creation

```
## Python Project Implementation Plan Request
Create a **summary** (`pr_info/steps/summary.md`) and **implementation plan** with self-contained steps (`pr_info/steps/step_1.md`, `pr_info/steps/step_2.md`, etc.).
Can you also give a summary of the architectural / design changes in the summary document?
Also list the folders \ modules \ files that should be created or modified by this implementation.

### Requirements:
- Follow **Test-Driven Development** where applicable. 
  Each step should have its own test implementation followed by related functionality implementation.  
- Each step must include a **clear LLM prompt** that references the summary and that specific step
- Apply **KISS principle** - minimize complexity, maximize maintainability
- Keep code changes minimal and follow best practices

### Each Step Must Specify:
- **WHERE**: File paths and module structure
- **WHAT**: Main functions with signatures
- **HOW**: Integration points (decorators, imports, etc.)
- **ALGORITHM**: 5-6 line pseudocode for core logic (if any)
- **DATA**: Return values and data structures
```
