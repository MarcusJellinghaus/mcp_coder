# Step 4: Add CI Integration

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Task: Add Vulture dead code check to the CI workflow architecture job.
This ensures new dead code is caught in pull requests.
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
    # ... existing checks (import-linter, tach, pycycle) ...
    - {name: "vulture", cmd: "vulture src tests vulture_whitelist.py --min-confidence 80"}
```

## HOW
1. Open `.github/workflows/ci.yml`
2. Find the `architecture` job's `matrix.check` array
3. Add vulture entry after existing checks (import-linter, tach, pycycle)
4. Vulture is installed via `.[dev]` dependencies (added in Step 0)

## ALGORITHM
```
1. Read ci.yml
2. Locate architecture job matrix check array
3. Add new entry: {name: "vulture", cmd: "vulture src tests vulture_whitelist.py --min-confidence 80"}
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
- Fails if dead code detected above 80% confidence
- Whitelist excludes known false positives
- Checks both `src` and `tests` directories

## VERIFICATION
```bash
# Local verification before push:
vulture src tests vulture_whitelist.py --min-confidence 80

# Should return exit code 0 (success) after all cleanup is done
echo $?
```

## INTEGRATION POINTS
- Vulture installed via `pip install .[dev]` in CI
- Runs in parallel with other architecture checks (import-linter, tach, pycycle)
- Uses same fail-fast: false strategy as other checks
- Only runs on pull requests (not on every push)
