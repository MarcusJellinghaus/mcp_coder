# Decisions

## 1. Exclude tests/ from docstring scope

**Decision:** Only fix docstrings in `src/`. Exclude `tests/` from D102 and DOC rules.

**Rationale:** Good test names are self-documenting. Adding ~109 one-line docstrings that rephrase the test name is busywork with near-zero value. This eliminates ~190 fixes and removes Step 3 entirely.

**Action:** Update ruff config to ignore D102/DOC rules for `tests/`.

## 2. DOC502 policy — keep 3-option judgment call

**Decision:** For each DOC502 violation, choose between:
1. Remove the Raises entry (default — stale docs)
2. Keep and add `noqa: DOC502` (exception propagates from callee, intentionally documented)
3. Fix the code (raise statement accidentally removed)

**Rationale:** Careful per-violation analysis is appropriate for Raises documentation since it affects API contracts.

## 3. Step 5 structure — keep as one step

**Decision:** Do not split Step 5 into sub-steps. Process by directory during execution for coherent context.

**Rationale:** DOC501 and DOC502 require the same analysis (read the function, check what it raises). ~86 fixes in `src/` is manageable in one pass.

## 4. Commit granularity — one commit per step

**Decision:** One commit per step (4 commits total after Step 3 removal).
