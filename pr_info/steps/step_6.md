# Step 6 — Incoming link and anchor updates + lychee check

## LLM prompt

> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_6.md`).
> Repoint the moved anchors listed below to the new per-process docs, and reword `docs/README.md:30`. Change only link targets and that one wording.
> Then run `tools/lychee_check.bat` and fix every broken link it reports in `README.md`, `docs/**/*.md` and `project_idea.md`.
> Format, then commit as one commit.

## WHERE / WHAT

| File | Line (current) | Change |
|---|---|---|
| `docs/cli-reference.md` | 523 | `processes-prompts/development-process.md#10-pr-health-status-10` → `processes-prompts/processes/pr-follow-up.md` |
| `docs/cli-reference.md` | 553 | same as above |
| `docs/cli-reference.md` | 1065 | `processes-prompts/development-process.md#8-failure-handling` → `processes-prompts/processes/failure-handling.md` |
| `docs/coordinator-vscodeclaude.md` | 116 | `#10-pr-health-status-10` link → `processes-prompts/processes/pr-follow-up.md` |
| `docs/getting-started/label-setup.md` | 319 | `#8-failure-handling` link → `../processes-prompts/processes/failure-handling.md` (the `14f`/`17f` sentence may point to `../processes-prompts/processes/automated-review.md` instead, as that doc owns those labels) |
| `docs/README.md` | 30 | "Full workflow methodology and prompts" → "Process overview; per-process docs hold details and prompt links" (wording only) |

Plain links to `development-process.md` stay valid and are not changed:
- `README.md:177`
- `project_idea.md:102`
- `docs/cli-reference.md:1253`
- `docs/configuration/claude-code.md:247`
- `docs/configuration/config.md:1200`
- `docs/getting-started/label-setup.md:334`
- `docs/repository-setup/README.md:138`

## HOW

1. Re-run `search_files` with pattern `development-process\.md#` over the repo. After the edits, the only matches allowed are inside `pr_info/`.
2. Run the link check via the Bash tool (no MCP equivalent): `cmd //c tools\\lychee_check.bat`. If `lychee` is not on PATH, write one line to `pr_info/.blocked.txt` and stop.
3. Fix every reported broken link. Common case: relative prefixes in `processes/*.md` (`../../../` to the repo root).

## ALGORITHM

```
for (file, line, old, new) in table: edit_file(file, old, new)
assert search_files("development-process\.md#") finds nothing outside pr_info/
run lychee_check.bat
while errors: fix link, rerun
```

## DATA

Not applicable.

## Checks

- lychee reports 0 errors.
- Format, then commit: `docs: update links and anchors to per-process docs`.
