@echo off
REM Run import-linter to check architectural boundaries
REM Configuration is in pyproject.toml under [tool.importlinter]
lint-imports %*
