# Decisions

Decisions made during plan review discussion for issue #468.

---

## Decision 1: Empty-list fallback when cache build failed (Step 2)

**Question:** When `_build_cached_issues_by_repo` fails for a repo, `cached_issues_by_repo`
has no entry for it. The derived `all_cached_issues` is `[]` (not `None`), so
`process_eligible_issues` skips `get_all_cached_issues` — no sessions are started for that repo.
Should we pass `None` instead to allow `process_eligible_issues` to fetch independently?

**Decision:** Pass `[]` (keep it simple), but log an `error` so the silent "no sessions"
behaviour is visible in logs.

---

## Decision 2: Unit test for Step 2 caller wiring

**Question:** Should a unit test be added to `test_commands.py` verifying that
`process_eligible_issues` is called with `all_cached_issues` populated correctly?

**Decision:** No test needed for Step 2. Argument wiring is verified by mypy and pylint
(static analysis). Step 1's unit test already proves the parameter behaviour end-to-end.
