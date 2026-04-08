@REM Check markdown links with lychee.
@REM
@REM Install: lychee is a single .exe — no toolchain required.
@REM   Download: https://github.com/lycheeverse/lychee/releases
@REM   Asset:    lychee-x86_64-windows.exe
@REM   Place it on PATH (e.g. .venv\Scripts\lychee.exe — already on PATH when venv is active).
@REM
@REM Usage:
@REM   This script runs in --offline mode (local files only, fast, no network).
@REM   To ALSO check external URLs, remove --offline below (slower, ~3s, may report
@REM   transient TLS/network errors that are not real broken links).
lychee --offline README.md "docs/**/*.md" project_idea.md
