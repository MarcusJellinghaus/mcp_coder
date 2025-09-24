@echo off
REM ===========================================================================
REM PR Summary Generator
REM ===========================================================================
REM 
REM Purpose: Generate a pull request summary prompt with git diff and copy
REM          it to clipboard for LLM analysis to create PR descriptions.
REM 
REM Usage:
REM   pr_summary.bat                   - Compare current branch vs main branch
REM   pr_summary.bat [base-branch]     - Compare current branch vs specified base
REM 
REM Examples:
REM   pr_summary.bat                   - Diff between current branch and main
REM   pr_summary.bat feature/parent    - Diff between current branch and feature/parent
REM   pr_summary.bat 38-format-code    - Diff between current branch and 38-format-code
REM 
REM Output:
REM   - Shows current branch, base branch, and main branch names
REM   - Generates PR summary creation prompt with git diff
REM   - Copies complete prompt to clipboard for LLM paste
REM   - Creates PR_Info folder if needed
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
    echo Usage: pr_summary.bat [base-branch-name]
)

echo Current branch: %CURRENT_BRANCH%
echo Base branch:    %BASE_BRANCH%
echo Main branch:    %MAIN_BRANCH%
echo.

REM Check if PR_Info folder exists, create if not
if not exist PR_Info (
    echo Creating PR_Info folder...
    mkdir PR_Info
)

REM Create temporary file with unique name for large diffs
set TEMP_FILE=%TEMP%\pr_summary_%RANDOM%_%TIME:~6,2%%TIME:~9,2%.txt

REM Generate git diff and create PR summary prompt
(
    echo Please read the information in folder `PR_Info` ^(including any implementation steps in `PR_Info/steps/`^) and review the code changes ^(git output^)
    echo Can you please create a limited size summary for a pull request?
    echo Please do not refer to the files in `PR_Info` directly !
    echo Please save the pull request summary in markdown file ^(as `PR_Info\pr_summary.md`^) so that I can easily copy/paste it.
    echo Last steps:
    echo     1^) Delete the `PR_Info/steps/` subfolder and the `PR_Info/.conversations/` subfolder and
    echo     2^) Clear the Tasks section from `TASK_TRACKER.md` ^(keep the template structure^)
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

echo PR summary prompt with git diff copied to clipboard!
echo Paste it in the LLM to generate a pull request summary.
exit /b 0