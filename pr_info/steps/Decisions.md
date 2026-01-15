# Decisions Log - Issue #228

Decisions made during plan review discussion.

## Decision 1: Remove `get_config_value()` Entirely

**Options discussed:**
- A) Remove `get_config_value()` entirely (forces all callers to use batch API)
- B) Keep `get_config_value()` as wrapper (backward compatible)
- C) Deprecate `get_config_value()` (gradual migration)

**Decision:** A - Remove entirely

---

## Decision 2: `get_config_values()` API Signature

**Options discussed:**
- A) 3-tuple `(section, key, env_var)` with `None` for auto-detect
- B) 2-tuple with optional `env_var_overrides` dict parameter
- C) 2-tuple only, no env_var override option

**Decision:** A - 3-tuple with `None` for auto-detect, with comprehensive docstring

---

## Decision 3: Test Fixture Complexity

**Options discussed:**
- A) Keep conditional logic (only fetch missing keys)
- B) Simplify to unconditional fetch (always fetch all keys)

**Decision:** A - Keep conditional logic as proposed

---

## Decision 4: `@log_function_call` on `get_config_file_path()`

**Options discussed:**
- A) Remove decorator from `get_config_file_path()`
- B) Keep decorator on `get_config_file_path()`

**Decision:** A - Remove decorator

---

## Decision 5: Redaction Constant

**Options discussed:**
- A) Hardcode `"***"`
- B) Define `REDACTED` constant at module level

**Decision:** A - Hardcode `"***"`

---

## Decision 6: Test Mocking Strategy

**Options discussed:**
- A) Update all mocks in Step 4/5
- B) Create a mock helper function

**Decision:** A - Update all mocks directly in Step 4/5

---

## Decision 7: Lazy vs Eager Loading

**Options discussed:**
- A) Lazy loading (only read config if env var doesn't satisfy key)
- B) Eager loading (always load config once at start)

**Decision:** A - Lazy loading

---

## Decision 8: Edge Case Test for Non-Existent Sensitive Fields

**Options discussed:**
- A) Add explicit test case
- B) Skip it (naturally handled by implementation)

**Decision:** B - Skip (implementation naturally handles this)

---

## Decision 9: `__all__` Export Updates

**Options discussed:**
- A) Add explicit checklist item
- B) Assume it's implied as part of refactoring

**Decision:** B - Implied in normal refactoring
