# Step 1: Create Test Data and Add Unit Tests for Multi-Phase Parsing (TDD)

## Summary Reference
See [summary.md](summary.md) for overall context and design decisions.

## Objective
Create test data file and add comprehensive unit tests for multi-phase task tracker parsing before implementing the fix.

---

## WHERE: File Paths

| Action | File Path |
|--------|-----------|
| Create | `tests/workflow_utils/test_data/multi_phase_tracker.md` |
| Modify | `tests/workflow_utils/test_task_tracker.py` |

---

## WHAT: Test Functions to Add

### In `tests/workflow_utils/test_task_tracker.py`

```python
class TestMultiPhaseTaskTracker:
    """Tests for multi-phase task tracker parsing."""

    def test_find_implementation_section_includes_all_phases(self) -> None:
        """Test that _find_implementation_section includes content from all phases."""

    def test_get_incomplete_tasks_across_phases(self) -> None:
        """Test getting incomplete tasks from multiple phases."""

    def test_get_step_progress_includes_all_phases(self) -> None:
        """Test that get_step_progress returns steps from all phases."""

    def test_phase_headers_recognized_as_continuations(self) -> None:
        """Test that phase headers don't terminate section parsing."""

    def test_backward_compatibility_single_phase(self) -> None:
        """Test that single-phase trackers still work correctly."""
```

---

## HOW: Integration Points

1. **Test Data Loading**: Use `Path(__file__).parent / "test_data" / "multi_phase_tracker.md"`
2. **Imports**: Use existing imports from `task_tracker` module
3. **Test Class**: Add new `TestMultiPhaseTaskTracker` class to existing test file

---

## ALGORITHM: Test Data Structure

```markdown
# Task Tracker with Phases

## Tasks

## Phase 1: Complete Phase ✅
### Step 1: Done
- [x] Task A (complete)

## Phase 2: In Progress 📋
### Step 2: Pending  
- [ ] Task B (incomplete) ← Must be found!
- [ ] Task C (incomplete) ← Must be found!

## Pull Request
- [ ] PR task (should NOT be found)
```

---

## DATA: Expected Test Results

| Test Function | Input | Expected Output |
|---------------|-------|-----------------|
| `test_get_incomplete_tasks_across_phases` | multi_phase_tracker.md | `["Task B", "Task C"]` (excludes PR task) |
| `test_get_step_progress_includes_all_phases` | multi_phase_tracker.md | Dict with Step 1 AND Step 2 |
| `test_find_implementation_section_includes_all_phases` | multi_phase_tracker.md | Content contains "Phase 2" |

---

## Implementation Details

### 1. Create Test Data File: `tests/workflow_utils/test_data/multi_phase_tracker.md`

```markdown
# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

---

## Tasks

## Phase 1: Initial Implementation (Steps 1-2) ✅ COMPLETE

### Step 1: Setup Infrastructure
- [x] Create directory structure
- [x] Add configuration files
- [x] Run quality checks

### Step 2: Core Implementation  
- [x] Implement main logic
- [x] Add error handling

---

## Phase 2: Code Review Fixes (Steps 3-4) 📋 NEW

### Step 3: Fix Documentation
- [ ] Update README with examples
- [ ] Add inline code comments
- [x] Fix typos in docstrings

### Step 4: Clean Up Code
- [ ] Remove unused imports
- [ ] Simplify complex functions

---

## Pull Request

- [ ] Review all changes
- [ ] Create pull request
```

### 2. Add Test Class to `tests/workflow_utils/test_task_tracker.py`

Add after existing test classes:

