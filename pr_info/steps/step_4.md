# Step 4: Update skill documentation files

## LLM Prompt
> Read `pr_info/steps/summary.md` for context. Implement Step 4: Update the skill SKILL.md files for `check_branch_status` and `implementation_approve`. No tests needed — documentation only. Run all code quality checks after.

## WHERE
- `.claude/skills/check_branch_status/SKILL.md`
- `.claude/skills/implementation_approve/SKILL.md`

## WHAT

### `check_branch_status/SKILL.md`:
- Add `--wait-for-pr` and `--pr-timeout` to the command description
- No change to the default skill command (it doesn't use `--wait-for-pr` by default)
- Document the new flags in the "What This Command Does" section

### `implementation_approve/SKILL.md`:
- Change instructions to gate label change on branch-status check:
  ```bash
  mcp-coder check branch-status --ci-timeout 400 --pr-timeout 600 --llm-truncate --wait-for-pr
  ```
- Only set `status-08:ready-pr` label if check passes (exit code 0)
- Add step: "Run branch-status check with `--wait-for-pr` first"

## ALGORITHM
N/A — documentation changes only.

## COMMIT
`docs(skills): document --wait-for-pr in check_branch_status and implementation_approve`
