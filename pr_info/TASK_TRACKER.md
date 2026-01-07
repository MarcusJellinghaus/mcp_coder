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

### Step 1: Restructure pyproject.toml Optional Dependencies
Reference: [pr_info/steps/step_1.md](steps/step_1.md)

- [ ] Implement Step 1: Restructure optional dependencies into `types`, `test`, `mcp`, and `dev` groups
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 1

### Step 2: Update Command Templates
Reference: [pr_info/steps/step_2.md](steps/step_2.md)

- [ ] Implement Step 2: Update Linux templates to use `--extra types` instead of `--extra dev`
- [ ] Implement Step 2: Add `uv sync --project %WORKSPACE%\repo --extra types` to Windows templates
- [ ] Add unit tests for template verification
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 2

### Step 3: Add Documentation to CONFIG.md
Reference: [pr_info/steps/step_3.md](steps/step_3.md)

- [ ] Implement Step 3: Add "Dependency Architecture for Automated Workflows" section to CONFIG.md
- [ ] Run quality checks (pylint, pytest, mypy) and fix all issues
- [ ] Prepare git commit message for Step 3

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Run final quality checks (pylint, pytest, mypy) on entire codebase
- [ ] Create PR summary with all changes
- [ ] Submit Pull Request for review
