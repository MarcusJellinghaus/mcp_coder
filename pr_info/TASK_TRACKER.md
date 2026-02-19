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

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

### Step 1: Extend `get_branch_diff()` with `ansi` parameter

See [step_1.md](./steps/step_1.md) for full details.

- [ ] Implement: add `ansi: bool = False` parameter to `get_branch_diff()` in `src/mcp_coder/utils/git_operations/diffs.py`; when `True`, prepend `--color=always` and `--color-moved=dimmed-zebra` to diff args
- [ ] Implement: add two new test methods to `TestDiffOperations` in `tests/utils/git_operations/test_diffs.py` (marked `@pytest.mark.git_integration`)
- [ ] Quality checks: run pylint, pytest, mypy and resolve all issues found
- [ ] Prepare git commit message for Step 1 changes

---

### Step 2: Create `compact_diffs.py` core module + unit tests

See [step_2.md](./steps/step_2.md) for full details.

- [ ] Implement: create `src/mcp_coder/utils/git_operations/compact_diffs.py` with all dataclasses, constants, and five-layer pure functions as specified
- [ ] Implement: create `tests/utils/git_operations/test_compact_diffs.py` with all test classes using synthetic string inputs only (no git repos)
- [ ] Quality checks: run pylint, pytest, mypy and resolve all issues found
- [ ] Prepare git commit message for Step 2 changes

---

### Step 3: CLI command — `git_tool.py` + parser + `main.py` wiring + tests

See [step_3.md](./steps/step_3.md) for full details.

- [ ] Implement: create `src/mcp_coder/cli/commands/git_tool.py` with `execute_compact_diff()` function mirroring `gh_tool.py` structure
- [ ] Implement: add `add_git_tool_parsers()` to `src/mcp_coder/cli/parsers.py`
- [ ] Implement: wire `_handle_git_tool_command()` and routing in `src/mcp_coder/cli/main.py`
- [ ] Implement: create `tests/cli/commands/test_git_tool.py` following `test_gh_tool.py` structure
- [ ] Quality checks: run pylint, pytest, mypy and resolve all issues found
- [ ] Prepare git commit message for Step 3 changes

---

### Step 4: Update `implementation_review.md` + delete prototype tools

See [step_4.md](./steps/step_4.md) for full details.

- [ ] Implement: edit `.claude/commands/implementation_review.md` — replace `Bash(git diff:*)` with `Bash(mcp-coder git-tool compact-diff:*)` in frontmatter, remove `BASE_BRANCH` assignment line, replace `git diff` command with `mcp-coder git-tool compact-diff --exclude "pr_info/.conversations/**"`
- [ ] Implement: verify `tools/compact_diff.py` and `tools/git-refactor-diff.py` are not imported in `src/` or `tests/`, then delete both files
- [ ] Quality checks: run pylint, pytest, mypy and resolve all issues found
- [ ] Prepare git commit message for Step 4 changes

---

### Step 5: Update documentation

See [step_5.md](./steps/step_5.md) for full details.

- [ ] Implement: add `git-tool compact-diff` section to `docs/cli-reference.md` mirroring the existing `gh-tool` section style
- [ ] Implement: add `compact_diffs.py` note to `docs/architecture/architecture.md` in the `utils/git_operations` section
- [ ] Implement: add compact diff bullet/sentence to `README.md` under an appropriate existing section
- [ ] Quality checks: run pylint, pytest, mypy and resolve all issues found
- [ ] Prepare git commit message for Step 5 changes

---

## Pull Request

- [ ] Review all changes across all steps for correctness and consistency
- [ ] Verify all quality checks pass (pylint, pytest, mypy) across the full codebase
- [ ] Confirm deleted prototype tools (`tools/compact_diff.py`, `tools/git-refactor-diff.py`) have no remaining references
- [ ] Write PR summary covering: problem solved, solution approach (two-pass pipeline), files created/modified/deleted, and key design decisions (D1–D7)
