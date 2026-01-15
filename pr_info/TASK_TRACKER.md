# MCP Coder Task Tracker

## Overview

This tracks **Feature Implementation** consisting of multiple **Implementation Steps**.

- **Feature**: A complete user-facing capability
- **Implementation Step**: A self-contained unit of work (tests + implementation)

## Status Legend

- [x] = Implementation step complete
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Migrate to uv and Update Dependencies

- [x] Add `astral-sh/setup-uv@v4` action after checkout in `test` job
- [ ] Add `astral-sh/setup-uv@v4` action after checkout in `architecture` job
- [ ] Replace pip installation with `uv pip install --system ".[dev]"` in `test` job
- [ ] Replace pip installation with `uv pip install --system ".[dev]"` in `architecture` job
- [ ] Run quality checks (pylint, pytest, mypy) for Step 1
- [ ] Prepare git commit message for Step 1

### Step 2: Add Environment Info and Tool Versions

- [ ] Add environment info step after dependency installation in `test` job
- [ ] Add environment info step after dependency installation in `architecture` job
- [ ] Prepend `black --version &&` to black matrix command
- [ ] Prepend `isort --version &&` to isort matrix command
- [ ] Prepend `pylint --version &&` to pylint matrix command
- [ ] Prepend `pytest --version &&` to unit-tests matrix command
- [ ] Prepend `pytest --version &&` to integration-tests matrix command
- [ ] Prepend `mypy --version &&` to mypy matrix command
- [ ] Prepend `lint-imports --version &&` to import-linter matrix command
- [ ] Prepend `tach --version &&` to tach matrix command
- [ ] Prepend `pycycle --version &&` to pycycle matrix command
- [ ] Prepend `vulture --version &&` to vulture matrix command
- [ ] Run quality checks (pylint, pytest, mypy) for Step 2
- [ ] Prepare git commit message for Step 2

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Verify CI passes with new configuration
- [ ] Review PR summary and description
- [ ] Create Pull Request
