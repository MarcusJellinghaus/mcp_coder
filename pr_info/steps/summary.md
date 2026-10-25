# Summary — #1288 Rework process documentation

## Goal

Replace the 1,230-line `docs/processes-prompts/development-process.md` with:

- a short overview,
- ten per-process docs,
- a hand-rewritten HTML label matrix that matches `src/mcp_coder/config/labels.json` (46 labels), kept honest by one new unit test.

The docs also gain the PR follow-up workflows (`fix-conflict`, `fix-ci`, `/pr_comment_triage`), a README pitch, and a cheat sheet update.

Headline sentence used in the overview:
> You decide scope and merge; everything else can run unattended; failures come back to you as labelled issues.

## Architectural / design changes

No production code changes. The documentation is restructured as follows.

| Before | After |
|---|---|
| One monolithic `development-process.md` (workflows, prompts, failure table, PR-health, automated review) | `development-process.md` = short overview: Mermaid diagram, three tiers, process table, links. Details live in `docs/processes-prompts/processes/*.md` |
| Prompts copied inline next to the skills that replace them | A `<details>` block with a `Slash Command:` header becomes a link to `.claude/skills/<name>/SKILL.md`. Every other prompt/template moves **verbatim** into an "Additional prompt details" section of the owning doc. The one exception is "Code Review Request", which moves verbatim as the issue says |
| One failure table, missing `03f-timeout/-mcp/-prereq` and `09f-timeout/-mcp` | Each per-process doc lists its own failure exits in full. `failure-handling.md` is an index that links to the owner doc |
| HTML matrix drifted (old `status:xxx` names, missing 14 labels, duplicate 04/07 cards) | Exactly one card per label in `labels.json`, descriptions copied from `labels.json`, one new `label-commands` element per card (auto-launch line + manual/exit line), PR follow-up rows, complete Color Reference |
| No check that the docs match the code | `tests/docs/test_workflow_matrix.py`: bidirectional label-name check plus `vscodeclaude.commands` on each card |

### Fixed per-process doc layout (every file in `processes/`)

```
# <Process name>
## Labels         – label list + one-line arrow chain of transitions
## Actor          – who runs it + tier (human required / human or supervisor skill / fully automated)
## Slash commands – table: command | purpose | resulting label (link to SKILL.md)
## Failure exits  – table: label | cause | recovery   ("None — human stage." if none)
## Additional prompt details   (only if prompts were moved here; content verbatim)
```

### Rules applied in every step

- **Sources of truth:**
  - labels → `labels.json`
  - workflows → `WORKFLOW_MAPPING` (`src/mcp_coder/cli/commands/coordinator/workflow_constants.py`)
  - review routing → `src/mcp_coder/workflows/review/config.py`
  - PR follow-up exits → `src/mcp_coder/workflows/fix_conflict/core.py`, `src/mcp_coder/workflows/fix_ci/core.py`
  - slash commands → `.claude/skills/`
- Every slash command named in the docs exists under `.claude/skills/`. Do not mention `/approve` (a GitHub comment action) or `/clear` (a Claude Code built-in). Use the skills instead (`/issue_approve` covers 01→02, 04→05, 07→08).
- Headless review "**can** run" (only with `auto_review_plan` / `auto_review_implementation`, default off).
- Supervisor skills end at "ready for approval". The status change is a separate command.
- Writing style per CLAUDE.md: no filler, lead with the outcome, tables and arrow chains.
- Links may only point to files that exist at the end of the step (links stay valid at every commit).
- Every new or changed `.md` file stays under 750 lines.
- Do not mention `implement_direct` or `issue_requirements`. They are out of scope.

### Deviation from the issue's commit order (intentional)

- The `.large-files-allowlist` entry is removed in the **overview step** (step 5), not the last step. The file-size check reports stale entries, so the removal must land in the same commit that shrinks the file to keep every commit green.
- The issue's commit groups (1) and (5) are split into several steps: one commit per independent part. The relative order is unchanged.

## Verified behaviour (documented as the code shows it)

- **`fix-conflict`:**
  - 71 → 72.
  - → 10: mergeable state settled and not `dirty`, or `unknown` after a successful rebase.
  - → 74 (with comment): `dirty`, no open PR found, or `unknown` after a failed rebase.
  - → 73: crash (`run_guarded`, or Jenkins watchdog).
  - Branch undetermined → exit 1, label stays 72.
- **`fix-ci`:**
  - 81 → 82.
  - → 10: CI green.
  - → 84 (with comment, Category line): formatter-config error, LLM timeout, MCP unavailable, or fix attempts exhausted.
  - → 83: crash.
  - Branch undetermined → exit 1, label stays 82.
- **`status-91`:** `/pr_comment_triage` → `mcp-coder gh-tool set-status status-10:pr-created` at the end.
- **Review lanes:**
  - Plan: 14 → 14i → 05 (success) / 04 (escalate) / `14f-*` (error).
  - Code: 17 → 17i → 08 / 07 / `17f-*`.
- **`create-plan` `03f-prereq` causes:** dirty working dir, issue not found, base branch missing, branch creation failed, `pr_info/` already exists, `pr_info/` creation failed.
- **vscodeclaude launch:** one command → interactive `<cmd> <issue#>`. Several commands → the first runs automated, the last resumes interactively.

## Files

### Created

```
docs/processes-prompts/processes/issue-discussion.md
docs/processes-prompts/processes/plan-creation.md
docs/processes-prompts/processes/plan-review.md
docs/processes-prompts/processes/implementation.md
docs/processes-prompts/processes/code-review.md
docs/processes-prompts/processes/pr-creation.md
docs/processes-prompts/processes/pr-merge.md
docs/processes-prompts/processes/pr-follow-up.md
docs/processes-prompts/processes/automated-review.md
docs/processes-prompts/processes/failure-handling.md
tests/docs/__init__.py
tests/docs/test_workflow_matrix.py
```

### Modified

```
docs/processes-prompts/development-process.md        (rewritten as short overview)
docs/processes-prompts/github_Issue_Workflow_Matrix.html (hand rewrite)
docs/processes-prompts/claude_cheat_sheet.md
README.md
docs/README.md
docs/cli-reference.md
docs/coordinator-vscodeclaude.md
docs/getting-started/label-setup.md
.large-files-allowlist
```

These may need edits only if `tools/lychee_check.bat` reports a broken link in them. Their links to the overview stay valid:
`docs/architecture/architecture.md`, `docs/configuration/claude-code.md`, `docs/configuration/config.md`, `docs/repository-setup/README.md`, `docs/repository-setup/claude-code.md`, `project_idea.md`.

### Not touched

`docs/processes-prompts/refactoring-guide.md`, all of `src/`.

## Steps

| Step | Commit |
|---|---|
| 1 | Per-process docs, stages 1–4: `issue-discussion`, `plan-creation`, `plan-review`, `implementation` |
| 2 | Per-process docs: `code-review`, `pr-creation`, `pr-merge` |
| 3 | Per-process docs: `pr-follow-up`, `automated-review` (+ back-links from steps 1–2 docs) |
| 4 | `failure-handling.md` index |
| 5 | Overview rewrite of `development-process.md` + allowlist removal |
| 6 | Incoming link and anchor updates + lychee run |
| 7 | Consistency test (first) + HTML matrix rewrite |
| 8 | README pitch section |
| 9 | Cheat sheet update |
