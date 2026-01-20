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
Implement ONE step from the task tracker.

**1. SELECT STEP**
- Read `pr_info/TASK_TRACKER.md`
- Find the first Step with unchecked sub-tasks (`- [ ]`)
- Work through ALL sub-tasks in that step sequentially
- Announce which task you're working on

**2. FOR EACH SUB-TASK**
- Read linked files in `pr_info/steps/` if referenced
- Implement only what's described
- Run code checks (pylint, pytest, mypy) when required
- Fix all issues before proceeding
- Mark sub-task complete: `- [ ]` → `- [x]`

**3. COMPLETE THE STEP**
- All sub-tasks must be `[x]` before finishing
- Write commit message to `pr_info/.commit_message.txt`
- Do NOT commit - just write the message to the file

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations
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

## CI Pipeline Checks

### CI Failure Analysis

This prompt analyzes CI pipeline failures to produce a problem description for fixing.
Placeholders: `[job_name]`, `[step_name]`, `[other_failed_jobs]`, `[log_excerpt]`

#### CI Failure Analysis Prompt
```
Analyze the CI pipeline failure and write a problem description.

**Context:**
- Failed job: [job_name]
- Failed step: [step_name]
- Other failed jobs: [other_failed_jobs]
- Implementation plan is in `pr_info/steps/`

**CI Log Excerpt:**
[log_excerpt]

**Your Task:**
1. Identify the root cause of the failure
2. Determine which files/code likely need changes
3. Write a clear problem description to `pr_info/.ci_problem_description.md`

**Output Format:**
Write a concise problem description (2-5 paragraphs) to the file that includes:
- What failed and why
- Which files are likely involved
- What changes are needed to fix it

Write ONLY the problem description to the file - no code, no markdown headers, just the analysis text.
```

### CI Fix

This prompt fixes CI issues based on the problem description from analysis.
Placeholders: `[problem_description]`

#### CI Fix Prompt
```
Fix the CI pipeline failure based on the problem description below.

**Problem Description:**
[problem_description]

**Your Task:**
1. Read the problem description carefully
2. Make the necessary code changes to fix the issue
3. Run quality checks: pylint, pytest, mypy
4. Fix any issues found by quality checks
5. Write a commit message to `pr_info/.commit_message.txt`

**Rules:**
- Make minimal, focused changes
- Ensure all quality checks pass
- Do NOT commit - just write the commit message file
```
