# Step 1: Token permissions in `github.md`, links from the other docs

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Docs only: edit `docs/repository-setup/github.md`, `docs/getting-started/label-setup.md`
> and `docs/configuration/config.md` as specified. Use the text blocks below verbatim.
> Then run the checks listed under **Verification**, format, and make one commit.

## Preconditions

If either of these does not hold, write one line to `pr_info/.blocked.txt` and stop:

- `github.md` still contains the line `with these read permissions. The list names the permissions behind its own rows of`.
- `label-setup.md` still contains this line:

  ```text
  The token needs `repo` scope permissions to create and manage labels.
  ```

## WHERE

- `docs/repository-setup/github.md`, section `## GitHub Token Configuration`
- `docs/getting-started/label-setup.md`, section `### GitHub Token Configuration`
- `docs/configuration/config.md`, auto-merge *Caveats* list and `### GitHub Credentials Setup`

## WHAT / HOW

There are no functions, imports or integration points; this step only edits Markdown.
The edits are listed below.

### A. `github.md`: fine-grained PAT item (list item 1)

Replace everything from `1. **Fine-grained PAT** (least privilege)...` through the
`` - `Code scanning alerts: Read` `` bullet with the block below. Every line of the
table is indented 3 spaces so it stays inside list item 1.

```markdown
1. **Fine-grained PAT** (least privilege). Grant repository access to the target repos
   with these permissions:

   | Permission | Level | Needed by |
   |---|---|---|
   | Actions | Read | Workflow runs, jobs and logs: `workflow_steps/ci.py`, `workflow_steps/merge.py`, `check_branch_status`, vscodeclaude (`workflows/vscodeclaude/checks.py`, `get_latest_ci_status`) |
   | Administration | Read (optional) | `verify` only: branch protection, Dependabot / secret-scanning rows; auto-delete branches unconfirmed (`verify` reads `delete_branch_on_merge` from the plain repo GET; whether it needs Administration is untested) |
   | Code scanning alerts | Read | `check_branch_status`, vscodeclaude (`workflows/vscodeclaude/checks.py`), auto-merge (`merge.py`), `/pr_comment_triage` |
   | Commit statuses | Read | Listing non-green checks when a PR is `mergeable_state=unstable` (mcp-workspace `get_non_green_checks`, via `check_branch_status`) |
   | Contents | Read and write | Write: issue branch creation via GraphQL `createLinkedBranch` (`gh-tool checkout-issue-branch`, `create_plan/prerequisites.py`) and auto-merge (`merge.py` → PUT `/pulls/{n}/merge`) |
   | Issues | Read and write | Labels create/update/delete (`define-labels`), `define-labels` initialising `status-01` on existing issues, label transitions (`set-status`, coordinator, `label_transitions.py`), the vscodeclaude `status-91` escalation, comments (`failure_handling.py`, `review/handoff.py`), mcp-workspace `github_issue_create` / `_edit` / `_comment` / `github_subissue_*`; linking the branch in `createLinkedBranch` |
   | Metadata | Read | Always on |
   | Pull requests | Read and write | `create-pr` (`workflows/create_pr/core.py`, incl. best-effort PR assignee when `auto_review_implementation` is on), PR description edit (`pr_description.py`), `/pr_comment_triage` (`github_review_comment_reply`, `github_review_thread_resolve`) |
   | Workflows | Read and write (conditional) | Only if auto-merge may merge PRs that touch `.github/workflows/` (e.g. `define-labels --generate-github-actions` output, Dependabot `github-actions` bumps): GitHub rejects such an API merge without it |

   Unconfirmed, worth testing with a least-privilege token:
   - the `createLinkedBranch` mapping (Contents + Issues write) is inferred;
   - the Workflows-write requirement for API merges of workflow-touching PRs;
   - whether the merge PUT needs Contents write;
   - the auto-delete-branches mapping (Administration vs. plain repo GET).

   `verify` does not test write access, so a token can pass `verify` and still fail on
   writes.
```

### B. `github.md`: ruleset/protection block

Leave it unchanged: from `` `verify` reads branch protection from both classic protection and rulesets. ``
through `can bypass".`.

### C. `github.md`: Code scanning paragraph

Replace the paragraph that starts with `**Code scanning alerts** — ` with:

```markdown
   **Code scanning alerts** — without `Code scanning alerts: Read`, vscodeclaude
   silently does nothing about alerts, auto-merge merges with only a warning, and
   `check_branch_status` reports the alerts as not checked.
```

