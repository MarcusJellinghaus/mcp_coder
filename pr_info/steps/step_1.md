# Step 1: Create Test Structure and Label Constants

## Objective
Set up test file structure and define the 10 workflow labels as constants with TDD approach.

## Context
Reference `summary.md` for overview. This step establishes the foundation: label definitions and test scaffolding.

## WHERE
- Create: `tests/workflows/test_define_labels.py`
- Create: `workflows/define_labels.py` (skeleton)

## WHAT

### In `workflows/define_labels.py`:
```python
WORKFLOW_LABELS = [
    ("status-01:created", "10b981", "Fresh issue, may need refinement"),
    ("status-02:awaiting-planning", "6ee7b7", "Issue is refined and ready for implementation planning"),
    ("status-03:planning", "a7f3d0", "Implementation plan being drafted (auto/in-progress)"),
    ("status-04:plan-review", "3b82f6", "First implementation plan available for review/discussion"),
    ("status-05:plan-ready", "93c5fd", "Implementation plan approved, ready to code"),
    ("status-06:implementing", "bfdbfe", "Code being written (auto/in-progress)"),
    ("status-07:code-review", "f59e0b", "Implementation complete, needs code review"),
    ("status-08:ready-pr", "fbbf24", "Approved for pull request creation"),
    ("status-09:pr-creating", "fed7aa", "Bot is creating the pull request (auto/in-progress)"),
    ("status-10:pr-created", "8b5cf6", "Pull request created, awaiting approval/merge"),
]
```

### In `tests/workflows/test_define_labels.py`:
```python
def test_workflow_labels_constant():
    """Verify WORKFLOW_LABELS has correct structure."""
    assert len(WORKFLOW_LABELS) == 10
    assert all(len(label) == 3 for label in WORKFLOW_LABELS)
    assert all(label[0].startswith("status-") for label in WORKFLOW_LABELS)
```

## HOW
- Import: `from workflows.define_labels import WORKFLOW_LABELS`
- Colors stored without '#' prefix (GitHub API format)
- Tuple structure: `(name, color, description)`

## ALGORITHM
```
1. Define WORKFLOW_LABELS as list of 10 tuples
2. Each tuple: (label_name, hex_color, description_text)
3. Names follow pattern: status-NN:state-name
4. Colors are 6-char hex without '#'
5. Descriptions from workflow document
6. Validate color format at module load (6-char hex)
```

## DATA
- **WORKFLOW_LABELS**: `list[tuple[str, str, str]]`
- Each tuple: `(name: str, color: str, description: str)`

## LLM Prompt
```
Reference: pr_info/steps/summary.md

Implement Step 1: Create test structure and label constants.

Tasks:
1. Create tests/workflows/test_define_labels.py with test_workflow_labels_constant()
2. Create workflows/define_labels.py with WORKFLOW_LABELS constant containing all 10 status labels from pr_info/github_Issue_Coder_Workflow.md
3. Extract exact names, colors, and descriptions from the workflow document
4. Ensure colors are 6-char hex WITHOUT '#' prefix
5. Add color validation at module load - validate all colors are 6-char hex format
6. Run pytest to verify constant structure

Follow existing test patterns from tests/workflows/.
```
