# Step 1: Add Constants, Prompts, and .gitignore Entry

## Overview

Add the foundational configuration: CI-related constants, LLM prompts for analysis and fixing (with placeholders for runtime substitution), and update .gitignore for the temporary problem description file.

## LLM Prompt for This Step

```
Implement Step 1 from pr_info/steps/step_1.md.

Reference the summary at pr_info/steps/summary.md for context.

This step adds constants, prompts, and .gitignore entry for the CI check feature.
No tests required for this step - it's configuration only.
```

---

## Part 1: Add Constants

### WHERE
`src/mcp_coder/workflows/implement/constants.py`

### WHAT
Add 5 new constants at the end of the file:

```python
# CI check constants
LLM_CI_ANALYSIS_TIMEOUT_SECONDS = 300  # 5 minutes for CI failure analysis
CI_POLL_INTERVAL_SECONDS = 15  # Poll CI status every 15 seconds
CI_MAX_POLL_ATTEMPTS = 50  # Max 50 attempts = 12.5 minutes max wait
CI_MAX_FIX_ATTEMPTS = 3  # Max 3 fix attempts before giving up
# Note: CI fix uses existing LLM_IMPLEMENTATION_TIMEOUT_SECONDS (3600s) - see Decision 9
```

### HOW
Append to existing constants file after the existing timeout constants.

### DATA
Constants are integers used by the CI check function in core.py.

---

## Part 2: Add Prompts

### WHERE
`src/mcp_coder/prompts/prompts.md`

### WHAT
Add two new prompts at the end of the file. Use `[placeholder]` syntax for runtime substitution with `.replace("[placeholder]", value)`.

#### CI Failure Analysis Prompt

This prompt analyzes CI pipeline failures to produce a problem description for fixing.
Placeholders: `[job_name]`, `[step_name]`, `[other_failed_jobs]`, `[log_excerpt]`

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

#### CI Fix Prompt

This prompt fixes CI issues based on the problem description from analysis.
Placeholders: `[problem_description]`

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

### HOW
Append to the end of prompts.md, following the existing format:
- Add `## CI Pipeline Checks` section header
- Add `### CI Failure Analysis` subsection with `#### CI Failure Analysis Prompt`
- Add `### CI Fix` subsection with `#### CI Fix Prompt`
- Each prompt has description text followed by a code block containing the prompt template

### ALGORITHM
```
1. Open prompts.md
2. Scroll to end of file
3. Add "## CI Pipeline Checks" section header
4. Add "### CI Failure Analysis" subsection
5. Add "#### CI Failure Analysis Prompt" with description and code block
6. Add "### CI Fix" subsection  
7. Add "#### CI Fix Prompt" with description and code block
```

---

## Part 3: Update .gitignore

### WHERE
`.gitignore` (project root)

### WHAT
Add one line to exclude the temporary CI problem description file:

```
# CI check temporary files
pr_info/.ci_problem_description.md
```

### HOW
Append to the end of .gitignore file.

### DATA
This ensures the temporary analysis file is never accidentally committed.

---

## Verification

After completing this step:
1. Constants file should have 4 new CI-related constants (see Decision 9 - no separate fix timeout)
2. Prompts file should have 2 new prompts (CI Failure Analysis, CI Fix)
3. .gitignore should include `pr_info/.ci_problem_description.md`

No tests required - this is configuration only.
