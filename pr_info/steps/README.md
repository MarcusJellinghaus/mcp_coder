# Implementation Steps Overview

This directory contains the step-by-step implementation plan for adding GitHub Labels Manager.

## Files in this Directory

- `summary.md` - Overview, architectural changes, and file manifest
- `step_1.md` - Unit tests for LabelsManager validation (TDD red phase)
- `step_2.md` - Implement LabelsManager class initialization (TDD green phase)
- `step_3.md` - Integration tests for label operations (TDD red phase)
- `step_4.md` - Implement label CRUD methods (TDD green phase)

## Reading Order

1. **Start with `summary.md`** - Understand the overall approach
2. **Follow steps sequentially** - Each step builds on previous ones
3. **Each step is self-contained** - Has WHERE, WHAT, HOW, ALGORITHM, DATA, and LLM prompt

## Implementation Workflow

```
Step 1: Write unit tests (FAIL) 
   ↓
Step 2: Implement initialization (PASS unit tests)
   ↓
Step 3: Write integration tests (FAIL)
   ↓
Step 4: Implement CRUD methods (PASS all tests)
```

## Quick Start

Each step includes an **LLM Prompt** section at the bottom. Copy that prompt to Claude Code or your AI assistant to implement that specific step.

## Testing Commands

```bash
# Unit tests only (fast)
pytest tests/utils/test_github_operations.py::TestLabelsManagerUnit -v

# Integration tests (requires GitHub config)
pytest tests/utils/test_github_operations.py::TestLabelsManagerIntegration -v -m github_integration

# All LabelsManager tests
pytest tests/utils/test_github_operations.py -k "LabelsManager" -v
```
