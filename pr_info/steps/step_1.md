# Step 1 — Per-process docs: issue discussion, plan creation, plan review, implementation

## LLM prompt

> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_1.md`).
> Create the four docs listed under WHERE in `docs/processes-prompts/processes/`. Use the fixed layout and rules from the summary.
> Take content from the current `docs/processes-prompts/development-process.md`. Do not modify it in this step.
> Verify every label, transition and slash command against the code sources named in the summary.
> Links may only point to files that already exist (no links yet to `code-review.md`, `automated-review.md`, `failure-handling.md` etc.).
> Run the file-size check, then format, then commit as one commit.

## WHERE

```
docs/processes-prompts/processes/issue-discussion.md   (new)
docs/processes-prompts/processes/plan-creation.md      (new)
docs/processes-prompts/processes/plan-review.md        (new)
docs/processes-prompts/processes/implementation.md     (new)
```

Relative link prefixes from `processes/`:
- skills: `../../../.claude/skills/<name>/SKILL.md`
- prompts: `../../../src/mcp_coder/prompts/prompts.md#<anchor>`
- config: `../../configuration/config.md`

## WHAT — content per doc

Line numbers refer to the **current** `development-process.md`. It is unchanged until step 5.

### `issue-discussion.md`

- **Labels:**
  - `status-01:created` (human_action) → `status-02:awaiting-planning`.
  - Major restart from later stages lands back on 01 (via `mcp-coder gh-tool set-status status-01:created`).
- **Actor:** human or supervisor skill.
  - vscodeclaude auto-launches `/issue_analyse` then `/discuss` (from `labels.json`).
  - `/issue_analyse_supervisor` runs the analysis through subagents and approves (→ 02), but escalates scope/requirements questions to the user.
- **Slash commands:** `/issue_analyse`, `/discuss`, `/issue_update`, `/issue_create`, `/issue_approve` (→ 02), `/issue_analyse_supervisor` (→ 02).
- **Failure exits:** "None — human stage."
- **Prompts:**
  - Lines 188–258 (five blocks with `Slash Command:` header) → links only.
  - Lines 262–271 "Add analysis to Issue Text" → move verbatim into "Additional prompt details".

### `plan-creation.md`

- **Labels:**
  - `status-02:awaiting-planning` (bot_pickup) → `status-03:planning` (bot_busy) → `status-04:plan-review`.
  - Goes to `status-14:plan-review-bot` instead when `auto_review_plan` is on.
- **Actor:** fully automated — coordinator dispatches `create-plan` on Jenkins (`WORKFLOW_MAPPING`).
- **Slash commands:** none for the bot. The failure labels auto-launch `/check_branch_status`.
- **Failure exits:** recovery for all four labels: fix the cause, then `mcp-coder gh-tool set-status status-02:awaiting-planning`.

  | Label | Cause |
  |---|---|
  | `status-03f:planning-failed` | Any other error or crash |
  | `status-03f-timeout:planning-llm-timeout` | LLM timeout |
  | `status-03f-mcp:planning-mcp-unavailable` | MCP server(s) failed to connect |
  | `status-03f-prereq:planning-prereq-failed` | Dirty working dir, issue not found, base branch missing, branch creation failed, `pr_info/` already exists, or `pr_info/` creation failed |

  Source: `src/mcp_coder/workflows/create_plan/core.py` (`FAILURE_LABELS`).
- **Prompts:** lines 299–310 → keep the three `prompts.md` links. Nothing else to move.

### `plan-review.md`

- **Labels:**
  - `status-04:plan-review` (human_action) → `status-05:plan-ready`.
  - Major restart → `status-02:awaiting-planning`, after deleting the plan files (from lines 473–476).
- **Actor:** human or supervisor skill.
  - vscodeclaude auto-launches `/plan_review_supervisor`.
  - The supervisor ends at "ready for approval". `/plan_approve` is a separate step.
- **Slash commands:** `/plan_review_supervisor`, `/plan_review`, `/discuss`, `/plan_update`, `/commit_push`, `/plan_approve` (→ 05), `/issue_approve` (04 → 05).
- **Failure exits:** "None — human stage."
- **Prompts:**
  - Lines 349–428 skill blocks → links.
  - Move verbatim into "Additional prompt details":
    - lines 404–412 "Commit updated implementation plan" message;
    - lines 430–471 "Requirements Update Note", "Consistency Review", "Change Summary Request".

### `implementation.md`

- **Labels:**
  - `status-05:plan-ready` (bot_pickup) → `status-06:implementing` (bot_busy) → `status-07:code-review`.
  - Goes to `status-17:code-review-bot` instead when `auto_review_implementation` is on.
- **Actor:** fully automated — coordinator dispatches `implement` on Jenkins.
- **Slash commands:** `/implementation_finalise` (finish open tasks after a failed run), `/commit_push`, `/check_branch_status`.
- **Failure exits:** copy the seven `06f-*` rows from lines 1130–1136. Every label in `labels.json` with a `status-06f` prefix must appear. Recovery for all: `mcp-coder gh-tool set-status status-05:plan-ready`.
- **Prompts:**
  - Lines 529–532 → keep the `prompts.md` links.
  - Lines 540–723 "Detailed Implementation Process" → move verbatim into "Additional prompt details".
  - Lines 725–727 `/commit_push` block → link only.

## HOW

Pure Markdown, no code. Each file starts with `# <Process name>` and a one-sentence purpose line.

## ALGORITHM

```
for doc in four docs:
    write Labels / Actor / Slash commands / Failure exits from code-verified facts
    for each <details> block in the source range:
        if it has "Slash Command:" header -> add link to SKILL.md in Slash commands table
        else -> copy block verbatim under "## Additional prompt details"
```

## DATA

Not applicable (docs only).

## Checks

- `mcp__mcp-workspace__check_file_size` with `max_lines=750`: the new files are not listed.
- Every slash command named exists under `.claude/skills/` (check with `list_directory`).
- If a skill named here is missing from `.claude/skills/`, write one line to `pr_info/.blocked.txt` and stop.
- `mcp__mcp-tools-py__run_format_code`, then commit: `docs(processes): add issue-discussion, plan-creation, plan-review, implementation docs`.
