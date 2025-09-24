@echo off
REM ===========================================================================
REM PR Review Generator
REM ===========================================================================
REM 
REM Purpose: Generate a structured pull request review prompt with git diff
REM          and copy it to clipboard for LLM analysis.
REM 
REM Usage:
REM   pr_review.bat                    - Compare current branch vs main branch
REM   pr_review.bat [base-branch]      - Compare current branch vs specified base
REM 
REM Examples:
REM   pr_review.bat                    - Diff between current branch and main
REM   pr_review.bat feature/parent     - Diff between current branch and feature/parent
REM   pr_review.bat 38-format-code     - Diff between current branch and 38-format-code
REM 
REM Output:
REM   - Shows current branch, base branch, and main branch names
REM   - Generates structured review prompt with git diff
REM   - Copies complete prompt to clipboard for LLM paste
REM   - Warns if diff is very large (>500KB)
REM 
REM ===========================================================================
setlocal enabledelayedexpansion

REM Check if we're in a git repository
git rev-parse --git-dir >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Not in a git repository
    exit /b 1
)

REM Get current branch name
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set CURRENT_BRANCH=%%i
if not defined CURRENT_BRANCH (
    echo Error: Could not detect current branch
    exit /b 1
)

REM Detect main/default branch
for /f "tokens=3" %%i in ('git symbolic-ref refs/remotes/origin/HEAD 2^>nul') do (
    for /f "tokens=2 delims=/" %%j in ("%%i") do set MAIN_BRANCH=%%j
)
REM Fallback to common defaults if detection fails
if not defined MAIN_BRANCH (
    git rev-parse --verify origin/main >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set MAIN_BRANCH=main
    ) else (
        git rev-parse --verify origin/master >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            set MAIN_BRANCH=master
        ) else (
            echo Error: Could not detect main branch
            exit /b 1
        )
    )
)

REM Determine base branch (the branch this feature branches from)
if not "%1"=="" (
    set BASE_BRANCH=%1
    echo Using base branch: %BASE_BRANCH%
) else (
    REM Default to main branch (most common case)
    set BASE_BRANCH=%MAIN_BRANCH%
    echo No base branch specified, defaulting to main branch
    echo Usage: pr_review.bat [base-branch-name]
)

echo Current branch: %CURRENT_BRANCH%
echo Base branch:    %BASE_BRANCH%
echo Main branch:    %MAIN_BRANCH%
echo.

REM Create temporary file with unique name for large diffs
set TEMP_FILE=%TEMP%\pr_review_%RANDOM%_%TIME:~6,2%%TIME:~9,2%.txt

REM Generate git diff and create enhanced review prompt
(
    echo ## Code Review Request
    echo.
    echo Review the changes below and identify any issues.
    echo.
    echo There is no read to run all checks, do not use pylint warnings.
    echo Feel free to further analyse any mentioned files and/or the file structure etc.
    echo.
    echo ### Focus Areas:
    echo - Logic errors or bugs
    echo - Tests for `__main__` functions should be removed ^(not needed^)
    echo - Unnecessary debug code or print statements
    echo - Code that could break existing functionality
    echo.
    echo ### Output Format:
    echo 1. **Summary** - What changed ^(1-2 sentences^)
    echo 2. **Critical Issues** - Must fix before merging
    echo 3. **Suggestions** - Nice to have improvements
    echo 4. **Good** - What works well
    echo.
    echo Do not perform any action. Just present the code review.
    echo.
    echo Current branch: %CURRENT_BRANCH%
    echo Base branch:    %BASE_BRANCH%
    echo Main branch:    %MAIN_BRANCH%
    echo.
    echo === GIT DIFF ===
    echo.
    git diff --unified=5 --no-prefix %BASE_BRANCH%...HEAD
) > %TEMP_FILE%

REM Check file size (warn if > 500KB)
for %%A in ("%TEMP_FILE%") do set FILE_SIZE=%%~zA
if %FILE_SIZE% GTR 512000 (
    echo Warning: Diff is large ^(%FILE_SIZE% bytes^). Clipboard may have limitations.
)

REM Copy to clipboard
type %TEMP_FILE% | clip

REM Clean up
del %TEMP_FILE%

echo PR review prompt with git diff copied to clipboard!
echo Paste it in the LLM to get a structured code review.
exit /b 0