# Step 2: Implement Matrix-Based CI Workflow

## LLM Prompt
```
Reference: pr_info/steps/summary.md - CI Pipeline Restructure

Implement Step 2: Convert the existing single-job CI workflow to a matrix-based approach. Use the test validations from Step 1 to ensure the matrix configuration preserves all functionality while providing proper red/green status per check.

Follow the requirements in this step document precisely.
```

## Objective
Replace the current CI structure with a matrix-based approach that shows individual job status and eliminates the manual aggregation step.

## WHERE
- `.github/workflows/ci.yml` (modify existing file)

## WHAT

### Main Configuration Changes
```yaml
# Matrix job structure
strategy:
  fail-fast: false
  matrix:
    check:
      - {name: "black", cmd: "black --check src tests"}
      - {name: "isort", cmd: "isort --check --profile=black --float-to-top src tests"}  
      - {name: "pylint", cmd: "pylint -E ./src ./tests"}
      - {name: "unit-tests", cmd: "pytest -m 'not git_integration...' --junitxml=unit-tests.xml"}
      - {name: "integration-tests", cmd: "pytest -m 'git_integration...' --junitxml=integration-tests.xml"}
      - {name: "mypy", cmd: "mypy --strict src tests"}

# Job naming
name: ${{ matrix.check.name }}
```

## HOW

### Integration Points
- **Preserve existing setup**: Python 3.11 installation and dependencies
- **Matrix execution**: GitHub automatically creates parallel jobs
- **Status reporting**: Each matrix job shows individual red/green status
- **Dependencies**: Maintain `needs: [check-forbidden-folders]` with `if: always()`

### Key Changes
1. **Remove**: All `continue-on-error: true` declarations
2. **Remove**: "Summarize results" step entirely
3. **Convert**: Steps to matrix configuration
4. **Add**: `fail-fast: false` to continue all checks on failures

## ALGORITHM

### Core Logic (CI transformation)
```
1. Extract existing check commands from steps
2. Create matrix configuration with fail-fast disabled
3. Replace individual steps with single matrix step
4. Remove continue-on-error and manual aggregation
5. Preserve forbidden-folders job (unchanged)
6. Maintain artifact uploads for test jobs
```

## DATA

### Matrix Configuration Structure
```yaml
# New matrix job structure
jobs:
  test:
    runs-on: ubuntu-latest
    needs: [check-forbidden-folders]
    if: always()
    strategy:
      fail-fast: false
      matrix:
        check: [...]  # Array of check configurations
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

## Implementation Notes
- **Preserved functionality**: All check commands remain identical
- **Artifact handling**: JUnit XML uploads maintained for test jobs
- **Job dependencies**: Keep relationship with forbidden-folders check
- **Parallel execution**: Matrix automatically parallelizes checks
- **Status clarity**: GitHub UI shows distinct jobs for each check

## Success Criteria
- Matrix jobs appear as separate entries in GitHub Actions UI
- Individual job failures show red status (not green)
- All checks continue running despite individual failures
- "Summarize results" step completely removed
- Existing functionality preserved (setup, commands, artifacts)
- External API provides job status per matrix entry

## Validation
- Run modified CI on test branch
- Verify job names appear correctly: "black", "isort", "pylint", etc.
- Confirm failed checks show red status in UI
- Test external API access to individual job status