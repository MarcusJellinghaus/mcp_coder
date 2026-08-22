# Step 8 — Docs: failure-label tables, HTML matrix, architecture note

Documentation only, no tests. Both label tables are hand-maintained: the repo's only HTML
generator is `tools/tach_docs.py`, which emits the dependency graph and report, and nothing
references `github_Issue_Workflow_Matrix.html` except the link in `docs/README.md:32`.
Hand-edit both.

## WHERE

| File | Change |
|------|--------|
| `docs/processes-prompts/development-process.md` | 4 rows in the failure-label table (`:1125-1140`) |
| `docs/processes-prompts/github_Issue_Workflow_Matrix.html` | 4 CSS rules (`:216-220`) + 4 cards in the `06f` `failed-stack` (`:402-421`) |
| `docs/architecture/architecture.md` | one bullet under the implement workflow (`~:290-297`) |

## WHAT

### A. `development-process.md`

The table is missing three existing labels as well as the new one. Add all four after the
`status-06f-timeout` row; every other `status-06f-*` row's Recovery column reads
`mcp-coder gh-tool set-status status-05:plan-ready`, so all four use that:

| Label | Triggered When |
|---|---|
| `status-06f-prep:task-tracker-prep-failed` | Task tracker preparation failed |
| `status-06f-mcp:mcp-unavailable` | MCP server unavailable during implementation |
| `status-06f-nochange:no-changes-after-retries` | LLM produced no file changes after 3 retry attempts |
| `status-06f-blocked:implementation-blocked` | Agent wrote `pr_info/.blocked.txt` — it could not verify the work and refused to claim it |

### B. `github_Issue_Workflow_Matrix.html`

Four CSS rules beside the existing failure colours, matching the `color` values in
`labels.json`:

```css
.status-task-tracker-prep-failed { --label-color: #b60205; }
.status-mcp-unavailable          { --label-color: #e99695; }
.status-no-changes-after-retries { --label-color: #d93f0b; }
.status-implementation-blocked   { --label-color: #d93f0b; }
```

Four matching cards in the stage-6 `failed-stack`, following the existing card markup
(`label-card highlight-red <class>`, `step-number`, `label-name`, `label-description`,
`status-badge badge-failed`). Suggested `step-number` / badge values:

| class | step-number | badge |
|---|---|---|
| `status-task-tracker-prep-failed` | `6f-prep` | `Failed` |
| `status-mcp-unavailable` | `6f-mcp` | `MCP Failed` |
| `status-no-changes-after-retries` | `6f-nc` | `No Changes` |
| `status-implementation-blocked` | `6f-b` | `Blocked` |

### C. `architecture.md`

One bullet under `workflows/implement/`, beside the existing `core.py` /
`task_processing.py` entries:

```
  - **Blocked channel**: an agent that cannot verify its work writes one line to `pr_info/.blocked.txt`; the workflow reads it before the files-changed check, fails the run with `status-06f-blocked` and surfaces the text. Task results travel as `TaskOutcome(success, reason, detail)`.
```

## HOW

Scope discipline: `development-process.md` also omits `status-03f-timeout`,
`status-03f-mcp`, `status-03f-prereq`, `status-09f-timeout` and `status-09f-mcp`. **Those
are other lanes and stay out of scope** — this issue fixes the implement lane's three
omissions plus the new label, nothing more.

## ALGORITHM

None.

## DATA

None.

## TESTS

None — no test reads these files. Verify by eye that the four `labels.json` colours match
the four CSS `--label-color` values, and that the table row order matches the label naming
convention used by the surrounding rows.

## COMMIT

`Document status-06f-blocked and the three missing 06f labels`

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_8.md, then implement Step 8 only.

Documentation only — no source or test changes. Three files:
A. docs/processes-prompts/development-process.md — add four rows to the failure-label
   table: the new status-06f-blocked plus the three implement-lane labels the table has
   always been missing (-prep, -mcp, -nochange). Recovery column is
   "mcp-coder gh-tool set-status status-05:plan-ready" for all four, matching the
   surrounding 06f rows.
B. docs/processes-prompts/github_Issue_Workflow_Matrix.html — four --label-color CSS rules
   and four matching cards in the stage-6 failed-stack. Both tables are hand-maintained;
   no generator produces this file. Match the hex colours to labels.json exactly.
C. docs/architecture/architecture.md — one bullet describing the blocked channel and
   TaskOutcome under workflows/implement/.

Stay in scope: development-process.md also omits several status-03f-* and status-09f-*
labels. Those belong to other lanes — leave them alone.

Use MCP tools for all file operations. Run the three checks (they should be unaffected),
then ./tools/format_all.sh and make exactly one commit.
```
