# Step 1: Implement Matrix-Based CI Workflow

## LLM Prompt
```
Reference: pr_info/steps/summary.md - CI Pipeline Restructure

Implement Step 1: Convert the existing single-job CI workflow to a matrix-based approach and update documentation.

Follow the requirements in this step document precisely.
```

## Objective
Replace the current CI structure with a matrix-based approach that shows individual job status per check.

## Files to Modify

### 1. `.github/workflows/ci.yml`

#### Remove
- All `continue-on-error: true` declarations
- All step `id:` attributes for checks (black, isort, pylint, etc.)
- The entire "Summarize results" step
- `needs: [check-forbidden-folders]` from test job
- `if: always()` from test job

#### Convert test job to matrix structure
```yaml
test:
  runs-on: ubuntu-latest
  strategy:
    fail-fast: false
    matrix:
      check:
        - {name: "black", cmd: "black --check src tests"}
        - {name: "isort", cmd: "isort --check --profile=black --float-to-top src tests"}
        - {name: "pylint", cmd: "pylint -E ./src ./tests"}
        - {name: "unit-tests", cmd: "pytest -m 'not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration' --junitxml=unit-tests.xml"}
        - {name: "integration-tests", cmd: "pytest -m 'git_integration or formatter_integration or github_integration' --junitxml=integration-tests.xml"}
        - {name: "mypy", cmd: "mypy --strict src tests"}
  name: ${{ matrix.check.name }}
  steps:
    - uses: actions/checkout@v4
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install .
        python -m pip install .[dev]
    - name: Run ${{ matrix.check.name }}
      run: ${{ matrix.check.cmd }}
```

#### Add inline comment
```yaml
# Matrix approach: Each check runs as independent job with individual pass/fail status
# fail-fast: false ensures all checks complete even if one fails
```

#### Preserve unchanged
- `check-forbidden-folders` job (no changes)
- Trigger configuration (on push/pull_request/workflow_dispatch)

### 2. `docs/architecture/ARCHITECTURE.md`

Add brief note (~2-3 lines) in Cross-cutting Concepts section:

```markdown
### CI Pipeline
- **Matrix-based execution**: Each check (black, isort, pylint, tests, mypy) runs as independent job with individual pass/fail status
- **Parallel execution**: All checks run simultaneously with `fail-fast: false`
```

## Success Criteria
- Matrix jobs appear as "test (black)", "test (isort)", etc. in GitHub Actions UI
- Individual job failures show red status (not green)
- All checks continue running despite individual failures
- "Summarize results" step removed
- `check-forbidden-folders` runs independently (no dependency)

## Verification
Done during PR review:
1. Push to feature branch
2. Observe GitHub Actions UI shows 6 separate jobs
3. Confirm each job has independent pass/fail status
