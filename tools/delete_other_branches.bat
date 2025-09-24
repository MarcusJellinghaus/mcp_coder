@echo off
REM Script to safely delete local Git branches that have been merged into main
REM Protects the current branch and main branch from deletion
REM Only deletes branches that have been fully merged (safe deletion with -d flag)
REM Does not switch branches - runs from your current branch

echo Getting current branch...
for /f "tokens=* USEBACKQ" %%i in (`git branch --show-current`) do set current_branch=%%i

if "%current_branch%"=="" (
    echo Failed to get current branch. Exiting.
    pause
    exit /b 1
)

echo Current branch: %current_branch%
echo Deleting merged branches (excluding main and current branch)...

git branch --merged main | findstr /v "main" | findstr /v "%current_branch%" | findstr /v "\*" > temp_branches.txt

if exist temp_branches.txt (
    for /f "tokens=*" %%i in (temp_branches.txt) do (
        set "branch_name=%%i"
        setlocal enabledelayedexpansion
        set "branch_name=!branch_name: =!"
        if "!branch_name!" neq "" (
            echo Deleting branch: !branch_name!
            git branch -d "!branch_name!"
        )
        endlocal
    )
    del temp_branches.txt
    echo Done!
) else (
    echo No merged branches to delete.
)

pause
