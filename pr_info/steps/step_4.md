# Step 4 — Failure-handling index

## LLM prompt

> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_4.md`).
> Create `docs/processes-prompts/processes/failure-handling.md`: an index of every failure label, each linking to the per-process doc that holds its recovery steps. Recovery details stay in the owner docs; do not duplicate them here.
> Run the file-size check, then format, then commit as one commit.

## WHERE

```
docs/processes-prompts/processes/failure-handling.md   (new)
```

## WHAT

Layout (same headings as the other docs):

- **Labels:** an index table — one row per label in `labels.json` with `"failure": true` (27 labels: 73, 74, 83, 84, 4 × `03f`, 7 × `06f`, 3 × `09f`, 3 × `14f`, 6 × `17f`). The same set is the one carrying `/check_branch_status` or `/implementation_finalise`.

  | Label | Stage | Recovery in |
  |---|---|---|
  | `status-03f:planning-failed` | Plan creation | [plan-creation.md](plan-creation.md#failure-exits) |
  | … | … | … |

  Owner docs:
  - `03f-*` → plan-creation
  - `06f-*` → implementation
  - `09f-*` → pr-creation
  - `14f-*` and `17f-*` → automated-review
  - 73 / 74 / 83 / 84 → pr-follow-up
- **Actor:** human (vscodeclaude opens a session on every failure label).
- **Slash commands:** `/check_branch_status` is the entry command for every failure label. Exception: `status-17f-tasks` auto-launches `/implementation_finalise`.
- **Failure exits — general recovery:** read the failure comment on the issue (Category / Stage / Error) → fix the cause → `mcp-coder gh-tool set-status <retry label>` (listed in the owner doc) → the bot picks the issue up again.
- 73 / 83 are crash labels (unhandled crash or Jenkins job died), not ordinary failures.

## HOW

The anchor `#failure-exits` exists in every owner doc because each has a `## Failure exits` heading.

## ALGORITHM

```
labels = [l for l in labels.json if l.get("failure")]
for l in labels: row(name, stage from prefix, link to owner doc #failure-exits)
```

Do this by hand, in `labels.json` order.

## DATA

Not applicable.

## Checks

- Every label in `labels.json` with `"failure": true` appears once (check with `search_files`).
- `check_file_size` (`max_lines=750`).
- Format, then commit: `docs(processes): add failure-handling index`.
