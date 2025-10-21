# Step 2a: Copy Workflow File to New Location

## Objective

Copy the existing workflow file from `workflows/create_plan.py` to the new package structure at `src/mcp_coder/workflows/create_plan.py` without any modifications. This establishes the new file location while preserving the original for rollback.

## Reference

Review `summary.md` for architectural context and `decisions.md` for the rationale behind the two-file architecture.

## WHERE: File Paths

### New Files
- `src/mcp_coder/workflows/create_plan.py` - Copied workflow module (unmodified copy)

### Source Files (Not Modified)
- `workflows/create_plan.py` - Original file (will be deleted in Step 7)

## WHAT: Main Task

Copy the entire file as-is to establish the new location in the package structure.

## HOW: Copy Process

### Simple File Copy

**Command:**
```bash
cp workflows/create_plan.py src/mcp_coder/workflows/create_plan.py
```

**Or using MCP tool:**
```python
# Read original file
original_content = read_file("workflows/create_plan.py")

# Save to new location
save_file("src/mcp_coder/workflows/create_plan.py", original_content)
```

## ALGORITHM: Verification Process

```python
# 1. Read original file
original = read_file("workflows/create_plan.py")

# 2. Save to new location
save_file("src/mcp_coder/workflows/create_plan.py", original)

# 3. Verify file exists at new location
verify_file_exists("src/mcp_coder/workflows/create_plan.py")

# 4. Verify content is identical
new_content = read_file("src/mcp_coder/workflows/create_plan.py")
assert original == new_content
```

## DATA: File Information

**Source:** `workflows/create_plan.py`
- Size: ~485 lines
- Contains: Complete standalone workflow with CLI parsing

**Destination:** `src/mcp_coder/workflows/create_plan.py`
- Exact copy of source
- Will be refactored in subsequent sub-steps (2b, 2c, 2d)

## Verification Steps

1. **File Created:**
   ```bash
   ls -la src/mcp_coder/workflows/create_plan.py
   ```
   Expected: File exists

2. **Content Identical:**
   ```bash
   diff workflows/create_plan.py src/mcp_coder/workflows/create_plan.py
   ```
   Expected: No differences

3. **Import Check (will fail - expected):**
   ```python
   python -c "from mcp_coder.workflows.create_plan import main"
   ```
   **Note:** This will fail due to import path issues in the copied file. This is expected and will be fixed in Step 2d.

## Next Steps

Proceed to **Step 2b** to refactor the main function signature.

## LLM Prompt for Implementation

```
Please review pr_info/steps/summary.md, pr_info/steps/decisions.md, and pr_info/steps/step_2a.md.

Implement Step 2a: Copy Workflow File to New Location

Requirements:
1. Read the entire content of workflows/create_plan.py
2. Save it to src/mcp_coder/workflows/create_plan.py (exact copy, no modifications)
3. Verify the file was created successfully
4. Verify content is identical using diff or comparison

This is just a file copy - no code changes yet. Changes will happen in steps 2b, 2c, and 2d.

After implementation:
1. Confirm file exists at new location
2. Confirm content is identical to original
3. Note that imports will fail (expected) - will be fixed in step 2d

Do not proceed to the next step yet - wait for confirmation.
```
