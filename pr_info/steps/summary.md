# Harden quality-tool isolation: import contract and subprocess rule (#1193)

Part of epic #1192. Lands on `main` before the epic branch is created.

## Goal

Python quality tools are reachable only through the quality-tool boundary, for both imports and subprocess calls. Today that boundary is the `mcp_coder.mcp_tools_py` shim; #1195 moves the workflows onto the toolkit interface.

## Architectural / design changes

No production code changes and no runtime behaviour change. Two static guards are added:

| Guard | Catches | Runs in |
|---|---|---|
| `quality_tools_isolation` contract in `.importlinter` | `import` of a quality tool anywhere in `mcp_coder` | CI job `import-linter` |
| `quality-tools` rule in `RULES`, `tools/check_forbidden_calls.py` | Literal argv lists that run a quality tool from `src/` | CI job `forbidden-calls` |

Both are needed because import-linter cannot see subprocess calls, and subprocess is how these tools actually run.

Design decisions:

- **One contract for all tools.** They share one boundary, and a failure still names the imported module.
- **No `ignore_imports`.** External packages are leaf nodes in the graph, so `mcp_coder -> mcp_tools_py -> pytest` isn't seen as a chain.
- **`_pytest` is listed separately.** It is its own top-level package.
- **One regex for the rule.** A single alternation covers `["<tool>"`, `"-m", "<tool>"` and `"run", "<tool>"`, in the existing `Rule` shape. The match starts at `[`, `"-m"` or `"run"`, so that is the line reported.
- **The rule message names the boundary**, not `mcp_coder.mcp_tools_py`, which #1195 moves callers away from.
- **`black` and `isort` are not covered.** #1292 retired them on purpose.
- **The rule's tool list stays at the nine tools from the issue.** `importlinter` is forbidden as an import only: the installed package has no `__main__.py`, so `-m importlinter` wouldn't run.
- **The rule is a text scan.** It guards against accidents, not deliberate bypass. See the known limits in the step 2 docstring.
- **The contract is proved by a one-off check, not a permanent test.** A misspelled forbidden name passes `lint-imports` silently, because import-linter skips forbidden modules that aren't in the graph. The result is recorded in the contract commit's message.

## Files

Created: none, apart from these plan files. Two throwaway files are created and deleted during implementation: `src/mcp_coder/_quality_probe.py` (step 1) and `.scratch/test_probe.py` (step 2).

Modified:

| File | Step | Change |
|---|---|---|
| `.importlinter` | 1 | Add `quality_tools_isolation` after `mcp_checker_isolation` |
| `tests/tools/test_check_forbidden_calls.py` | 2 | One parametrized test, 54 cases |
| `tools/check_forbidden_calls.py` | 2 | `_QUALITY_TOOLS`, new `RULES` entry, module docstring |
| `tools/forbidden_calls_check.sh` | 2 | Comment |
| `tools/forbidden_calls_check.bat` | 2 | Comment |
| `docs/repository-setup/quality-and-security-checks.md` | 2 | `forbidden-calls` entry |
| `docs/architecture/enforcement.md` | 2 | "Shim boundary" section |

No changes under `src/`, and none to `pyproject.toml` or `tach.toml`. Declared dependencies stay.

## Steps

1. [Import contract and one-off check](./step_1.md)
2. [Subprocess rule, tests and docs](./step_2.md)
