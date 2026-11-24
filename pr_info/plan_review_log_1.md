# review-plan review log 1

## Round 1 — 2026-11-24
**Findings**:
Reviewing the plan: checking the conftest toolkit stub and the rebase test next.Nearly done — checking whether any skill test asserts body content against `allowed-tools`.pr_info/steps/step_2.md:97 — medium — `implement_direct` step 5 becomes "run the project's checks and tests as CLAUDE.md maps them", but mcp-coder's `.claude/CLAUDE.md` requires only pylint/pytest/mypy. The ruff step would move only to `python.md`, and `implement_direct` never reads `python.md`. So mcp-coder's own `implement_direct` sessions would stop running ruff, which breaks the issue's constraint that mcp-coder sessions keep every removed Python step. Fix: make the wording "as CLAUDE.md and the knowledge base's language notes map them", or explicitly accept dropping ruff there.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_2.md (~line 97), change the new implement_direct step 5 wording from "run the project\'s checks and tests as CLAUDE.md maps them" to "run the project\'s checks and tests as CLAUDE.md and the knowledge base\'s language notes (e.g. python.md) map them", and state that implement_direct reads the matching language note. mcp-coder\'s implement_direct sessions then keep the ruff step that moves into python.md, as the issue requires.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-24
**Findings**:
Checking the rest of `load_toolkit_config`, then the skill files the plan edits.Verifying the rebase test coupling, then emitting the report.pr_info/steps/step_2.md:122 — medium — Step 2 moves the Python planning and refactoring rules out of `planning_principles.md` and `refactoring_principles.md` and into `python.md`. These are the test layout, "apply pyproject.toml / mypy overrides during planning", pylint `R0401` / `TYPE_CHECKING`, `try/except ImportError`, `__init__.py` / `conftest.py`, and the pytest checks used to verify a move. But `plan_review_supervisor` (Setup, `.claude/skills/plan_review_supervisor/SKILL.md:23-25`), `plan_review` (`SKILL.md:39`) and `issue_analyse_supervisor` (`SKILL.md:20-21`) read only the named principle files, never `python.md`. So mcp-coder's interactive planning and issue-analysis sessions lose these rules. This breaks the issue's constraint that mcp-coder sessions keep every Python step removed from the prose. It is the same gap round 1 fixed for `implement_direct`. Fix: change the Setup knowledge-base list in `plan_review_supervisor` and `issue_analyse_supervisor` to "read every file under `.claude/knowledge_base/` (`*.md`)", as step 2 already does for `implementation_review_supervisor`.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_2.md, add edits to the Setup knowledge-base reading lists in `.claude/skills/plan_review_supervisor/SKILL.md` (lines 23-25), `.claude/skills/plan_review/SKILL.md` (line 39) and `.claude/skills/issue_analyse_supervisor/SKILL.md` (lines 20-21). Each should say "read every file under `.claude/knowledge_base/` (`*.md`)", the same wording step 2 already uses for `implementation_review_supervisor`. Those sessions then still get the Python planning and refactoring rules that move into `python.md`.'], escalate_reason=None)
**Changes**:
applied
