# Summary — #1449 init: deploys Python-only skills, agents and knowledge base to every repo

Epic: #1455. Related: #1192, #1453 (#1453 links to the docs section added here).

## Goal

`mcp-coder init` copies `.claude/{skills,knowledge_base,agents}` unfiltered into every
repo. Non-Python repos get Python-specific prose and `knowledge_base/python.md`. After this
change:

- The prose of every deployed Markdown file is toolkit-neutral. Steps are described by
  purpose ("format, then run the project's checks and tests as CLAUDE.md maps them").
- Python specifics that leave the prose move to `knowledge_base/python.md`.
- `init` deploys `python.md` only when the repo's toolkit is `mcp-tools-py`, and otherwise
  prints a short reminder to adapt the generic files.
- Frontmatter (`tools:`, `allowed-tools`) is **unchanged**.

## Architectural / design changes

1. **One neutral source, no overlays or templates.** Skill bodies, agent bodies and the
   knowledge base stay single files. Python specifics live only in `python.md`, which
   carries a short purpose → tool list (checks, tests, format, dead code / architecture,
   refactoring). mcp-coder's own `.claude/CLAUDE.md` is not changed; mcp-coder-only details
   (pytest `-n auto`, integration markers) are already there.
2. **`init` becomes toolkit-aware, but only for one file.**
   - New helper `_is_python_toolkit(project_dir) -> bool` in `cli/commands/init.py` calls
     `toolkit_runner.load_toolkit_config`. A `ValueError` (missing / invalid table) is logged
     as a warning with its own text (which already carries the no-toolkit help) and counts as
     "not Python". `init` never fails because of the toolkit and creates no config file.
   - `_deploy_skills` gains `skip_python: bool`; when true it skips
     `knowledge_base/python.md`.
   - The toolkit is read only when deploying, not in the self-deploy skip inside mcp-coder.

   | Toolkit | `python.md` | Output |
   |---|---|---|
   | `mcp-tools-py` | deployed | nothing extra |
   | other name, e.g. `command` | skipped | reminder |
   | missing or invalid | skipped | warning (error text), then reminder |

3. **`toolkit_runner._PYTHON_TOOLKIT` becomes public `PYTHON_TOOLKIT`**, so `init` reuses
   the single definition of `"mcp-tools-py"`.
4. **Clean-tree check is stricter.** `implementation_approve`, `implementation_needs_rework`,
   `plan_approve` and `pr_comment_triage` drop the `uv.lock` exception: any tracked or
   untracked change → stop and report.
5. **`implementation_review_supervisor` reads every `.claude/knowledge_base/*.md`**, like the
   automated review prompts in `prompts.md` already do. No skill depends on `python.md`
   existing.
6. **Test guard.** A new test enforces neutral prose in every deployed Markdown file except
   `knowledge_base/python.md`. `tests/workflows/rebase/test_prompt.py` reads the repo-root
   `.claude/skills/rebase/SKILL.md` instead of the gitignored packaged copy.

Out of scope: refreshing repos that already have the files (`init` still never overwrites).

## Files created or modified

### Step 1 — `init` reads the toolkit (code, tests, docs)
- `src/mcp_coder/utils/toolkit_runner.py` — rename `_PYTHON_TOOLKIT` → `PYTHON_TOOLKIT`
- `src/mcp_coder/cli/commands/init.py` — `_is_python_toolkit`, `skip_python`, reminder
- `tests/cli/commands/test_init.py` — new class `TestInitToolkit`
- `docs/repository-setup/README.md` — new section "Adapting Deployed Files (Non-Python Repos)"
- `docs/cli-reference.md` — `init` toolkit paragraph
- `docs/repository-setup/claude-code.md` — `python.md` line notes "`mcp-tools-py` only"

### Step 2 — neutral prose (deployed `.claude/` files, prompt, tests)
- `.claude/knowledge_base/python.md` — gains the Python specifics
- `.claude/knowledge_base/planning_principles.md`
- `.claude/knowledge_base/refactoring_principles.md`
- `.claude/agents/code-engineer.md`, `.claude/agents/plan-engineer.md` (bodies only)
- `.claude/skills/{commit_push,implement_direct,implementation_finalise,implementation_review,implementation_review_supervisor,plan_review,plan_review_supervisor,pr_comment_triage,rebase,implementation_approve,implementation_needs_rework,plan_approve}/SKILL.md` (bodies only)
- `.claude/skills/rebase/rebase_design.md`
- `src/mcp_coder/prompts/prompts.md` — `Code files` strategy row
- `tests/workflows/rebase/test_prompt.py` — read repo-root `SKILL.md`
- `tests/cli/commands/test_init_deployed_neutral.py` — **new**

No new modules or packages.
