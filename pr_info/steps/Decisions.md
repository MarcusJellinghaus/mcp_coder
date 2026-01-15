# Decisions Log - Issue #284

## Discussed Decisions

### 1. uv Action Version
**Decision:** Keep `astral-sh/setup-uv@v4` as specified in the plan.

**Rationale:** Safe, tested version. No need to chase latest.

---

### 2. Install Command Simplification
**Decision:** Use `".[dev]"` instead of `".[dev,types]"`.

**Rationale:** The `dev` optional dependency already includes `types` via `mcp-coder[types,test,mcp]` in pyproject.toml. Using `".[dev]"` follows the DRY principle and avoids redundancy.

---

### 3. Rollback Documentation
**Decision:** Skip adding rollback documentation to the plan.

**Rationale:** Reverting to pip if needed is straightforward (undo the changes). Not worth documenting.

---

### 4. structlog Cleanup
**Decision:** Out of scope for this issue.

**Rationale:** The observation that `structlog` remains in dependencies after commit `bce299a` ("replace structlog with standard logging") should be addressed in a separate issue to keep this PR focused on CI migration.