```python
class TestMultiPhaseTaskTracker:
    """Tests for multi-phase task tracker parsing."""

    @pytest.fixture
    def multi_phase_content(self) -> str:
        """Load multi-phase test tracker content."""
        test_data_path = Path(__file__).parent / "test_data" / "multi_phase_tracker.md"
        return test_data_path.read_text(encoding="utf-8")

    def test_find_implementation_section_includes_all_phases(
        self, multi_phase_content: str
    ) -> None:
        """Test that _find_implementation_section includes content from all phases."""
        section = _find_implementation_section(multi_phase_content)
        
        # Should include content from both phases
        assert "Phase 1" in section or "Step 1" in section
        assert "Phase 2" in section or "Step 3" in section
        assert "Update README with examples" in section
        # Should NOT include Pull Request section
        assert "Review all changes" not in section

    def test_get_incomplete_tasks_across_phases(
        self, multi_phase_content: str
    ) -> None:
        """Test getting incomplete tasks from multiple phases."""
        # Use internal function with content string
        incomplete = _get_incomplete_tasks(multi_phase_content)
        
        # Should find incomplete tasks from Phase 2
        assert "Update README with examples" in incomplete
        assert "Add inline code comments" in incomplete
        assert "Remove unused imports" in incomplete
        assert "Simplify complex functions" in incomplete
        
        # Should NOT include completed tasks
        assert "Create directory structure" not in incomplete
        assert "Fix typos in docstrings" not in incomplete
        
        # Should NOT include Pull Request tasks
        assert "Review all changes" not in incomplete
        assert "Create pull request" not in incomplete

    def test_get_step_progress_includes_all_phases(self) -> None:
        """Test that get_step_progress returns steps from all phases."""
        with TemporaryDirectory() as temp_dir:
            # Copy test data to temp directory
            test_data_path = Path(__file__).parent / "test_data" / "multi_phase_tracker.md"
            tracker_path = Path(temp_dir) / "TASK_TRACKER.md"
            tracker_path.write_text(test_data_path.read_text(encoding="utf-8"))
            
            progress = get_step_progress(temp_dir)
            
            # Should have steps from both phases
            step_names = list(progress.keys())
            assert any("Step 1" in name for name in step_names)
            assert any("Step 3" in name or "Step 4" in name for name in step_names)

    def test_phase_headers_recognized_as_continuations(self) -> None:
        """Test that phase headers don't terminate section parsing."""
        content = """# Task Tracker

## Tasks

## Phase 1: Done ✅
- [x] Task from phase 1

## Phase 2: In Progress
- [ ] Task from phase 2

## Pull Request
- [ ] PR task
"""
        section = _find_implementation_section(content)
        
        # Phase 2 content should be included
        assert "Task from phase 2" in section
        # PR section should be excluded
        assert "PR task" not in section

    def test_backward_compatibility_single_phase(self) -> None:
        """Test that single-phase trackers still work correctly."""
        content = """# Task Tracker

## Tasks

### Step 1: Setup
- [x] Complete task
- [ ] Incomplete task

### Pull Request
- [ ] Create PR
"""
        incomplete = _get_incomplete_tasks(content)
        
        assert incomplete == ["Incomplete task"]
```

---

## Verification

After implementing tests, run:
```bash
pytest tests/workflow_utils/test_task_tracker.py::TestMultiPhaseTaskTracker -v
```

**Expected Result**: 
- The **multi-phase tests** (tests 1-4) should **FAIL** initially (TDD - tests first, then implementation)
- The **backward compatibility test** (`test_backward_compatibility_single_phase`) should **PASS** since it uses existing functionality

---

## LLM Prompt for Step 1

```
You are implementing Step 1 of issue #156: Support for Multi-Phase Task Tracker.

CONTEXT:
- See pr_info/steps/summary.md for overall design
- See pr_info/steps/step_1.md for this step's details

TASK:
1. Create test data file: tests/workflow_utils/test_data/multi_phase_tracker.md
2. Add TestMultiPhaseTaskTracker class to tests/workflow_utils/test_task_tracker.py
3. Run the new tests to verify they FAIL (TDD approach)

REQUIREMENTS:
- Follow existing code style and patterns in the test file
- Import required functions from task_tracker module
- Use pytest fixtures for test data loading
- Tests should fail initially (implementation comes in Step 2)

FILES TO MODIFY:
- tests/workflow_utils/test_data/multi_phase_tracker.md (CREATE)
- tests/workflow_utils/test_task_tracker.py (ADD test class)
```
