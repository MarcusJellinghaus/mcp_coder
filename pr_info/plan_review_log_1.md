# Plan Review Log — Issue #829 (run 1)

Branch: `829-refactor-packaging-reorganise-optional-extras-and-tighten-import-linter-isolation`
Started: 2026-04-16

## Round 1 — 2026-04-16

**Findings** (from engineer review):
1. [design] Install-hint call-sites in `docs/configuration/config.md`, `docs/configuration/mlflow-integration.md`, `docs/architecture/architecture.md` remain untouched by step 4 despite being listed in issue #829 scope.
2. [structural] README "Optional features" insertion location ambiguous ("near existing Installation or Documentation block").
3. [structural/minor] Optional TOML comment explaining `[mcp]` extra removal in `[dev]`.
4. [structural] Step 1's `move_module` call uses filesystem-path form; dotted-module form may be required by the tool.
5. [design/noted] No automated test for `[langchain-base]` / meta-`[langchain]` package-set equivalence.

**Decisions**:
- Finding #1 → **ask user**. User chose: extend step 4 to add one-line pointers at all three existing `[langchain]` mention sites.
- Finding #2 → **accept**. Pin README insertion to a `#### Optional features` subsection directly after the `pip install -e ".[dev]"` block under `### Installation`, before `## 📚 Documentation`.
- Finding #3 → **skip**. Minor/optional; commit message already covers the rationale.
- Finding #4 → **accept**. Keep filesystem-path form (confirmed correct via tool docstring) and add a fallback note for the dotted form.
- Finding #5 → **skip/noted**. Explicitly deferred to issue #838 per #829 scope.

**User decisions**:
- Q: How should step 4 handle the three existing docs that still promote bare `pip install 'mcp-coder[langchain]'`?
  A: Extend step 4 — add pointers in all 3 files.

**Changes applied** (via `/plan_update`):
- `pr_info/steps/step_4.md` — retitled to cover all four doc sites; added WHERE/WHAT/HOW entries for the three existing-doc pointer insertions; pinned README insertion location; expanded acceptance criteria and link-check scope to four links; updated commit subject/body.
- `pr_info/steps/step_1.md` — added fallback note for dotted-module form of `move_module`.
- `pr_info/steps/summary.md` — added the three doc files to the Modified list; updated §4 Documentation architectural description; updated step sequence label and acceptance bullet.
- `pr_info/steps/Decisions.md` — new file logging applied decisions and skipped findings.

**Status**: Plan updated; commit pending.


## Round 2 — 2026-04-16

**Findings**: none.

**Round 1 verification**:
- Step 4 WHERE/HOW/Acceptance consistently list all four doc sites (new `optional-dependencies.md` + pointers in `docs/configuration/config.md`, `docs/configuration/mlflow-integration.md`, `docs/architecture/architecture.md`).
- README insertion location pinned to a `#### Optional features` subsection directly after the `pip install -e ".[dev]"` fenced block and before `## 📚 Documentation` — slot verified against current README.
- Step 1 dotted-module fallback note present with concrete arguments.
- `summary.md` Modified list and Acceptance block match step 4's scope.
- `Decisions.md` logs decisions and skipped findings.
- Step 2's `[dev]` replacement matches current `pyproject.toml` (drops `mcp`, keeps `types,test,langchain,mlflow,tui`).

**Status**: no changes needed — plan is internally consistent and covers issue #829 scope.

## Final Status

- **Rounds run**: 2
- **Commits produced**: 1 (`docs(plan): extend step 4 to update existing [langchain] docs, clarify step 1 + step 4 details (#829)`) + this log commit.
- **Outcome**: plan is ready for implementation approval.
- **Deferred items** (not blockers):
  - Finding #3 — optional TOML comment about `[mcp]` extra removal.
  - Finding #5 — automated `[langchain-base]` vs meta-`[langchain]` equivalence test (explicitly deferred to issue #838 per #829 scope).
