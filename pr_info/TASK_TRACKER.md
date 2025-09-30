# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in PR_Info/ folder

---

## Tasks

### Step 1: Create Test Structure and Label Constants
[x] Implement WORKFLOW_LABELS constant in workflows/define_labels.py with all 10 status labels
[x] Add color validation at module load (6-char hex format)
[x] Create tests/workflows/test_define_labels.py with test_workflow_labels_constant()
[x] Run quality checks: pylint, pytest, mypy - fix all issues
[ ] Prepare git commit message for Step 1

### Step 2: Implement apply_labels Core Function with Tests
[ ] Implement calculate_label_changes() as pure function (no logging, side-effect-free)
[ ] Write 8 unit tests for calculate_label_changes() covering:
  - Empty repo, create, update, delete, unchanged, preserve non-status
  - Partial match (5 of 10), all exist unchanged
[ ] Implement apply_labels() orchestrator with dry_run support
[ ] Add pytest fixtures to mock LabelsManager (Option B from decisions)
[ ] Write 3 integration tests for apply_labels():
  - Success flow, dry-run mode, API error fails fast
[ ] Add INFO level logging in apply_labels() only
[ ] Ensure skip API calls for unchanged labels (idempotency)
[ ] Implement strict deletion of obsolete status-* labels
[ ] Ensure fail-fast on API errors (exit on first error)
[ ] Run quality checks: pylint, pytest, mypy - fix all issues
[ ] Prepare git commit message for Step 2

### Step 3: Implement CLI Argument Parsing and Logging Setup
[ ] Copy parse_arguments() from workflows/create_PR.py to workflows/define_labels.py
[ ] Remove --llm-method argument (not needed)
[ ] Keep --project-dir and --log-level arguments
[ ] Add --dry-run flag (action='store_true', default=False)
[ ] Copy resolve_project_dir() from workflows/create_PR.py
[ ] Add 4 tests for argument parsing and validation
[ ] Run quality checks: pylint, pytest, mypy - fix all issues
[ ] Prepare git commit message for Step 3

### Step 4: Implement main() Function and Script Entry Point
[ ] Add shebang and module docstring to workflows/define_labels.py
[ ] Implement main() function following workflows/create_PR.py pattern
[ ] Call parse_arguments(), resolve_project_dir(), setup_logging(), apply_labels()
[ ] Pass dry_run flag to apply_labels(): apply_labels(project_dir, dry_run=args.dry_run)
[ ] Log at start: project directory, repository name, dry-run mode status
[ ] Add if __name__ == "__main__": main()
[ ] Add 2 tests for main() covering success and error scenarios
[ ] Run quality checks: pylint, pytest, mypy - fix all issues
[ ] Prepare git commit message for Step 4

### Step 5: Create Windows Batch Wrapper Script
[ ] Copy workflows/create_PR.bat to workflows/define_labels.bat
[ ] Update script name and description in comments
[ ] Remove --llm-method parameter (not needed)
[ ] Keep --project-dir, --log-level, and --dry-run parameters
[ ] Update python command to call define_labels.py
[ ] Verify UTF-8 encoding setup is preserved
[ ] Test batch file: workflows\define_labels.bat --help
[ ] Run quality checks: pylint, pytest, mypy - fix all issues
[ ] Prepare git commit message for Step 5

### Step 6: Final Verification
[ ] Run all unit tests: pytest tests/workflows/test_define_labels.py -v
[ ] Verify 17+ tests pass (8 calculate_label_changes, 3 apply_labels, 4 CLI, 2 main)
[ ] Test script imports: python -c "from workflows.define_labels import main"
[ ] Manual smoke test: python workflows/define_labels.py --dry-run --log-level DEBUG
[ ] Verify batch file works: workflows\define_labels.bat --help
[ ] Run quality checks: pylint, pytest, mypy - fix all issues
[ ] Prepare git commit message for Step 6

---

## Pull Request
[ ] Review all code changes and ensure completeness
[ ] Verify all tests pass (17+ unit tests total)
[ ] Run final quality checks: pylint, pytest, mypy - ensure all pass
[ ] Prepare comprehensive PR summary with:
  - Overview of label definition workflow
  - List of 10 workflow labels defined
  - Key features: dry-run mode, idempotency, fail-fast error handling
  - Test coverage summary
  - Usage examples
[ ] Create pull request from branch to main
[ ] All tasks completed