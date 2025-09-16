# Step 4: Implement Simplified Test Fixtures

## Objective
Implement streamlined, reusable git repository fixtures in `conftest.py` to support all test scenarios while minimizing setup overhead and ensuring consistent test environments.

## WHERE
- File: `tests/utils/conftest.py`
- Dependencies: `git`, `pytest`, `pathlib`

## WHAT
Implement 2 core fixtures and helper utilities:

### Core Fixtures
```python
@pytest.fixture
def git_repo(tmp_path) -> tuple[Repo, Path]

@pytest.fixture  
def git_repo_with_files(tmp_path) -> tuple[Repo, Path]
```

### Helper Functions
```python
def setup_git_config(repo: Repo) -> None  
def create_sample_files(project_dir: Path, file_specs: dict) -> None
def verify_git_state(repo: Repo, expected_commits: int = None) -> dict
```

## HOW
### Fixture Design Principles
- Return both `git.Repo` object and `Path` to project directory
- Configure git user for commits (required for git operations)
- Create realistic but simple file structures for testing
- Provide two repository states: empty and with committed files
- Minimize setup time while ensuring isolation
- Let tests create complex states inline when needed

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
4. For git_repo_with_files: create 2-3 sample files and commit them
5. Return tuple of (repo_object, project_path)
```

## DATA
### Fixture Return Types
```python
# git_repo fixture
return (Repo, Path)  # Empty repo ready for first commit

# git_repo_with_files fixture  
return (Repo, Path)  # Repo with 2-3 committed files ready for modification
```

### Sample Test Files for git_repo_with_files
```python
# Simple test files for modification scenarios
sample_files = {
    "README.md": "# Test Project\\n\\nA sample project for testing.",
    "main.py": "def main():\\n    print('Hello, World!')",
    "config.yml": "debug: false\\nport: 8080"
}
```

## LLM Prompt for Implementation
```
Based on the Git Operations Test Simplification Summary and previous steps, implement Step 4 to create streamlined git repository fixtures in tests/utils/conftest.py.

Create 2 fixtures that provide different git repository states for testing:

1. git_repo: Clean, empty git repository
2. git_repo_with_files: Repository with 2-3 committed files for modification testing

Each fixture should:
- Use tmp_path to create isolated test directory
- Initialize git repository with Repo.init()
- Configure git user.name and user.email (required for commits)
- Create simple, realistic test files for git_repo_with_files
- Return tuple of (repo_object, project_directory_path)
- Be fast and reliable for repeated test runs

Also create helper functions for common operations:
- setup_git_config(): Configure git user for repository
- create_sample_files(): Create files from specifications
- verify_git_state(): Check repository state for assertions

Example fixture implementation:
```python
import pytest
from pathlib import Path
from git import Repo

@pytest.fixture
def git_repo(tmp_path):
    \"\"\"Create a clean, empty git repository for testing.\"\"\"
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # Initialize git repository
    repo = Repo.init(project_dir)
    
    # Configure git user (required for commits)
    setup_git_config(repo)
    
    return repo, project_dir

@pytest.fixture
def git_repo_with_files(tmp_path):
    \"\"\"Create git repository with sample committed files for modification tests.\"\"\"
    repo, project_dir = git_repo(tmp_path)
    
    # Create simple test files
    sample_files = {
        "README.md": "# Test Project\\n\\nSample project for testing.",
        "main.py": "def main():\\n    print('Hello, World!')",
        "config.yml": "debug: false\\nport: 8080"
    }
    
    create_sample_files(project_dir, sample_files)
    
    # Stage and commit files
    repo.index.add(list(sample_files.keys()))
    repo.index.commit("Initial commit with sample files")
    
    return repo, project_dir

def setup_git_config(repo: Repo) -> None:
    \"\"\"Configure git user for repository.\"\"\"
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

def create_sample_files(project_dir: Path, file_specs: dict) -> None:
    \"\"\"Create test files from specifications.\"\"\"
    for file_path, content in file_specs.items():
        full_path = project_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
```

Focus on creating fixtures that are:
- Fast to set up and tear down
- Provide realistic git repository states
- Support both empty repo and modification scenarios
- Return consistent data structures
- Handle git configuration properly
- Simple and focused (avoid complex states - let tests create those inline)
```

## Verification
- [ ] Both fixtures can be imported and used
- [ ] git_repo creates clean repository with proper git config
- [ ] git_repo_with_files has committed files and proper history
- [ ] Helper functions work correctly
- [ ] Fixtures are fast (each takes <100ms to create)
- [ ] All test files from previous steps can use these fixtures
- [ ] Complex states can be created inline in tests when needed
