# Step 1: Add GitHub Integration Test Marker

## Objective
Add github_integration test marker to project configuration for conditional test execution.

## WHERE
- File: `pyproject.toml`

## WHAT
- Add github_integration marker to pytest configuration

## HOW
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
1. Locate markers array in pytest configuration
2. Add github_integration marker with description
3. Verify syntax with toml validation
```

## DATA
- **Input**: Existing pyproject.toml configuration
- **Output**: Updated configuration with new test marker

## LLM Prompt
```
You are implementing Step 1 of the GitHub Pull Request Operations feature as described in pr_info/steps/summary.md.

Add the github_integration test marker to pyproject.toml following the existing patterns in the file.

Requirements:
- Add github_integration marker to the pytest markers section
- Follow existing formatting and style in the file
- Ensure valid TOML syntax

Make minimal changes - only add the test marker without modifying existing content.
```

## Verification
- [ ] github_integration marker added to pytest configuration
- [ ] Valid TOML syntax maintained
- [ ] No existing markers modified
