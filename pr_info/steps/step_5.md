# Step 5 — Overview rewrite + allowlist removal

## LLM prompt

> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_5.md`).
> Replace the whole content of `docs/processes-prompts/development-process.md` with the short overview described below. All detail now lives in `processes/*.md` (steps 1–4).
> In the same commit, remove the `docs/processes-prompts/development-process.md` line from `.large-files-allowlist`. The file-size check reports stale entries, so both changes must land together.
> Run the file-size check, then format, then commit as one commit.

## WHERE

```
docs/processes-prompts/development-process.md   (rewrite, target < 150 lines)
.large-files-allowlist                          (remove one line)
```

## WHAT — overview content, in order

1. `# Development Process`, then the headline sentence:
   > You decide scope and merge; everything else can run unattended; failures come back to you as labelled issues.
2. One line: what mcp-coder is and why → link to the README pitch section, `../../README.md`. The anchor is added in step 8, so link to the file only. Do not repeat the pitch.
3. **One Mermaid `flowchart`.**
   - **Nodes:** the labels 01, 02, 04, 05, 07, 08, 10, 71, 81, 91, plus "Merged". No failure labels.
   - **Edges:**
     - `01 -->|/issue_analyse … /issue_approve| 02`
     - `02 -->|create-plan| 04`
     - `04 -->|/plan_approve| 05`
     - `05 -->|implement| 07`
     - `07 -->|/implementation_approve| 08`
     - `08 -->|create-pr| 10`
     - `10 -->|merge| Merged`
     - follow-up loop: `10 --> 71 -->|fix-conflict| 10`, `10 --> 81 -->|fix-ci| 10`, `10 --> 91 -->|/pr_comment_triage| 10`
     - dashed optional headless review: `02 -.->|auto_review_plan| 05` and `05 -.->|auto_review_implementation| 08`, labelled "can run headless (review-plan / review-implementation)"
   - **Tiers:** three `classDef`s (colours) with a legend line under the diagram:
     - *human required*: merge, 10;
     - *human or supervisor skill*: 01, 04, 07, 91;
     - *fully automated* (coordinator / vscodeclaude / Jenkins): 02, 05, 08, 71, 81.
   - Subgraphs only for stage grouping, if they help layout.
   - Note: "Renders on GitHub. Full state machine incl. failure labels: [workflow matrix](github_Issue_Workflow_Matrix.html)."
4. **Process table:**

   | Process | Trigger label | Actor | Slash commands | Doc |
   |---|---|---|---|---|

   One row per doc. All 10 docs from `processes/`:
   - issue discussion, plan creation, plan review, implementation, code review, PR creation, PR merge, PR follow-up, automated review, failure handling;
   - the failure-handling row has trigger "any failure label".

   Slash commands are only those that exist under `.claude/skills/`.
5. **Links:** [Claude Code Cheat Sheet](claude_cheat_sheet.md), [Label Setup](../getting-started/label-setup.md) (prerequisite), [Workflow Matrix](github_Issue_Workflow_Matrix.html).

Do **not** keep:
- the PyCharm anchor note;
- the old diagrams, prompts, tables or numbered sections.

## HOW

- The new links point to `processes/<name>.md`; all of them exist after steps 1–4.
- The old anchors (`#8-failure-handling`, `#10-pr-health-status-10`) disappear here. Step 6 updates their incoming links. The `.md` links stay valid in this commit, so only the fragments go stale until step 6.

## ALGORITHM

```
overwrite development-process.md with sections 1–5
delete line "docs/processes-prompts/development-process.md" from .large-files-allowlist
check_file_size(max_lines=750) -> no new files listed and no stale allowlist entry
```

## DATA

Not applicable.

## Checks

- `check_file_size` (`max_lines=750`).
- If the check output still flags `development-process.md` as a stale allowlist entry after the edit, write one line to `pr_info/.blocked.txt` and stop.
- Format, then commit: `docs(processes): rewrite development-process.md as short overview`.
