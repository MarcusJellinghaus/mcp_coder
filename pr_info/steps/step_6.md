# Step 6 — Replace the `architecture.md` §8 subsections with a pointer

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md` exactly.
> Touch only the two subsections named below. The rest of `architecture.md` stays unchanged.
> Make one commit.

## WHERE
`docs/architecture/architecture.md`, `## 8. Cross-cutting Concepts`.

## HOW
- Replace `### Architectural Boundary Enforcement` and its five bullets with:
  ```
  ### Architectural Boundary Enforcement
  Why and how module boundaries, cycles, dead code, dependencies and file size are enforced:
  see [enforcement.md](enforcement.md).
  ```
  (No contract count.)
- Leave `### Refactoring Guidelines` exactly as it is.
- Delete `### Dead Code Detection` and its four bullets.

## ALGORITHM
None.

## DATA
None.

## Checks
- `search_files(pattern="20 contracts|Dead Code Detection", glob="docs/architecture/architecture.md")` returns no hits.
- `search_files(pattern="^### Refactoring Guidelines$", glob="docs/architecture/architecture.md")` finds one hit.

## Commit
`docs(architecture): point architecture.md enforcement section at enforcement.md`
