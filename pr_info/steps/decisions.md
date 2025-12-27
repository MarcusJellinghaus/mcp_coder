# Decisions Log - CI Pipeline Restructure

Decisions made during plan review discussion.

## Decision 1: Remove Test Files
**Topic**: Should we create `tests/ci/` test files to validate the matrix approach?
**Decision**: Remove entirely — rely on manual verification by running the workflow during PR review.
**Rationale**: YAML parsing tests cannot verify GitHub Actions runtime behavior; manual verification is more effective.

## Decision 2: Consolidate Steps
**Topic**: Should we keep 4 steps or consolidate?
**Decision**: Consolidate to 1 step (implement + documentation). Verification happens during PR review.

## Decision 3: Artifact Uploads
**Topic**: How should we handle JUnit XML artifact uploads in the matrix approach?
**Decision**: Skip for now — out of scope for this change.

## Decision 4: Job Naming
**Topic**: What should the job name prefix be in GitHub UI?
**Decision**: Keep "test" → displays as "test (black)", "test (isort)", etc.

## Decision 5: check-forbidden-folders Dependency
**Topic**: Should all matrix jobs wait for `check-forbidden-folders`?
**Decision**: Keep `check-forbidden-folders` as a separate job, remove the `needs` dependency from the test matrix so checks run immediately in parallel.

## Decision 6: Documentation Update
**Topic**: What level of documentation update in `docs/architecture/ARCHITECTURE.md`?
**Decision**: Minimal — add a brief note (~2-3 lines) in Cross-cutting Concepts mentioning matrix-based CI.
