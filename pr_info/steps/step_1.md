# Step 1: Add PyGithub Dependency and Test Marker

## Objective
Add PyGithub dependency and github_integration test marker to project configuration.

## WHERE
- File: `pyproject.toml`

## WHAT
- Add PyGithub>=1.59.0 to dependencies array
- Add github_integration marker to pytest configuration

## HOW
### Dependencies Section
```toml
dependencies = [
    # ... existing dependencies ...
    "PyGithub>=1.59.0",
]
```

### Test Markers Section
```toml
[tool.pytest.ini_options]
markers = [
    # ... existing markers ...
    "github_integration: tests requiring GitHub API access and credentials",
]
```

## ALGORITHM
```
1. Locate dependencies array in pyproject.toml
2. Add PyGithub>=1.59.0 to end of array
3. Locate markers array in pytest configuration
4. Add github_integration marker with description
5. Verify syntax with toml validation
```

## DATA
- **Input**: Existing pyproject.toml configuration
- **Output**: Updated configuration with new dependency and marker

## LLM Prompt
```
You are implementing Step 1 of the GitHub Pull Request Operations feature as described in pr_info/steps/summary.md.

Add the PyGithub dependency and github_integration test marker to pyproject.toml following the existing patterns in the file.

Requirements:
- Add "PyGithub>=1.59.0" to the dependencies array
- Add github_integration marker to the pytest markers section
- Follow existing formatting and style in the file
- Ensure valid TOML syntax

Make minimal changes - only add the two required entries without modifying existing content.
```

## Verification
- [ ] PyGithub appears in dependencies array
- [ ] github_integration marker added to pytest configuration
- [ ] Valid TOML syntax maintained
- [ ] No existing dependencies or markers modified
