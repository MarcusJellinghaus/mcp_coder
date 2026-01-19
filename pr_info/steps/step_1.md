# Step 1: Update Implementation Prompt

## LLM Prompt

```
Implement Step 1 from pr_info/steps/summary.md.

Update the implementation prompt in prompts.md to specify where the commit message should be written.

Read the summary first, then make the minimal change required.
```

## WHERE

**File**: `src/mcp_coder/prompts/prompts.md`

**Section**: "Implementation Prompt Template using task tracker" → "**3. COMPLETE THE STEP**"

## WHAT

Change the commit message instruction from ambiguous to specific:

**Current text**:
```
- Prepare commit message when that sub-task appears
```

**New text**:
```
- Write commit message to `pr_info/.commit_message.txt`
```

## HOW

1. Open `src/mcp_coder/prompts/prompts.md`
2. Locate the "Implementation Prompt Template using task tracker" section
3. Find the "**3. COMPLETE THE STEP**" subsection
4. Replace the line about commit message preparation

## DATA

No code changes - this is a prompt text update only.

## VERIFICATION

- Run existing tests to ensure no regressions: `pytest tests/test_prompt_manager.py -v`
- Visually verify the prompt file contains the updated instruction
