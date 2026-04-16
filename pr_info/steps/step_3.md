# Step 3 — Add `langchain_transitive_isolation` import-linter contract

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`).
> Implement ONLY step 3: add one new grouped `forbidden` contract to
> `.importlinter`. Do NOT touch `pyproject.toml` or docs. Verify with
> `mcp__tools-py__run_lint_imports_check`; it must pass. Also run pylint,
> pytest, mypy (must still pass — unrelated but mandated by CLAUDE.md).
> Commit: `chore(imports): add langchain_transitive_isolation contract`.

## WHERE

Single file: `.importlinter` — add one new section near the existing
`langchain_library_isolation` / `langchain_vendor_sdk_isolation` blocks.

## WHAT

Add the following contract block. Pattern mirrors `langchain_library_isolation`
exactly (same `source_modules`, same dual-form `ignore_imports` of
`providers.langchain` and `providers.langchain.**`).

```ini
# -----------------------------------------------------------------------------
# Contract: LangChain Transitive Dependencies Isolation
# -----------------------------------------------------------------------------
# langchain_mcp_adapters, langgraph, truststore, and httpx are transitive
# optional dependencies installed via [langchain-base]. Only the langchain
# provider package may import them. Grouped into one contract because the
# boundary (source_modules + ignore_imports) is identical for all four —
# same grouping style as langchain_library_isolation above.
# -----------------------------------------------------------------------------
[importlinter:contract:langchain_transitive_isolation]
name = LangChain Transitive Dependencies Isolation
type = forbidden
source_modules =
    mcp_coder
forbidden_modules =
    langchain_mcp_adapters
    langgraph
    truststore
    httpx
ignore_imports =
    mcp_coder.llm.providers.langchain -> langchain_mcp_adapters
    mcp_coder.llm.providers.langchain.** -> langchain_mcp_adapters
    mcp_coder.llm.providers.langchain -> langgraph
    mcp_coder.llm.providers.langchain.** -> langgraph
    mcp_coder.llm.providers.langchain -> truststore
    mcp_coder.llm.providers.langchain.** -> truststore
    mcp_coder.llm.providers.langchain -> httpx
    mcp_coder.llm.providers.langchain.** -> httpx
```

## HOW

Use `mcp__workspace__edit_file` to append the new block at the end of the
"THIRD-PARTY LIBRARY ISOLATION CONTRACTS" region in `.importlinter`,
directly after the `langchain_vendor_sdk_isolation` contract to keep all
langchain isolation blocks adjacent.

**Pre-condition (already true after step 1):** `mcp_manager.py` lives at
`mcp_coder.llm.providers.langchain.mcp_manager`, so its
`from langchain_mcp_adapters.client import …` falls inside the
`providers.langchain.**` allow-list.

## ALGORITHM

```
1. Insert the new [importlinter:contract:langchain_transitive_isolation]
   block after langchain_vendor_sdk_isolation.
2. Run lint-imports.
   - If fails on langchain_mcp_adapters: confirm step 1's move landed.
   - If fails on langgraph/truststore/httpx: identify the source module
     outside providers.langchain and fix (expected: no hits — these are
     only imported from inside providers/langchain/).
3. Run pylint / pytest (fast) / mypy — all green.
```

## DATA

No runtime data. Contract metadata only. The `lint-imports` output must
show the new contract listed under "KEPT".

## Verification

- `mcp__tools-py__run_lint_imports_check` — **primary gate**; must show:
  ```
  LangChain Transitive Dependencies Isolation KEPT
  ```
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_pytest_check` (fast subset)
- `mcp__tools-py__run_mypy_check`

## Commit

```
chore(imports): add langchain_transitive_isolation contract

One grouped forbidden contract covering the four transitive optional
dependencies (langchain_mcp_adapters, langgraph, truststore, httpx).
Mirrors the dual-form ignore_imports pattern of langchain_library_isolation
so the same providers/langchain/** boundary applies. Valid only after
mcp_manager.py moved under providers/langchain/ in the previous commit.

Refs #829
```
