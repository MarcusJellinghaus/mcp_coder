# Plan Decisions — Issue #829

This file logs decisions taken during plan-revision discussions.

## 2026-04-16 — Plan-review feedback application

### Decision 1 — Extend step 4 to cover all doc call-sites listed in issue #829 (finding #1)

**User decision:** extend step 4 (not defer). Issue #829's scope lists
install hints in four doc files; prior plan only touched the new
`optional-dependencies.md` page and `README.md`. Step 4 now also adds a
one-line pointer at the existing `[langchain]`/install mentions in:

- `docs/configuration/config.md` (around line 215 — existing
  `pip install 'mcp-coder[langchain]'` example)
- `docs/configuration/mlflow-integration.md` (around line 17 — existing
  `[mlflow]` install block)
- `docs/architecture/architecture.md` (around line 193 — existing
  `langchain/` optional-install bullet)

Exact wording is the implementer's call; the requirement is that each page
acquires a visible pointer to the new reference page.

### Decision 2 — Pin down README insertion location (finding #2)

**User decision:** the prior "near Installation or Documentation block"
phrasing was too vague. Step 4 now specifies: insert a new
`#### Optional features` subsection directly after the
`pip install -e ".[dev]"` fenced block under `### Installation`, before
the `## 📚 Documentation` heading. Heading depth is `####` so it nests
under `### Installation`.

### Decision 3 — Clarify `move_module` parameter form (finding #4)

**User decision:** tool-signature inspection confirms
`mcp__tools-py__move_module` documents both `source_module` and
`dest_package` as "path relative to project root", so the existing
filesystem-path form in step 1 is correct. Added a short **Fallback**
note to step 1: if the tool rejects filesystem paths in this environment,
retry with the dotted-module form
(`mcp_coder.llm.mcp_manager` → `mcp_coder.llm.providers.langchain`).

### Skipped findings

- **Finding #3** (optional `[mcp]` removal TOML comment) — skipped per user.
- **Finding #5** (automated equivalence test for `pip install [langchain]`
  package set) — out of scope per issue, deferred to #838.
