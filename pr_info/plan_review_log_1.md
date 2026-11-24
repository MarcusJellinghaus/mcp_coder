# review-plan review log 1

## Round 1 — 2026-11-24
**Findings**:
Reviewing the plan: checking the conftest toolkit stub and the rebase test next.Nearly done — checking whether any skill test asserts body content against `allowed-tools`.pr_info/steps/step_2.md:97 — medium — `implement_direct` step 5 becomes "run the project's checks and tests as CLAUDE.md maps them", but mcp-coder's `.claude/CLAUDE.md` requires only pylint/pytest/mypy. The ruff step would move only to `python.md`, and `implement_direct` never reads `python.md`. So mcp-coder's own `implement_direct` sessions would stop running ruff, which breaks the issue's constraint that mcp-coder sessions keep every removed Python step. Fix: make the wording "as CLAUDE.md and the knowledge base's language notes map them", or explicitly accept dropping ruff there.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_2.md (~line 97), change the new implement_direct step 5 wording from "run the project\'s checks and tests as CLAUDE.md maps them" to "run the project\'s checks and tests as CLAUDE.md and the knowledge base\'s language notes (e.g. python.md) map them", and state that implement_direct reads the matching language note. mcp-coder\'s implement_direct sessions then keep the ruff step that moves into python.md, as the issue requires.'], escalate_reason=None)
**Changes**:
applied
