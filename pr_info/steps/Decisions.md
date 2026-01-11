# Decisions

## Decision 1: Add exports to `workflow_utils/__init__.py`

**Question:** Should we add exports to `workflow_utils/__init__.py` for the moved functions?

**Decision:** Yes, add exports after moving the file.

**Rationale:** Allows shorter imports like `from mcp_coder.workflow_utils import generate_commit_message_with_llm`.

---

## Decision 2: Verification approach

**Question:** Should we include a manual functional test step in addition to unit tests?

**Decision:** Unit tests only.

**Rationale:** The ~66 unit tests covering `commit_operations` are comprehensive enough for this pure refactoring.

---

## Decision 3: Step structure

**Question:** Should we consolidate the 4 implementation steps into fewer steps?

**Decision:** Keep 4 separate steps.

**Rationale:** Easier to follow, clearer checkpoints, better for debugging if something goes wrong.
