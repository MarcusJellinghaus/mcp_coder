# Step 3 — Remove the session-limit caveat from the docs

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`.
> Docs only. If either caveat sentence below is not found, write one line to
> `pr_info/.blocked.txt` and stop. Make exactly one commit.

## WHERE

- `docs/coordinator-vscodeclaude.md` — section "PR-health checks for `status-10:pr-created`"
- `docs/processes-prompts/development-process.md` — section "10. PR-health (status-10)"

## WHAT

1. `docs/coordinator-vscodeclaude.md`: delete the sentence
   `The checks currently run only while the session limit has not been reached.`
   Then add, after "…how often you run (or schedule) the command.":
   `The checks run whether or not a session slot is free.`
2. `docs/processes-prompts/development-process.md`: in
   `…checks it on every \`coordinator vscodeclaude\` run (while below the session limit) for three problems.`
   delete ` (while below the session limit)`.

## HOW

Plain text edits with `mcp__mcp-workspace__edit_file`; no other wording changes.

## ALGORITHM / DATA

None.

## Verification

`mcp__mcp-workspace__search_files(pattern="session limit", glob="docs/**/*.md")` finds no PR-health caveat.

## Commit

`docs(vscodeclaude): PR-health checks no longer depend on the session limit (#1238)`
