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

### Step 1: `tach_docs.py` writes to `docs/architecture/dependencies/` — [step_1.md](./steps/step_1.md)

- [x] Implementation: update `tests/tools/test_tach_docs.py` first (watch it fail), then fix `tools/tach_docs.py` and the `tach_docs.sh` / `.bat` header comments
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: pydeps scripts write to `docs/architecture/dependencies/` — [step_2.md](./steps/step_2.md)

- [ ] Implementation: path replacement in `tools/pydeps_graph.sh`, `tools/pydeps_graph.bat` and the `pydeps_graph.html` command snippet
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Create `enforcement.md`, update README badge and docs index — [step_3.md](./steps/step_3.md)

- [ ] Implementation: write `docs/architecture/enforcement.md`, update the `README.md` architecture badge and the `docs/README.md` entry; verify all relative links resolve
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Cut down `docs/architecture/dependencies/readme.md` — [step_4.md](./steps/step_4.md)

- [ ] Implementation: replace intro with pointer, delete covered sections, trim Vulture section, fix comparison-table row and Generated Files line
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Cut down `python.md` *Architecture Enforcement*, fix the MCP note — [step_5.md](./steps/step_5.md)

- [ ] Implementation: reduce `## Architecture Enforcement` to the link plus *Customize* notes (keep required headings), replace the *For Claude Code* MCP note
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: Replace `architecture.md` §8 subsections with a pointer — [step_6.md](./steps/step_6.md)

- [ ] Implementation: replace *Architectural Boundary Enforcement* bullets with the pointer, delete *Dead Code Detection*, leave *Refactoring Guidelines* unchanged
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: Add `enforcement.md` links to the #1181 hub — [step_7.md](./steps/step_7.md)

- [ ] Implementation: add `enforcement.md` links to the overview table and the Architecture, File size, Dependencies and Repo hygiene sections of `quality-and-security-checks.md`; run the final path sweep
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against `main` and address findings
- [ ] PR summary prepared