### D. `github.md`: Classic PAT item

Keep the existing text, including the `repo`-scope sentence and the `security_events`
bullet. After the `security_events` bullet, add:

```markdown
   - If auto-merge may merge PRs that touch `.github/workflows/`, add the `workflow`
     scope (`repo` doesn't include it). Unconfirmed.
```

### E. `github.md`: two bold-lead-in blocks before `**How to create:**`

Insert this between the Classic PAT item and `**How to create:**`. These are
paragraphs, not headings:

```markdown
**Check runs limitation:** whether fine-grained PATs can be granted a Checks permission
is unconfirmed. `check_branch_status` lists non-green checks only when CI passed (or is
not configured) and GitHub reports the PR as `mergeable_state=unstable`. It reads commit
statuses and check runs together, so if the check-run call fails (403 on a private repo)
neither is listed and `check_branch_status` shows `could not list checks: …`.

**Required in the future:** not needed by mcp-coder today, or needed only in specific
setups. These are recommended for full visibility of repo problems, and are candidates
if mcp-coder starts surfacing them.

Read:

| Permission | Why |
|---|---|
| Dependabot alerts | Vulnerable-dependency alerts (repos with `dependabot.yml`) |
| Discussions | GitHub Discussions, if the repo uses them |
| Repository security advisories | Private vulnerability reports (the `SECURITY.md` channel) |
| Secret scanning alerts | Leaked-credential alerts |

Write:

| Permission | Why |
|---|---|
| Discussions | Posting in GitHub Discussions |
| Repository security advisories | Triage and publish vulnerability reports outside the web UI |
| Workflows | Also needed if the same token is the git push credential (local or Jenkins `github_credentials_id`): pushes changing `.github/workflows/` need it |
```

Do not touch the text from `## Repo Security Configuration Checks` onward. Its
"fine-grained PAT table above" wording is now accurate.

### F. `label-setup.md`

Replace this line:

```text
The token needs `repo` scope permissions to create and manage labels.
```

with:

```markdown
For the permissions the token needs, see [GitHub Token Configuration](../repository-setup/github.md#github-token-configuration).
```

### G. `config.md`: auto-merge *Caveats*

In the bullet `- Alerts skipped (403/404: the token lacks \`Code scanning alerts: Read\`, or code scanning is not enabled) → merges, with a warning in the Jenkins log.`,
replace `` `Code scanning alerts: Read` `` with
`the [code-scanning permission](../repository-setup/github.md#github-token-configuration)`.
Leave the rest of the bullet unchanged.

### H. `config.md`: `### GitHub Credentials Setup`

1. After the intro sentence, add:

```markdown
The `github_credentials_id` credential (Username with password: GitHub user + PAT)
serves both sides. AutoRunner's executor jobs export the PAT as `GITHUB_TOKEN`, which
overrides `[github] token` in `config.toml`, so it is the workflows' API token. They
also use it for the repo checkout; the container executor embeds it in the clone URL,
so pushes use it too.
```

2. Replace the four numbered items under `#### 1. Create GitHub Personal Access Token` with:

```markdown
1. Go to GitHub → Settings → Developer settings → Personal access tokens, and create a
   fine-grained or classic token.
2. Grant the permissions in [GitHub Token Configuration](../repository-setup/github.md#github-token-configuration),
   plus Workflows write (classic: `workflow` scope) if pushes may change
   `.github/workflows/`.
3. Copy the generated token (save it securely - you won't see it again)
```

3. Leave `#### 2. Store Token in Jenkins`, `#### 3. Use Credentials ID in Configuration`
   and **Security Notes** unchanged.

## ALGORITHM

```
check preconditions -> else write one line to pr_info/.blocked.txt, stop
github.md: apply A, C, D, E (B untouched)
label-setup.md: apply F
config.md: apply G, H
run verification checks; fix any failure
format, stage, commit
```

## DATA

There are no return values or data structures. The result is Markdown only. The anchor
`#github-token-configuration` resolves to `## GitHub Token Configuration` in `github.md`,
and no headings are added or renamed.

## Verification

- `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "tests/cli/commands/test_define_labels_actions.py"])` must pass.
- Read back the edited section of `github.md`. Check that the table lines are indented
  3 spaces and that `**How to create:**` is still a plain paragraph after the new blocks.
- Run `mcp__mcp-tools-py__run_format_code`.

## Commit

`docs(github): list write permissions the workflow token needs (#1394)`
