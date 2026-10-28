# Step 3 — Docs, plus the final acceptance search

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` exactly.
> Update the four docs files below to remove the three markers and the stale
> `github_operations` references. Leave everything under `docs/tests/performance_data/`
> and the trend text in `runtime_statistics.md` unchanged. Run the acceptance search
> and the checks, then make one commit.

## WHERE / WHAT

### `tests/README.md`
- Quick Start:
  - Replace `pytest -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"` with the comment `# See the marker filter in .claude/CLAUDE.md`. Keep the `# Fast unit tests only` heading comment.
  - Delete the `pytest -m claude_api_integration`, `pytest -m formatter_integration` and `pytest -m github_integration` lines.
  - Delete `pytest tests/utils/github_operations/    # All GitHub operations tests`.
- Test Structure tree: delete the `github_operations/` entry and its three child lines (`test_github_utils.py`, `test_issue_manager.py`, `test_issue_manager_integration.py`). Leave the rest of the tree alone.
- Test Markers table: delete the `claude_api_integration`, `formatter_integration` and `github_integration` rows.
- Marking Tests code block: delete the three decorated example functions for those markers, together with their blank-line separators.

### `docs/architecture/architecture.md`
- Replace the whole `- **GitHub integration**: \`utils/github_operations/\` ...` block (line ~299 through `  - Smoke tests: \`test_github_integration_smoke.py\` ...`, line ~317) with one line:
  `- **GitHub integration**: GitHub operations live in mcp-workspace (not in this repo)`
- Test categories list: delete the `claude_api_integration` entry and the `github_integration` entry, each with its `When to use` / `Requirements` sub-bullets.
- `- **Recommended**:` line (~451): set the `-m` string to the CLAUDE.md set from the summary.
- Under "Workflow Engine": delete the line `- \`src/mcp_coder/utils/github_operations/\` - GitHub API integration`.

### `docs/tests/runtime_statistics.md`
- Performance thresholds:
  - Delete the `### Claude API Integration Tests` block and the `### GitHub Integration Tests` block (heading plus 3 bullets each).
  - Rename `### Formatter Integration Tests` to `### Checker Integration Tests (\`checker_integration\`)`.
- Known Slow Tests Registry:
  - Delete `#### Claude API Integration Tests (Exceeding 30.0s threshold)` and its line.
  - Delete `#### GitHub Integration Tests (Exceeding 30.0s threshold)` and its line.
  - Rename both `#### Formatter Integration Tests (...)` headings to `#### Checker Integration Tests (...)`, keeping the threshold text in parentheses.
- Approved slow tests:
  - Rename `### Claude Integration Tests (\`@pytest.mark.claude_integration\`)` to `### Claude CLI Integration Tests (\`@pytest.mark.claude_cli_integration\`)`.
  - In that section, delete the entries (with their sub-bullets) for `test_basic_cli_api_integration` and `test_interface_contracts`. Keep `test_env_vars_propagation` and `test_session_continuity`.
  - Delete the whole `### Claude API Integration Tests`, `### Formatter Integration Tests` and `### GitHub Integration Tests` sections, up to (but not including) the `---` that follows.
- Don't touch the Performance Trends text.

### `docs/tests/runtime-statistics-review-process.md`
- Thresholds table:
  - `| Claude CLI/API Integration | 5.0s/10.0s | 10.0s/30.0s | Network overhead |` becomes `| Claude CLI Integration | 5.0s | 10.0s | Network overhead |`
  - `| Formatter Integration | 3.0s | 8.0s | Code analysis |` becomes `| Checker Integration | 3.0s | 8.0s | Code analysis |`
  - Delete the `| GitHub Integration | ... |` row.

## HOW / ALGORITHM / DATA

No code. Markdown edits only.

## Acceptance search (acts as the test)

Search the whole project for:

```
claude_api_integration|formatter_integration|github_integration|@pytest\.mark\.claude_integration
```

Expected: every hit is under `docs/tests/performance_data/` (the `pr_info/` plan files may mention the names too; ignore those).
If a hit remains elsewhere, fix it within this step's files. If it is in a file no step lists, write one line to `pr_info/.blocked.txt` naming the file, and stop.

## Checks, then commit

1. Run `mcp__mcp-tools-py__run_format_code`.
2. Run pylint, mypy, and the unit tests with the CLAUDE.md command (`-n auto`).
3. Commit once, e.g. `docs: remove unused pytest markers and stale github_operations references`.
