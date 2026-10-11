# Step 4 — Document the token types and permissions

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md`. This step
> changes docs only; keep the text short. Run the formatter and commit.

## WHERE

`docs/repository-setup/github.md`, section `## GitHub Token Configuration`. Replace the
"**Required permissions:**" and "**How to create a GitHub token:**" blocks. Keep the
config-file table and the TOML example.

## WHAT — content to write

**Token options** (either one works):

1. **Fine-grained PAT** (least privilege). Grant repository access to the target repos
   with these read permissions, which are the ones `mcp-coder verify` probes:
   - `Contents: Read`
   - `Administration: Read` (branch protection)
   - `Pull requests: Read`
   - `Issues: Read`
   - `Actions: Read`
   - `Commit statuses: Read`

   Without `Administration: Read`, `verify` shows branch protection as
   `[WARN] not verifiable`. That is not an error, and the exit code is unaffected.

2. **Classic PAT** (simpler, broader). Use the `repo` scope (`public_repo` covers public
   repositories only). Classic scopes grant permissions in bundles, so a `repo`-scope
   token satisfies all of the checks above.

**How to create:** go to GitHub → Settings → Developer settings → Personal access
tokens, choose *Fine-grained tokens* or *Tokens (classic)*, then add the token to the
config file.

Do not list write permissions for workflow automation, and do not list permissions for
the #1180 security-settings rows. Both are out of scope.

## Commit

`docs(github): document fine-grained and classic token permissions`
