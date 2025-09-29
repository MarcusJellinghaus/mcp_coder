# Implementation Structure - Visual Overview

## File Tree After Implementation

```
mcp_coder/
│
├── src/mcp_coder/utils/github_operations/
│   ├── __init__.py                 ← MODIFIED: Add LabelsManager export
│   ├── github_utils.py             (existing - reused)
│   ├── pr_manager.py               (existing - reference)
│   └── labels_manager.py           ← NEW: Core implementation
│
├── tests/utils/
│   ├── conftest.py                 (existing - reused fixtures)
│   └── test_github_operations.py   ← MODIFIED: Add 2 test classes
│
└── pr_info/steps/                  ← NEW: Implementation plan
    ├── QUICKSTART.md               Quick reference guide
    ├── FILES.md                    Complete file manifest
    ├── README.md                   Steps overview
    ├── summary.md                  Architecture & design
    ├── decisions.md                Implementation decisions log
    ├── step_1.md                   Unit tests (TDD red)
    ├── step_2.md                   Initialization (TDD green)
    ├── step_3.md                   Integration tests (TDD red)
    └── step_4.md                   CRUD methods (TDD green)
```

## Class Structure

```
LabelsManager
├── Initialization
│   ├── __init__(project_dir)
│   │   ├─> Validate directory exists
│   │   ├─> Check git repository
│   │   ├─> Get GitHub URL
│   │   └─> Get token from config
│   │
│   └── _parse_and_get_repo()
│       └─> Return Repository object
│
├── Validation (Private)
│   ├── _validate_label_name(name)
│   │   └─> Check non-empty, no special chars
│   │
│   └── _validate_color(color)
│       └─> Check 6-char hex string
│
└── CRUD Operations (Public)
    ├── get_labels()
    │   └─> List[LabelData]
    │
    ├── get_label(name)
    │   └─> LabelData
    │
    ├── create_label(name, color, description)
    │   └─> LabelData
    │
    └── delete_label(name)
        └─> bool
```

## Data Flow

```
User Code
   ├─> LabelsManager(project_dir)
   │      │
   │      ├─> Validate inputs
   │      ├─> Get GitHub token
   │      └─> Initialize GitHub client
   │
   ├─> get_labels()
   │      │
   │      ├─> Get Repository
   │      ├─> Fetch labels from GitHub API
   │      └─> Return List[LabelData]
   │
   ├─> get_label(name)
   │      │
   │      ├─> Validate name
   │      ├─> Get Repository
   │      ├─> Fetch specific label from GitHub API
   │      └─> Return LabelData (or {} if not found)
   │
   ├─> create_label(name, color, desc)
   │      │
   │      ├─> Validate name & color
   │      ├─> Get Repository
   │      ├─> Create via GitHub API
   │      └─> Return LabelData
   │
   └─> delete_label(name)
          │
          ├─> Validate name
          ├─> Get Repository
          ├─> Delete via GitHub API
          └─> Return bool
```

## Test Structure

```
Unit Tests (Mock GitHub API)
├── TestLabelsManagerUnit
    ├── test_initialization_requires_project_dir()
    ├── test_initialization_requires_git_repository()
    ├── test_initialization_requires_github_token()
    ├── test_label_name_validation()
    └── test_color_validation()

Integration Tests (Real GitHub API)
└── TestLabelsManagerIntegration
    ├── test_labels_lifecycle()
    │   ├─> Create label with timestamp
    │   ├─> Verify creation
    │   ├─> List and find label
    │   ├─> Delete label
    │   └─> Cleanup in finally
    ├── test_get_label_by_name()
    │   ├─> Create label
    │   ├─> Get label by name
    │   ├─> Verify data matches
    │   ├─> Test nonexistent label returns {}
    │   └─> Cleanup in finally
    └── test_create_label_idempotency()
        ├─> Create label
        ├─> Create again with same name
        ├─> Verify returns existing label
        └─> Cleanup in finally
```

## TDD Workflow

```
Step 1 (Red)                Step 2 (Green)
┌─────────────────┐        ┌──────────────────┐
│  Write Unit     │   →    │  Implement       │
│  Tests          │        │  Initialization  │
│  (5 tests)      │        │  & Validation    │
└─────────────────┘        └──────────────────┘
      FAIL ✗                      PASS ✓
         ↓                           ↓
Step 3 (Red)                Step 4 (Green)
┌─────────────────┐        ┌──────────────────┐
│  Write          │   →    │  Implement       │
│  Integration    │        │  CRUD Methods    │
│  Tests          │        │  (3 methods)     │
└─────────────────┘        └──────────────────┘
      FAIL ✗                      PASS ✓
```

## Dependencies Diagram

```
LabelsManager
    │
    ├─> github (PyGithub)        [Already installed]
    ├─> github_utils             [Existing module]
    ├─> git_operations           [Existing module]
    ├─> user_config              [Existing module]
    └─> log_utils                [Existing module]

No new dependencies required! ✓
```

## Configuration Flow

```
User Config File                  Environment Variable
~/.mcp_coder/config.toml    OR    GITHUB_TOKEN
    ↓                                  ↓
[github]                          os.getenv()
token = "ghp_..."                     ↓
    ↓                                 ↓
get_config_value("github", "token")  ← Priority 2
    ↓
LabelsManager.__init__()
    ↓
Github(token)
    ↓
GitHub API
```

## Implementation Phases

```
Phase 1: Setup & Validation
├── Write validation tests
├── Implement __init__
├── Implement validators
└── Test: All validation tests pass

Phase 2: CRUD Operations
├── Write integration tests
├── Implement get_labels()
├── Implement create_label()
├── Implement delete_label()
└── Test: All tests pass (unit + integration)

Phase 3: Documentation (Optional)
└── Update ARCHITECTURE.md
```

## Success Criteria

✅ All unit tests pass (5 tests)
✅ All integration tests pass (3 tests)
✅ Code follows existing patterns
✅ No new dependencies added
✅ Proper error handling (no exceptions to caller)
✅ Logging on all operations
✅ TypedDict for structured data
