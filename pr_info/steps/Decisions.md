# Decisions Log

## Discussion Date: 2026-01-31

### Decision 1: Step 2 - Missing pr_info/ Directory Behavior
**Question:** What should `check_prerequisites()` do when `pr_info/` directory is missing?

**Decision:** Fail with error message: "folder pr_info not found. Run 'create_plan' first."

**Rationale:** Enforces correct workflow order (create_plan → implement → create_pr). If pr_info/ is missing, it means no plan was created - which is an error, not something to silently fix.

---

### Decision 2: Deleting TASK_TRACKER.md with pr_info/
**Question:** Is deleting `TASK_TRACKER.md` entirely (by deleting `pr_info/`) the intended behavior?

**Decision:** Yes, delete everything. Complete deletion of `pr_info/` folder including TASK_TRACKER.md.

**Rationale:** Clean slate for next feature, simpler implementation.

---

### Decision 3: The .conversations/ Directory
**Question:** Should Step 4 create a `.conversations/` directory inside `pr_info/`?

**Decision:** Yes, create `pr_info/.conversations/` directory.

**Rationale:** It will be used (user confirmed awareness of use case).

---

### Decision 4: Who Creates TASK_TRACKER.md
**Question:** Who should create `TASK_TRACKER.md`?

**Decision:** `create_plan.py` creates it from template when setting up the `pr_info/` structure.

---

### Decision 5: Template Content
**Question:** What should the TASK_TRACKER_TEMPLATE contain?

**Decision:** Use the following exact template:

```markdown
# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->

## Pull Request
```
