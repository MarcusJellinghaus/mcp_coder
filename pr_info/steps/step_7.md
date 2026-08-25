# Step 7 — Boy-scout fix: `coordinator --dry-run` in `cli-reference.md`

Read [summary.md](summary.md) first.

Independent of every other step; may be done at any point. Kept separate so it is a reviewable
docs-only diff rather than noise inside a code commit.

## WHERE

- `docs/cli-reference.md` (modify, `:505-506` and `:1155-1156`)

## WHAT

Two problems at each of the two sites.

**1. The prose is wrong.** Both say `--dry-run` means "Preview without executing". It does not —
`execute_coordinator_test` fires a **real** Jenkins build of the executor job running an
environment smoke test. It touches no GitHub issues and changes no labels, but it is not a
preview.

**2. The example command is invalid.** Both show:

```bash
mcp-coder coordinator --all --dry-run
```

`main.py:156-167` rejects `--dry-run` unless **both** `--repo` and `--branch-name` are given, so
this errors out as written.

`parsers.py:314`'s help text ("Trigger Jenkins test instead of dispatching workflows") is already
correct — leave it alone, and match its framing.

## HOW

At `:505-506`:

```bash
# Smoke-test one repo on Jenkins (triggers a real build; changes no issues or labels)
mcp-coder coordinator --dry-run --repo mcp_coder --branch-name main
```

At `:1155-1156`, same correction. Keep the existing surrounding entries (`--all`,
`--force-refresh`) untouched.

While in the file, check for any other occurrence of `--dry-run` described as a preview in a
`coordinator` context and correct it the same way; the `--dry-run` flags of *other* commands are
out of scope and must not be touched.

Optionally add a one-line cross-reference to `docs/repository-setup/jenkins.md` (step 2) near the
coordinator entry, since `--dry-run` is the documented first-run / new-repo setup command and is
exactly what an operator runs while configuring Jenkins permissions.

## ALGORITHM / DATA

N/A.

## TESTS

None — docs only. Confirm any relative link added resolves to a real file.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_7.md`.
>
> Fix the two `coordinator --dry-run` descriptions and example commands in `docs/cli-reference.md`
> at `:505-506` and `:1155-1156`: the prose wrongly calls it a preview (it triggers a real Jenkins
> build) and the example `mcp-coder coordinator --all --dry-run` is rejected by
> `main.py:156-167`, which requires both `--repo` and `--branch-name`.
>
> Match the framing of `parsers.py:314`'s help text, which is already correct — do not change it.
> Do not touch the `--dry-run` flag of any other command.
>
> Run `mcp__tools-py__run_pytest_check` with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
> to confirm nothing regressed, then commit as one commit.
