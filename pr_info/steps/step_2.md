# Step 2: Add Environment Info and Tool Versions

## LLM Prompt

```
Read pr_info/steps/summary.md for context on Issue #284.

Implement Step 2: Add environment info step and tool version display in the CI workflow.

Changes to make in .github/workflows/ci.yml:
1. Add environment info step after dependency installation in both `test` and `architecture` jobs
2. Prepend version command to each matrix check command using &&

Ensure Step 1 (uv migration) is already complete before this step.
```

## WHERE

| File | Action |
|------|--------|
| `.github/workflows/ci.yml` | Modify |

## WHAT

### Add Environment Info Step (both jobs)

Add after "Install dependencies" step:

```yaml
- name: Environment info
  run: |
    uname -a
    python --version
    uv --version
    git --version
```

### Update Matrix Commands - Test Job

**Before → After:**

| Name | Before | After |
|------|--------|-------|
| black | `black --check src tests` | `black --version && black --check src tests` |
| isort | `isort --check --profile=black --float-to-top src tests` | `isort --version && isort --check --profile=black --float-to-top src tests` |
| pylint | `pylint -E ./src ./tests` | `pylint --version && pylint -E ./src ./tests` |
| unit-tests | `pytest -m '...' --junitxml=unit-tests.xml` | `pytest --version && pytest -m '...' --junitxml=unit-tests.xml` |
| integration-tests | `pytest -m '...' --junitxml=integration-tests.xml` | `pytest --version && pytest -m '...' --junitxml=integration-tests.xml` |
| mypy | `mypy --strict src tests` | `mypy --version && mypy --strict src tests` |

### Update Matrix Commands - Architecture Job

**Before → After:**

| Name | Before | After |
|------|--------|-------|
| import-linter | `lint-imports` | `lint-imports --version && lint-imports` |
| tach | `tach check` | `tach --version && tach check` |
| pycycle | `pycycle --here --ignore ...` | `pycycle --version && pycycle --here --ignore ...` |
| vulture | `vulture src tests vulture_whitelist.py --min-confidence 60` | `vulture --version && vulture src tests vulture_whitelist.py --min-confidence 60` |

## HOW

### Version Commands Verified

All tools support `--version`:
- `black --version` ✓
- `isort --version` ✓
- `pylint --version` ✓
- `pytest --version` ✓
- `mypy --version` ✓
- `lint-imports --version` ✓
- `tach --version` ✓
- `pycycle --version` ✓
- `vulture --version` ✓

### Why Prepend with &&

Using `&&` ensures:
1. Version is displayed first in logs
2. If version command fails, check doesn't run (fail-fast)
3. No additional steps or matrix complexity
4. Easy to maintain

## DATA

### Expected Log Output Example

```
=== Environment info ===
Linux runner-xxx 6.5.0-xxx #xxx SMP ...
Python 3.11.x
uv 0.5.x
git version 2.xx.x

=== Run black ===
black, 24.x.x (compiled: yes)
...
All done! ✨ 🍰 ✨
```

## ALGORITHM

```
1. Display environment info (uname, python, uv, git versions)
2. For each matrix check:
   a. Display tool version
   b. Run actual check command
   c. Report pass/fail
```

## Validation

After implementation, verify in CI logs:
- [ ] Environment info step shows all 4 tool versions
- [ ] Each check shows its tool version before running
- [ ] All checks pass (no functional changes)
- [ ] CI completes faster than before (uv speedup)
