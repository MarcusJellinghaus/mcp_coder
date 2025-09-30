# Step 5: Create Windows Batch Wrapper Script

## Objective
Create `define_labels.bat` following existing workflow script patterns.

## Context
Reference `summary.md`. Copy structure from `workflows/create_PR.bat` for consistency.

## WHERE
- Create: `workflows/define_labels.bat`

## WHAT

### In `workflows/define_labels.bat`:
```batch
@echo off
REM define_labels.bat - Windows Batch Wrapper for Label Definition
REM
REM Usage:
REM   define_labels.bat [--project-dir <path>] [--log-level <level>]

REM Set UTF-8 encoding
REM Set PYTHONPATH
REM Execute: python workflows\define_labels.py --project-dir . --log-level INFO
REM Handle exit codes
```

## HOW
- Copy from `workflows/create_PR.bat`
- Remove `--llm-method` parameter
- Keep UTF-8 encoding setup
- Keep PYTHONPATH configuration
- Use default log level INFO

## ALGORITHM
```
1. Set console codepage to UTF-8
2. Configure Python UTF-8 environment variables
3. Set PYTHONPATH to include src directory
4. Echo start message
5. Call python workflows\define_labels.py with args
6. Check ERRORLEVEL and exit accordingly
```

## DATA
- **Input**: Command-line arguments (forwarded to Python script)
  - `--project-dir <path>` (optional)
  - `--log-level <level>` (optional)
  - `--dry-run` (optional flag)
- **Output**: Exit code (0 success, non-zero failure)

## LLM Prompt
```
Reference: pr_info/steps/summary.md

Implement Step 5: Windows batch wrapper.

Tasks:
1. Copy workflows/create_PR.bat to workflows/define_labels.bat
2. Update script name and description in comments
3. Remove --llm-method parameter (not needed)
4. Keep --project-dir and --log-level
5. Update python command to call define_labels.py
6. Test by running: workflows\define_labels.bat --help

Verify UTF-8 encoding setup is preserved exactly as in create_PR.bat.
```
