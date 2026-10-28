# Summary — Remove unused pytest markers (#1264)

## Goal

Remove `claude_api_integration`, `formatter_integration` and `github_integration`
from this repo. No live test carries them, so they suggest coverage that does not
exist. While there, delete the dead code and stale docs left over from the Claude
SDK removal and from moving `github_operations` to mcp-workspace.

## Architectural / design changes

- **No runtime code changes.** `src/` is untouched. This is cleanup of config, tooling, test scaffolding and docs.
- **Registered marker set shrinks.** `pyproject.toml` drops `claude_api_integration` and `github_integration`. `formatter_integration` was never registered.
- **One source of truth for the unit-test filter.** `.claude/CLAUDE.md` holds the canonical set. `tests/README.md` and the `pyproject.toml` comment point to it. The files that need a literal expression (`docs/architecture/architecture.md`, `tools/get_pytest_performance_stats.bat`, `.run/...run.xml`) copy it.
- **CI selection is unchanged.** The CI unit job only loses the three markers. It does not adopt the CLAUDE.md set, which also excludes `jenkins_integration`; that's #1356. The integration job filter becomes `git_integration or install_integration`.
- **GitHub test scaffolding removed.** The `GitHubTestSetup` / `github_test_setup` / `create_github_manager` fixtures in `tests/conftest.py` are unused since the mcp-workspace move.
- **Out of scope:** mcp-workspace (uses `github_integration` correctly), `docs/tests/performance_data/` and the trend text in `runtime_statistics.md` (history), the rest of the stale test tree in `tests/README.md`, and #1356.

### The CLAUDE.md set (8 markers)

```
not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration
```

### The CI unit-job set (7 markers, no `jenkins_integration`)

```
not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not langchain_integration and not llm_integration and not textual_integration
```

## TDD note

No behaviour changes, so there are no new unit tests. Each step has a check that
plays the role of the test:
- Step 1: a collect-only run proving the removed markers select 0 tests, so CI selection can't change.
- Steps 2–3: the existing unit tests, pylint and mypy, plus the acceptance search.

## Files modified

| Step | File |
|---|---|
| 1 | `pyproject.toml` |
| 1 | `.github/workflows/ci.yml` |
| 1 | `.claude/CLAUDE.md` |
| 1 | `.run/pytest in tests - just unit tests.run.xml` |
| 1 | `tools/get_pytest_performance_stats.bat` |
| 1 | `tools/ci_coverage_summary.py` |
| 2 | `tests/llm/providers/claude/test_claude_integration.py` |
| 2 | `tests/conftest.py` |
| 2 | `vulture_whitelist.py` |
| 3 | `tests/README.md` |
| 3 | `docs/architecture/architecture.md` |
| 3 | `docs/tests/runtime_statistics.md` |
| 3 | `docs/tests/runtime-statistics-review-process.md` |

No files or folders are created or deleted (apart from these plan files).

## Steps

1. [step_1.md](./step_1.md): marker definitions and `-m` filters in config, CI and tooling
2. [step_2.md](./step_2.md): dead test code and unused GitHub fixtures
3. [step_3.md](./step_3.md): docs, plus the final acceptance search

## Acceptance (whole PR)

- A search for `claude_api_integration|formatter_integration|github_integration|@pytest\.mark\.claude_integration` finds only files under `docs/tests/performance_data/`.
- The CI unit and integration jobs select the same tests as before.
- Unit tests, pylint and mypy pass.
