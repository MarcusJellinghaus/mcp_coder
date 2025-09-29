# Step 8: Create Shared GitHub Test Fixture

## Context
Extract common GitHub test setup logic into a shared fixture to reduce duplication between `labels_manager` and `pr_manager` test fixtures and improve test maintainability.

## WHERE

### Test File to Modify
```
tests/utils/test_github_operations.py
```

## WHAT

### Shared Fixture and Helper Functions

```python
@pytest.fixture
def github_test_setup(tmp_path: Path) -> Generator[GitHubTestSetup, None, None]:
    """Shared GitHub test setup for both LabelsManager and PullRequestManager."""

def create_github_manager[T](manager_class: type[T], git_dir: Path, github_token: str) -> T:
    """Generic helper to create GitHub manager instances with mocked config."""

class GitHubTestSetup(TypedDict):
    git_dir: Path
    github_token: str
    test_repo_url: str
```

### Updated Manager Fixtures

```python
@pytest.fixture  
def labels_manager(github_test_setup: GitHubTestSetup) -> Generator[LabelsManager, None, None]:
    """Create LabelsManager using shared setup."""

@pytest.fixture
def pr_manager(github_test_setup: GitHubTestSetup) -> Generator[PullRequestManager, None, None]:
    """Create PullRequestManager using shared setup."""
```

## HOW

### Integration Points
- Create `GitHubTestSetup` TypedDict for structured test data
- Extract configuration validation logic into shared fixture
- Create generic manager factory function with type hints
- Update both manager fixtures to use shared setup
- Maintain all existing skip conditions and error handling

### Test Configuration Logic
Consolidate GitHub token and repository URL retrieval:
- Environment variables (priority 1): `GITHUB_TOKEN`, `GITHUB_TEST_REPO_URL`
- Config file fallback (priority 2): `github.token`, `github.test_repo_url`
- Graceful skipping when configuration missing

## ALGORITHM

### Shared Setup Logic
```
1. Check environment variables for GitHub token and test repo URL
2. Fall back to config file if environment variables not set  
3. Skip test if either token or repo URL missing
4. Clone test repository to temporary directory
5. Return structured setup data for manager creation
```

## DATA

### GitHubTestSetup Structure
```python
class GitHubTestSetup(TypedDict):
    git_dir: Path           # Cloned repository directory
    github_token: str       # Validated GitHub token
    test_repo_url: str      # Test repository URL
```

### Manager Factory Function
```python
def create_github_manager[T](
    manager_class: type[T], 
    git_dir: Path, 
    github_token: str
) -> T
```

## LLM Prompt

```
Create shared GitHub test fixture to eliminate duplication between manager test fixtures.

Context: Read pr_info/steps/summary.md and pr_info/steps/decisions.md for overview.
Reference: Current test fixtures in tests/utils/test_github_operations.py

Tasks:
1. Create GitHubTestSetup TypedDict with fields: git_dir, github_token, test_repo_url
2. Create github_test_setup fixture that:
   - Consolidates GitHub configuration validation logic
   - Handles environment variable and config file fallbacks  
   - Clones test repository to tmp_path
   - Returns GitHubTestSetup structure
   - Uses same skip conditions as existing fixtures
3. Create generic create_github_manager helper function:
   - Uses TypeVar for generic manager type
   - Mocks user_config.get_config_value appropriately
   - Returns configured manager instance
4. Update labels_manager fixture to use shared setup
5. Update pr_manager fixture to use shared setup
6. Remove duplicated configuration logic from both fixtures

Implementation notes:
- Maintain all existing skip conditions and error messages
- Keep same configuration priority: env vars > config file
- Preserve all debugging output from pr_manager fixture
- Use proper type hints with TypeVar for generic function
- All existing tests must pass without modification

Run tests:
1. pytest tests/utils/test_github_operations.py::TestLabelsManagerUnit -v  
2. pytest tests/utils/test_github_operations.py::TestPullRequestManagerUnit -v
Expected: All tests PASS (fixtures refactored but behavior unchanged)
```

## Notes

- Pure refactoring of test infrastructure
- All existing test behavior must be preserved
- Reduce fixture code duplication by ~60%
- Maintain all skip conditions and error handling
- Improve test maintainability and consistency
