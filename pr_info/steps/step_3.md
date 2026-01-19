# Step 3: Update CI Pipeline - Forbidden File Check

## LLM Prompt

```
Implement Step 3 from pr_info/steps/summary.md.

Update the CI workflow to block PRs that contain pr_info/.commit_message.txt.
Add a simple file existence check - no need for a new function.
Keep the job name as "check-forbidden-folders" (as specified in the issue).
```

## WHERE

**File**: `.github/workflows/ci.yml`

**Location**: Inside the `check-forbidden-folders` job, after the existing folder checks (around line 50)

## WHAT

Add a simple file existence check before the final error evaluation:

```bash
# Check for forbidden commit message file
if [ -f "pr_info/.commit_message.txt" ]; then
    echo "❌ ERROR: Found forbidden file pr_info/.commit_message.txt"
    echo "Description: Transient commit message file should not be committed"
    ERROR=1
else
    echo "✅ No forbidden commit message file found"
fi
```

## HOW

1. Open `.github/workflows/ci.yml`
2. Locate the `check-forbidden-folders` job
3. Find the section with existing `check_forbidden_folder` and `check_empty_folder` calls
4. Add the new file check AFTER those calls but BEFORE the final `if [ $ERROR -eq 1 ]` block
5. Keep job name unchanged (`check-forbidden-folders`)

## ALGORITHM

```
1. Use simple bash `[ -f path ]` test for file existence
2. If file exists, set ERROR=1 and print error message
3. If file doesn't exist, print success message
```

## DATA

No data structures - this is a simple bash conditional check.

## VERIFICATION

The CI check cannot be tested locally in the traditional sense, but:

1. **Syntax check**: Ensure the YAML is valid
2. **Logic check**: The file check follows the same pattern as existing checks
3. **Manual test**: Create a test PR with the file to verify it blocks

```bash
# Verify YAML syntax (if yamllint is available)
yamllint .github/workflows/ci.yml

# Or use Python
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
```
