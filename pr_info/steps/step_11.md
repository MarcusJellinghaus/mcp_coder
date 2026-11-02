# Step 11 — Documentation

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_11.md` only.
> Docs only — no code changes. Keep edits short and factual (see the Writing style
> in `.claude/CLAUDE.md`). Run pytest (fast unit set, `-n auto`) in case doc
> tests exist, run `run_format_code`, and make exactly one commit.

## WHERE / WHAT

| File | Edit |
|---|---|
| `docs/processes-prompts/processes/08-pr-creation.md` | still `dirty` → `status-71` (fix-conflict), not `status-74`; flow line at the top |
| `docs/processes-prompts/processes/71-pr-follow-up.md` | replace "`fix-conflict` is a plain rebase with no LLM" with: git-only rebase, then LLM rebase on conflict / rebase_failed; hand-off comment includes the LLM reason; `status-74` entry command `/rebase` |
| `docs/processes-prompts/processes/17-automated-code-review.md` | rebase gate runs the LLM rebase after a git-only conflict / failure; hands off only if that fails (with reason) |
| `docs/processes-prompts/processes/failure-handling.md` | `status-74` opens with `/rebase`, then `/check_branch_status` (not `/check_branch_status` only) |
| `docs/cli-reference.md` | `fix-conflict`: new args `--llm-method`, `--mcp-config`, `--settings` (overrides least-privilege permissions, no auto-detect) and LLM fallback; `create-pr`: still conflicting → `status-71`; `rebase`: fix the "same rebase step review runs" claim (review runs git-only first, then this LLM rebase with an explicit base and a marker filter); pytest timeout 1800 s; `review-implementation`: LLM fallback in rebase gate |
| `docs/getting-started/label-setup.md` | `status-72` description without "Mechanical" |
| `docs/processes-prompts/claude_cheat_sheet.md` | `status-74` meaning (LLM rebase failed / still conflicting) |
| `docs/coordinator-vscodeclaude.md` | `status-74` commands `/rebase`, `/check_branch_status` |
| `docs/repository-setup/github.md` | base-branch guard of `mcp-coder rebase` does not apply to automated callers (they pass the detected base explicitly) |
| `docs/repository-setup/repo.md` | "`.gitignore` Entries": add `.mcp-coder/` and `logs/`, required for the automated LLM rebase (review / fix-conflict hand off when `.mcp-coder/` is not ignored) |

Also mention in `cli-reference.md` / `repo.md`: automated LLM rebase runs pytest in the
mcp-coder tool env (`sys.executable`); target-repo test deps must be installed there.

## ALGORITHM / DATA

None.

## Checks

Search `docs/` for remaining "Mechanical rebase", "plain rebase with no LLM" and
`status-74` statements about create-pr; fix any leftover.
