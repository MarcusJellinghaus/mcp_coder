# Step 2 — `docs/cli-reference.md`: trust qualifiers

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`). Implement only Step 2: add the trust qualifier to three places in `docs/cli-reference.md` as described below. Change docs only, no code. Then run `mcp__mcp-tools-py__run_format_code`, pylint, mypy and the fast pytest suite (see CLAUDE.md), and make one commit: `docs(cli-reference): qualify Base Branch with issue-body trust (#1275)`.

## Precondition

Step 1 is committed: `docs/repository-setup/github.md` contains `### Trust and Validation`. If it does not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

`docs/cli-reference.md`:

- around line 431: the `rebase` option `--base-branch BRANCH`;
- around line 433: the `rebase` **Description**;
- around line 992: the `gh-tool get-base-branch` detection priority, item 1.

Link target from this file: `repository-setup/github.md#trust-and-validation`.

## WHAT

1. **`--base-branch` option (line 431).** Change it to:
   `- \`--base-branch BRANCH\` - Base branch to rebase onto (default: auto-detect). Needed only when the detected base is not \`main\`/\`master\` and was not named in the issue's \`### Base Branch\` section (an issue-named base is used only when the issue body is trusted — see [Trust and Validation](repository-setup/github.md#trust-and-validation)).`

2. **Rebase description (line 433).** Replace only the clause
   `a base named in the issue's \`### Base Branch\` section is trusted;`
   with
   `a base named in the issue's \`### Base Branch\` section is used as-is, but only when the issue body is trusted (see [Trust and Validation](repository-setup/github.md#trust-and-validation)) — otherwise detection falls back;`
   Keep the rest of the line, from "a base found from an open PR, git merge-base or the default branch is accepted automatically only when …" to the end, unchanged.

3. **`gh-tool get-base-branch` priority 1 (line 992).** Change it to:
   `1. **Linked issue's base branch** - Extracts issue number from branch name and checks the \`### Base Branch\` section in the issue body, if the issue body is trusted (see [Trust and Validation](repository-setup/github.md#trust-and-validation))`

## HOW

Docs only. Do not repeat the trust rule or the fallback chain here — link to them.

## ALGORITHM

None — text edits only.

## DATA

None.

## Tests

No tests, because this step changes docs only. The quality checks must pass.
