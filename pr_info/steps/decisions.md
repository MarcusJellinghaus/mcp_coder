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

## 5. Split remaining work into small tasks to avoid timeout

**Decision:** Steps 1–5 partially completed but left ~102 violations. Split remaining work into 6 small tasks (steps 6–11) instead of retrying as one large task.

**Rationale:** The CI-fix loop timed out twice (3600s each) trying to fix all remaining violations in a single LLM session. Smaller tasks reduce the risk of timeout and make progress incremental.

**Action:** Steps 6–11 added. Each targets a specific rule or small set of rules.

## 6. Split DOC201 (Returns) into two batches by directory

**Decision:** DOC201 fixes split into step 8 (cli, config, formatters, checks, mcp_tools, prompt_manager) and step 9 (llm, utils, workflows, workflow_utils).

**Rationale:** 32 DOC201 violations require reading each function to understand return values. Splitting by directory keeps each batch manageable.

## 7. Split Raises fixes into DOC502 then DOC501

**Decision:** DOC502 (remove extraneous, step 10) before DOC501 (add missing, step 11).

**Rationale:** Removing stale entries (DOC502) is simpler and can be done first. Adding missing Raises (DOC501) is the final step and includes a full `ruff check src tests` verification.
