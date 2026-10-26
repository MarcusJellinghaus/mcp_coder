# Step 3 — Document the label-workflow rule

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`. This is a documentation-only change. Make sure the consistency test from step 2 still passes (do not edit the YAML blocks). Run pylint, pytest (`-n auto`, unit markers), mypy and `run_format_code`; all must pass. Produce one commit.

## WHERE
- `docs/repository-setup/github.md`

## WHAT
1. In § "GitHub Actions Setup", add a subsection directly after the "Approve Command Handler" purpose line and before "### Installing Actions":
   ```markdown
   ### Label-Changing Workflows Must Gate on Author Trust

   Any workflow that changes labels on behalf of a comment or event author must gate on `author_association` (`OWNER`, `MEMBER`, `COLLABORATOR`), e.g.:

   `if: contains(fromJSON('["OWNER","MEMBER","COLLABORATOR"]'), github.event.comment.author_association)`

   **Why:** GitHub restricts label edits to users with triage access or higher, but a workflow runs with `GITHUB_TOKEN` write access and bypasses that restriction. Without the gate, any GitHub user could move an issue through the bot pipeline. The generated `approve-command.yml` applies this gate.
   ```
2. In § "Trust and Validation" (under Base Branch), add one bullet linking to it:
   `- **Workflows**: GitHub Actions that change labels apply the same trusted set; see [Label-Changing Workflows Must Gate on Author Trust](#label-changing-workflows-must-gate-on-author-trust).`

## HOW
- Anchor: GitHub slugifies `### Label-Changing Workflows Must Gate on Author Trust` to `#label-changing-workflows-must-gate-on-author-trust`.

## ALGORITHM / DATA
None (documentation only).
