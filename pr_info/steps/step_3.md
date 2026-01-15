# Step 3: Add CI Integration

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Task: Add Vulture dead code check to the CI workflow architecture job.
Vulture should already be clean locally (verified in Step 2).
This step adds CI enforcement to catch future dead code.
```

## WHERE
| File | Action |
|------|--------|
| `.github/workflows/ci.yml` | Modify - add vulture to architecture matrix |

## WHAT

### Add to CI architecture matrix

Add vulture check to the existing `architecture` job matrix in `.github/workflows/ci.yml`:

```yaml
# In architecture job matrix:
matrix:
  check:
    - {name: "import-linter", cmd: "lint-imports"}
    - {name: "tach", cmd: "tach check"}
    - {name: "pycycle", cmd: "pycycle --here --ignore .venv,__pycache__,build,dist,.git,.pytest_cache,.mypy_cache"}
    - {name: "vulture", cmd: "vulture src tests vulture_whitelist.py --min-confidence 60"}
```

## HOW
1. Open `.github/workflows/ci.yml`
2. Find the `architecture` job's `matrix.check` array
3. Add vulture entry after existing checks
4. Vulture is already installed via `.[dev]` dependencies (added in Step 0)

## ALGORITHM
```
1. Read ci.yml
2. Locate architecture job matrix check array
3. Add new entry: {name: "vulture", cmd: "vulture src tests vulture_whitelist.py --min-confidence 60"}
4. Save file
5. Verify YAML syntax is valid
```

## DATA

### CI Matrix Entry
```yaml
{name: "vulture", cmd: "vulture src tests vulture_whitelist.py --min-confidence 80"}
```

### Expected CI Behavior
- Vulture runs as part of the architecture matrix (PR-only)
- Fails if dead code detected above 60% confidence
- Whitelist excludes known false positives and API completeness items
- Checks both `src` and `tests` directories

## VERIFICATION

```python
# Verify YAML syntax is valid:
Bash("python -c \"import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))\"")

# Verify vulture still passes locally:
Bash("vulture src tests vulture_whitelist.py --min-confidence 60")

# Run full code quality checks:
mcp__code-checker__run_pylint_check()
mcp__code-checker__run_mypy_check()
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"])
```

## SUCCESS CRITERIA
- [ ] CI workflow YAML is valid
- [ ] Vulture check added to architecture matrix
- [ ] Local vulture check still passes
- [ ] All other code quality checks pass
