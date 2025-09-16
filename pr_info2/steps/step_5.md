# Step 5: Implement Shared Test Fixtures

## Objective
Implement robust, reusable git repository fixtures in `conftest.py` to support all test scenarios while minimizing setup overhead and ensuring consistent test environments.

## WHERE
- File: `tests/utils/conftest.py`
- Dependencies: `git`, `pytest`, `pathlib`

## WHAT
Implement 3 core fixtures and helper utilities:

### Core Fixtures
```python
@pytest.fixture
def git_repo(tmp_path) -> tuple[Repo, Path]

@pytest.fixture  
def git_repo_with_commits(tmp_path) -> tuple[Repo, Path]

@pytest.fixture
def complex_git_state(tmp_path) -> tuple[Repo, Path, dict]
```

### Helper Functions
```python
def create_test_files(project_dir: Path, file_specs: dict) -> None
def setup_git_config(repo: Repo) -> None  
def verify_git_state(repo: Repo, expected_commits: int = None) -> dict
```

## HOW
### Fixture Design Principles
- Return both `git.Repo` object and `Path` to project directory
- Configure git user for commits (required for git operations)
- Create realistic file structures for testing
- Provide different repository states (empty, with commits, complex)
- Minimize setup time while ensuring isolation

### Integration Points
```python
# Import in test files
from git import Repo

# Fixture usage pattern
def test_something(self, git_repo):
    repo, project_dir = git_repo
    # Use project_dir for file operations
    # Use repo for git state verification
```

## ALGORITHM
```
1. Create temporary directory using pytest tmp_path
2. Initialize git repository using Repo.init()
3. Configure git user.name and user.email (required for commits)
4. Create test files based on fixture type
5. Perform initial commits if needed for fixture type
6. Return tuple of (repo_object, project_path)
```

## DATA
### Fixture Return Types
```python
# git_repo fixture
return (Repo, Path)  # Empty repo ready for first commit

# git_repo_with_commits fixture  
return (Repo, Path)  # Repo with 2-3 committed files

# complex_git_state fixture
return (Repo, Path, dict)  # Repo with mixed staged/modified/untracked
# dict = {"staged": [...], "modified": [...], "untracked": [...]}
```

### Test File Specifications
```python
# Standard test files for git_repo_with_commits
test_files = {
    "README.md": "# Test Project\\n\\nA sample project for testing.",
    "src/main.py": "def main():\\n    print('Hello, World!')",
    "src/__init__.py": "",
    ".gitignore": "*.pyc\\n__pycache__/\\n.env"
}

# Complex state files for complex_git_state
complex_files = {
    "committed": {"existing.txt": "original content"},
    "staged": {"new_feature.py": "def new_feature(): pass"}, 
    "modified": {"existing.txt": "modified content"},
    "untracked": {"temp.md": "temporary notes"}
}
```

## LLM Prompt for Implementation
```
Based on the Git Operations Test Simplification Summary and previous steps, implement Step 5 to create robust git repository fixtures in tests/utils/conftest.py.

Create 3 fixtures that provide different git repository states for testing:

1. git_repo: Clean, empty git repository
2. git_repo_with_commits: Repository with 2-3 committed files 
3. complex_git_state: Repository with mixed staged/modified/untracked files

Each fixture should:
- Use tmp_path to create isolated test directory
- Initialize git repository with Repo.init()
- Configure git user.name and user.email (required for commits)
- Create realistic test files for the scenario
- Return tuple of (repo_object, project_directory_path)
- Be fast and reliable for repeated test runs

Also create helper functions for common operations:
- create_test_files(): Create files from specifications
- setup_git_config(): Configure git user for repository
- verify_git_state(): Check repository state for assertions

Example fixture implementation:
```python
import pytest
from pathlib import Path
from git import Repo

@pytest.fixture
def git_repo(tmp_path):
    \"\"\"Create a clean git repository for testing.\"\"\"
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # Initialize git repository
    repo = Repo.init(project_dir)
    
    # Configure git user (required for commits)
    setup_git_config(repo)
    
    return repo, project_dir

@pytest.fixture
def git_repo_with_commits(tmp_path):
    \"\"\"Create git repository with sample committed files.\"\"\"
    repo, project_dir = git_repo(tmp_path)
    
    # Create initial files
    test_files = {
        "README.md": "# Test Project\\n\\nSample project for testing.",
        "src/main.py": "def main():\\n    print('Hello, World!')",
        "src/__init__.py": "",
    }
    
    create_test_files(project_dir, test_files)
    
    # Stage and commit files
    repo.index.add(["README.md", "src/main.py", "src/__init__.py"])
    repo.index.commit("Initial commit")
    
    return repo, project_dir

def setup_git_config(repo: Repo) -> None:
    \"\"\"Configure git user for repository.\"\"\"
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

def create_test_files(project_dir: Path, file_specs: dict) -> None:
    \"\"\"Create test files from specifications.\"\"\"
    for file_path, content in file_specs.items():
        full_path = project_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
```

Focus on creating fixtures that are:
- Fast to set up and tear down
- Provide realistic git repository states
- Support all the test scenarios from previous steps
- Return consistent data structures
- Handle git configuration properly
```

## Verification
- [ ] All 3 fixtures can be imported and used
- [ ] git_repo creates clean repository with proper git config
- [ ] git_repo_with_commits has committed files and proper history
- [ ] complex_git_state provides mixed staged/modified/untracked files
- [ ] Helper functions work correctly
- [ ] Fixtures are fast (each takes <100ms to create)
- [ ] All test files from previous steps can use these fixtures
