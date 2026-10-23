# Step 1 — `docs/repository-setup/github.md`: add the Trust and Validation section

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`). Implement only Step 1: edit `docs/repository-setup/github.md` as described below. Change docs only, no code. Then run `mcp__mcp-tools-py__run_format_code`, pylint, mypy and the fast pytest suite (see CLAUDE.md), and make one commit: `docs(github): document Base Branch trust gate and ref-name rule (#1275)`.

## Precondition

The file contains the heading `## Base Branch Support for Issues` and the subsections `### Parsing Rules`, `### Validation`, `### Epic Branches` and `### Backward Compatibility`. If any of these is missing, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

`docs/repository-setup/github.md`, section `## Base Branch Support for Issues` (around lines 195–270).

## WHAT

1. **Parsing Rules** (around lines 219–225):
   - Replace `- **Single line only**: Multiple lines will cause an error` with:
     `- **Single line only**: a multi-line value is rejected on write by mcp-workspace; otherwise it is ignored (see [Trust and Validation](#trust-and-validation))`
   - Add a bullet after it:
     `- **Valid git ref name**: see [Trust and Validation](#trust-and-validation)`
   - Replace the `Empty = default` bullet with:
     `- **Empty = fallback**: if the section is empty, missing, untrusted or malformed, the fallback in [Trust and Validation](#trust-and-validation) applies`

2. **New subsection.** Insert it directly after Parsing Rules and before `### Validation`:

   ```markdown
   ### Trust and Validation

   The section is honoured only when the issue body is trusted:

   - **Trusted body**: the author is trusted (`OWNER`, `MEMBER`, `COLLABORATOR`, or listed in `[github] trusted_commenters`), **or** the last body editor is the token user or listed in `trusted_commenters`. Full rule: mcp-workspace README, [Commenter trust](https://github.com/MarcusJellinghaus/mcp-workspace#commenter-trust); config key: [GitHub configuration](https://github.com/MarcusJellinghaus/mcp-workspace#github-configuration).
     - Editor trust has no role check: a collaborator editing a stranger's issue does not make it trusted unless they are in `trusted_commenters`.
     - If the untrusted author edits the body again, they become the last editor and the section is ignored again.
   - **Untrusted → ignored entirely**: no value, no error, no Review Gate block. Tool output does not mention it; only a log line records it.
   - **Ref-name rule**: the value must be a valid git ref name ([`git check-ref-format`](https://git-scm.com/docs/git-check-ref-format)): no spaces or control characters; no `..`, `~`, `^`, `:`, `?`, `*`, `[`, `\`, `@{` or `//`; no leading `-` or `.`; no trailing `.`, `/` or `.lock`.
   - **Malformed** (multiple lines or an invalid ref name) in a trusted issue: mcp_coder commands ignore it silently, as if it were untrusted. Only mcp-workspace tools report it: the `check_branch_status` MALFORMED line / Review Gate, and `get_base_branch`.

   **Fallback** when there is no usable section (missing, empty, untrusted or malformed):

   - **Base branch detection** — `gh-tool get-base-branch`, `rebase`, the implement workflow's rebase step, `fix-conflict`, `git-tool`, create-pr, review — falls through to the open PR's base → git merge-base → default branch. For `mcp-coder rebase`, a result other than `main`/`master` needs `--base-branch`.
   - **Branch creation** — `create-plan`, `gh-tool checkout-issue-branch` — starts from the default branch.
   ```

3. **Validation** (around lines 227–232): add this bullet to the list:
   `- mcp-workspace's \`github_issue_create\` / \`github_issue_edit\` reject a multi-line or invalid ref-name value on write (unless the server runs with \`--no-enforce-base-branch-format\`)`

4. **Epic Branches**, item 2 (around line 241). Change the end of the item to:
   `... create-plan, implement, \`mcp-coder rebase\`, review and create-pr then use it without flags — provided the sub-issue body is trusted (written by a trusted author, or last edited by the token user or an allowlisted login; see [Trust and Validation](#trust-and-validation)).`

5. **Backward Compatibility** (around line 249). Replace the paragraph with:
   `Existing issues without a \`### Base Branch\` section — or whose section is ignored because the body is untrusted or the value is malformed — fall back as described in [Trust and Validation](#trust-and-validation): detection falls back to the PR base, merge-base or default branch, and branch creation uses the repository's default branch (typically \`main\` or \`master\`).`

## HOW

Docs only. No imports, no code integration. Keep the section's existing markdown style: bold bullet labels, and the `###` level for subsections.

## ALGORITHM

None — text edits only.

## DATA

None.

## Tests

No tests, because this step changes docs only. The quality checks must still pass. They are unaffected by this step.
