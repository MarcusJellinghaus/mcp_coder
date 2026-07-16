@echo off
rem Launcher for prune-branches.ps1 - forwards all args (e.g. -Delete, -Main master).
rem Prefers PowerShell 7 (pwsh); falls back to built-in Windows PowerShell 5.1.
where pwsh >nul 2>nul && (
  pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0prune-branches.ps1" %*
) || (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0prune-branches.ps1" %*
)
