# Task Status Tracker

## Instructions for LLM
This tracks Feature Implementation consisting of multiple Implementation Steps (tasks).

**Task format:**
- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete

---

## Tasks

### Implementation Steps

- [ ] **Step 1: Setup Data Models** - [step_1.md](steps/step_1.md)
  - [ ] Create package structure
  - [x] Define TaskInfo dataclass
  - [ ] Implement exception hierarchy

- [x] **Step 2: Core Parser** - [step_2.md](steps/step_2.md)
  - [x] Implement section parsing
  - [x] Add task extraction logic

- [ ] **Step 3: Public API** - [step_3.md](steps/step_3.md)
  - [ ] Implement get_incomplete_tasks()
  - [ ] Implement is_task_done()

### Pull Request

- [ ] **Quality Checks**
  - [ ] Run pylint checks
  - [ ] Run pytest validation