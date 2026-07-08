# Decisions — #438 plan review

Reviewer-approved updates applied to the implementation plan.

- **F401 pruning churns across steps 1–7, not one-shot.** Clarified in the
  summary's "KISS: import handling" section that `ruff_fix(select=["F401"])` on
  the original `test_status_display.py` keeps running as the file shrinks; each
  step re-runs F401 on the files it touches. It is not a cleanup completed in
  Step 1.
- **Vulture is not a blocking gate for this move.** Noted in the summary's
  "Per-step verification" section that pre-existing vulture warnings for this
  file (e.g. `return_value`, `repo_url`) travel with the moved class bodies and
  are informational for this mechanical test-only move — not a step failure.
- **Pytest marker exclusions aligned with CLAUDE.md.** Updated the
  `run_pytest_check` marker-exclusion string in all step files to the canonical
  fast-unit invocation excluding all ten integration markers (added
  `copilot_cli_integration`, `jenkins_integration`, `llm_integration`,
  `textual_integration`).
