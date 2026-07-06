# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Reorganize VSCodeClaude command tests (no production code change)

Detail: [step_1.md](./steps/step_1.md)

- [x] Implementation: move `_assessment_stub`, `TestSkipGithubInstallWiring`, and `TestAtCapacityDiagnosticLog` verbatim from `test_commands.py` to `test_vscodeclaude_cli.py`; reconcile imports (add `SimpleNamespace`, `MagicMock`, `patch`, `VSCodeClaudeConfig` to target; remove now-unused `SimpleNamespace`, `VSCodeClaudeConfig` from source). No `src/` changes.
- [x] Quality checks: run_format_code, run_pylint_check, run_pytest_check, run_mypy_check, run_vulture_check — fix all issues (same test count as before)
- [x] Commit message prepared

### Step 2: Move the VSCodeClaude source family + repoint patch strings

Detail: [step_2.md](./steps/step_2.md)

- [ ] Implementation: `move_symbol` (dry-run + verify GATE, then execute) the 5 VSCodeClaude functions to new `commands_vscodeclaude.py`; set `__all__` in both modules; split `__init__.py` into two import blocks; remove `commands.py` from `.large-files-allowlist`; blanket `replace_all` patch-string repoint in the 3 vscodeclaude-only test files
- [ ] Quality checks: run_format_code, run_pylint_check, run_pytest_check, run_mypy_check, run_lint_imports_check, run_vulture_check, check_file_size, tach check, compact-diff (imports + headers only) — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] Address PR review feedback
- [ ] Write PR summary
