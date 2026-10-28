# Refactoring Principles

Rules for moving code without changing it. Repo-specific details (size limits, allowlists, import contracts) live in the repo's own docs, e.g. `docs/processes-prompts/refactoring-guide.md` where it exists.

## Key Rules

- **Move, don't change.** Logic changes belong in a separate PR.
- **Use the refactoring tools** (`move_symbol`, `move_module`) — they update imports. Don't move code by hand.
- **Clean deletion, no legacy artifacts.** No stubs, no re-exports for backward compatibility.
- **Small steps.** Review the compact diff and keep it short — go step by step.
- **Merge two steps when the state between them is not solid** — if code doesn't work or tests can't pass after the first step.
- **Tests mirror source structure.**

## Allowed edits

Besides moved code, a pure move may only contain:

- Import statements, including optional-import `try/except ImportError` blocks
- Mock/patch target strings that must follow a moved symbol
- Module-level boilerplate a new file needs: a logger, a module docstring, a copy of the source's module-level test markers
- Package files (`__init__.py`, `conftest.py`) needed by the move
- Stale names in comments and docstrings — replace the names only
- Removing comments left with nothing under them
- Size-check allowlist entries

Anything else is a code change: stop and report.

## How to move

1. Plan each tool call so the tool produces the final result itself.
2. If it doesn't, try other tool options first (different grouping or order).
3. Only then make the smallest hand edit: move whole top-level statements, change nothing inside them.

## Plan the layout

- **Map each test to the module it calls**, not the one it patches. Misplaced tests move to their module's test file.
- **Check the hard constraints first:** a file that is one big class, a single unit larger than the size budget, file-local fixtures that tests depend on, definitions that must stay above their users.
- **Prefer layouts that keep shared helpers in place and move only whole classes or functions.**

## Verify

- **Compact diff:** only moves, imports and allowed edits remain.
- **A green test run doesn't prove a pure move.** Check that nothing was silently lost: test count, markers, patch targets that still resolve but patch nothing, fixtures no longer applied, names shadowed in the destination.
- Run all checks — pytest, pylint, mypy, ruff, import contracts, file size.

## Refactoring issues

- **Decisions and constraints, not a pre-computed implementation.** Keep the target layout, ordering constraints, exceptions and checks. Line ranges, import lists and counts go stale and duplicate the planning step.
- **Link to these rules;** don't copy them into each issue.
- **No line numbers in files that other open issues also edit.** Refer to the path or symbol.
- **Every prohibition needs a way out:** an allowed fallback or an explicit "stop and report".
- **Every step and check must be doable with the implementer's tools.**
