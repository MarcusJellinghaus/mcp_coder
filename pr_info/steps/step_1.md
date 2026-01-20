# Step 1: Add Constants, Prompts, and .gitignore Entry

## Overview

Add the foundational configuration: CI-related constants, LLM prompts for analysis and fixing (with placeholders for runtime substitution), a helper function for prompt placeholder substitution (Decision 22), and update .gitignore for the temporary problem description file.

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
CI_NEW_RUN_POLL_INTERVAL_SECONDS = 5  # Poll for new CI run every 5 seconds
CI_NEW_RUN_MAX_POLL_ATTEMPTS = 6  # Max 6 attempts = 30 seconds to detect new run
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

## Part 4: Add Prompt Substitution Helper (Decision 22)

### WHERE
`src/mcp_coder/prompt_manager.py`

### WHAT
Add a helper function to get prompts with placeholder substitution:

```python
def get_prompt_with_substitutions(
    source: str,
    header: str,
    substitutions: Dict[str, str],
) -> str:
    """Get prompt from markdown source and substitute [placeholder] values.

    This is a convenience wrapper around get_prompt() that handles
    placeholder substitution for prompts that use [placeholder] syntax.

    Args:
        source: File path, directory path, wildcard pattern, or string content
        header: Header name to search for (any level: #, ##, ###, ####, #####)
        substitutions: Dictionary mapping placeholder names (without brackets)
            to their replacement values.
            Example: {"job_name": "test", "step_name": "Run tests"}
            This would replace [job_name] with "test" and [step_name] with "Run tests"

    Returns:
        str: The prompt content with all [placeholder] values replaced

    Raises:
        ValueError: If header not found or no code block after header
        FileNotFoundError: If file path doesn't exist

    Example:
        # Load CI analysis prompt with substitutions
        prompt = get_prompt_with_substitutions(
            'prompts/prompts.md',
            'CI Failure Analysis Prompt',
            {
                'job_name': 'test',
                'step_name': 'Run tests',
                'log_excerpt': 'Error: assertion failed',
                'other_failed_jobs': 'build, lint',
            }
        )
    """
    prompt = get_prompt(source, header)
    for key, value in substitutions.items():
        prompt = prompt.replace(f"[{key}]", value)
    return prompt
```

### HOW
1. Add `Dict` to imports from typing if not already present
2. Add the function after `get_prompt()` function
3. Add to module's `__all__` if one exists

### TESTS
Add tests in `tests/test_prompt_manager.py`:

```python
class TestGetPromptWithSubstitutions:
    """Tests for get_prompt_with_substitutions function."""

    def test_substitutes_single_placeholder(self):
        """Should replace a single [placeholder] with value."""
        content = '''# Test Prompt
```
Hello [name], welcome!
```'''
        result = get_prompt_with_substitutions(content, 'Test Prompt', {'name': 'World'})
        assert result == 'Hello World, welcome!'

    def test_substitutes_multiple_placeholders(self):
        """Should replace multiple [placeholder] values."""
        content = '''# Test Prompt
```
Job: [job_name], Step: [step_name]
```'''
        result = get_prompt_with_substitutions(
            content, 'Test Prompt',
            {'job_name': 'test', 'step_name': 'Run tests'}
        )
        assert result == 'Job: test, Step: Run tests'

    def test_empty_substitutions_returns_unchanged(self):
        """Empty substitutions dict should return prompt unchanged."""
        content = '''# Test Prompt
```
Hello [name]!
```'''
        result = get_prompt_with_substitutions(content, 'Test Prompt', {})
        assert result == 'Hello [name]!'

    def test_missing_placeholder_unchanged(self):
        """Placeholders not in dict should remain unchanged."""
        content = '''# Test Prompt
```
Hello [name] and [other]!
```'''
        result = get_prompt_with_substitutions(content, 'Test Prompt', {'name': 'World'})
        assert result == 'Hello World and [other]!'
```

---

## Verification

After completing this step:
1. Constants file should have 6 new CI-related constants (see Decision 9 - no separate fix timeout)
2. Prompts file should have 2 new prompts (CI Failure Analysis, CI Fix)
3. .gitignore should include `pr_info/.ci_problem_description.md`
4. `get_prompt_with_substitutions()` helper function added to prompt_manager.py with tests

Run tests: `pytest tests/test_prompt_manager.py -v`
