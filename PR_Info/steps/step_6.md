# Step 6: Update Batch Script

## Overview
Update the `implement.bat` batch script to use the new `--project-dir` parameter with current directory as default.

## WHERE
- **File**: `workflows/implement.bat`

## WHAT

### Batch Script Update
```batch
@echo off
REM Updated implement workflow with project directory parameter
echo Starting implement workflow...
python workflows\implement.py --project-dir .
```

## HOW

### Batch Script Changes
- **Parameter**: Add `--project-dir .` to Python script call
- **Current directory**: Use "." as default project directory
- **Error handling**: Maintain existing error code handling
- **Compatibility**: Keep existing pause and exit behavior

## ALGORITHM

### Batch Script Update (3 steps)
```pseudocode
1. Keep existing error handling and echo messages
2. Update python command to include --project-dir parameter
3. Use "." to represent current directory
```

## DATA

### Batch Script Command
```batch
# Updated command line
python workflows\implement.py --project-dir .

# Arguments passed to Python script
sys.argv = ["workflows/implement.py", "--project-dir", "."]
```



## LLM PROMPT

Please read the **summary.md** file and implement **Step 6** exactly as specified.

**Context**: We've completed updating all Python functions to support `--project-dir` parameter (Steps 1-5). Now we need to update the batch script and create integration tests.

**Your Task**:

1. **Update `workflows/implement.bat`**:
   - Modify the Python command to include `--project-dir .`
   - Keep existing error handling and pause behavior

**Specific Requirements**:

**Batch Script Requirements**: 
- Change `python workflows\implement.py` to `python workflows\implement.py --project-dir .`
- Maintain all existing error handling and user experience

This completes the implementation - the workflow should now work from any location with `--project-dir` parameter support.

**Note**: No testing is required for workflows based on project decisions.
