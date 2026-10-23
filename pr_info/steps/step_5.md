# Step 5 — `ci.yml`: run `pull_request` for PRs against any base

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md` exactly.
> No Python tests apply. Run pylint, pytest (fast unit set, `-n auto`) and mypy to confirm nothing else broke.
> Make exactly one commit for this step.

## WHERE
- `.github/workflows/ci.yml`, `on:` block (top of file)

## WHAT
```yaml
on:
  push:
    branches: [ "**" ]
  pull_request:
    branches: [ "**" ]   # was: [ main ]
  workflow_dispatch:
```

## HOW
PR-only checks (`check-forbidden-folders`, the merge-with-base run) now also run for PRs against custom base branches,
which create-pr phase B waits for.

## DATA
None.
