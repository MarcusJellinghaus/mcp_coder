# Decisions - Vulture Integration

## Discussion Date: 2026-01-13

### 1. CI Job Placement
**Decision:** Add vulture to `architecture` job (PR-only), not `test` job.

**Rationale:** Dead code detection is closer to architecture checks. Running only on PRs provides faster feedback on regular pushes.

### 2. Whitelist Style
**Decision:** Use attribute-style whitelist (`_.item_name` format).

**Rationale:** More explicit and easier to maintain than dummy function approach.

### 3. Step Structure
**Decision:** Split original Step 1 into:
- Step 0: Add vulture dependency to pyproject.toml
- Step 1: Create whitelist file

**Note:** Step 0 was completed during discussion (vulture added to dev requirements).

### 4. Keep Steps 2 and 3 Separate
**Decision:** Keep source file cleanup (Step 2) and test file cleanup (Step 3) as separate steps.

**Rationale:** Maintains clear distinction between source and test code changes.

### 5. CI Scope
**Decision:** Include both `src` and `tests` directories in CI check.

**Command:** `vulture src tests vulture_whitelist.py --min-confidence 80`

### 6. Fixture Handling
**Decision:** Whitelist unused fixture parameters (e.g., `require_claude_cli`) rather than renaming to underscore prefix.

### 7. Whitelist Approach
**Decision:** Whitelist liberally now, review the list later in a separate issue.

**Rationale:** Avoids blocking implementation on deciding every item; allows focused review later.

### 8. Task Tracker
**Decision:** Leave TASK_TRACKER.md empty for now.
