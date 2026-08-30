# Step 2 — `implementation_approve` skill: gate on `Ready to merge`

**Read [summary.md](./summary.md) first** — see "Why two steps and not three".

One commit. Documentation-only; **not blocked** on mcp-workspace #268, so this can land
before or after step 1.

## WHY

`.claude/skills/implementation_approve/SKILL.md:19` currently reads:

> 3. Only if the branch-status check passes (exit code 0), run the set-status command ...

Step 1 of that same skill calls the `mcp__mcp-workspace__check_branch_status` **MCP tool**,
which returns report text and no exit code at all. The wording describes nothing that
exists — it is already wrong today, independently of this issue.

`Ready to merge` is the right single criterion. Upstream suppresses that recommendation on
**every** blocker — CI, tasks, PR feedback, merge state, rebase, and (after #268) the linked
branch — so one check on the report's `Recommendations` line covers all of them, and keeps
covering blockers added upstream later.

## WHERE

`.claude/skills/implementation_approve/SKILL.md` — instruction 3 at `:19`, and the `**Note:**`
paragraph directly below it if it also leans on the failure wording.

No other file. No code, no tests.

## WHAT

Replace the exit-code condition with a check on the returned report text. Something like:

> 3. Only if the report's `Recommendations` line contains `Ready to merge`, run the
>    set-status command and confirm it succeeded:

Keep the surrounding `bash` block, the `**Note:**` paragraph, instruction 2 (base-branch
confirmation), instruction 4 (post-label PR poll), the frontmatter (`description`,
`disable-model-invocation`, `allowed-tools`) and the `**Effect:**` line **as they are**.

If the `**Note:**` paragraph's "If the branch-status check fails" phrasing reads as
exit-code language in context, align it with the same criterion — e.g. "If `Ready to merge`
is absent, report the blockers to the user and do not set the label." Do not otherwise
rewrite it, and do not touch the `--force` sentence.

## DATA

No return values, no data structures. Markdown only.

## Verification

1. Re-read the edited file end to end and confirm the numbered instructions still flow
   (1 -> 2 -> 3 -> 4) and no other instruction references an exit code.
2. Run the three checks so the commit is clean:
   - `mcp__tools-py__run_pylint_check`
   - `mcp__tools-py__run_pytest_check` with
     `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
   - `mcp__tools-py__run_mypy_check`

   No result should change — this step touches no Python.

## LLM prompt

> Implement **step 2** of `pr_info/steps/step_2.md`. Read `pr_info/steps/summary.md` first
> for context.
>
> Edit only `.claude/skills/implementation_approve/SKILL.md`. Replace the "passes (exit code
> 0)" condition in instruction 3 with a check that the branch-status report's
> `Recommendations` line contains `Ready to merge`, because step 1 of that skill calls an
> MCP tool that returns text and no exit code. Align the `**Note:**` paragraph below it with
> the same criterion if it reads as exit-code language; leave the frontmatter, the bash
> block, the other instructions, the `**Effect:**` line and the `--force` sentence unchanged.
>
> This step is independent of mcp-workspace #268 and must not touch any Python file. Use MCP
> tools for file operations. Run pylint, pytest (with the fast-unit-test marker exclusions)
> and mypy to confirm nothing regressed, then commit once.
