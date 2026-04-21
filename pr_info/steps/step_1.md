# Step 1: Fix `.importlinter` misleading comment

**Ref:** [summary.md](summary.md) — Item #4

## Context

The Requests Library Isolation contract in `.importlinter` (line 321) has a comment that says:

```
# The 'requests' library should only be used in github_operations.
```

But the `ignore_imports` section allows **two** modules to use `requests`:

```ini
ignore_imports =
    mcp_coder.utils.github_operations.** -> requests
    mcp_coder.utils.jenkins_operations.client -> requests
```

The comment is misleading — it omits `jenkins_operations.client`.

## WHERE

- `.importlinter` — line 321

## WHAT

Update the comment to accurately reflect both allowed modules.

## HOW

Single text edit: replace the comment line.

**Old (line 321):**
```
# The 'requests' library should only be used in github_operations.
```

**New:**
```
# The 'requests' library should only be used in github_operations and jenkins_operations.
```

## Verification

```
mcp__tools-py__run_lint_imports_check()
```

Lint-imports must still pass — the comment change has no functional impact.

## LLM Prompt

> Read the summary at `pr_info/steps/summary.md` and this step at `pr_info/steps/step_1.md`.
>
> Fix the misleading comment in `.importlinter` line 321. The Requests Library Isolation contract comment says "only used in github_operations" but `ignore_imports` also allows `jenkins_operations.client`. Update the comment to mention both modules. Then run `lint-imports` to verify the config still passes.
