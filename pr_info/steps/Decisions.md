# Decisions

Decisions made during plan review discussion.

---

## D1: `status_labels` initialisation in `get_stale_sessions`

**Decision:** Add `status_labels: list[str] = []` before the `if cached_issues_by_repo:` block in Step 1.

**Rationale:** Makes scoping explicit and prevents any theoretical `UnboundLocalError`. The existing scoping is safe in practice, but the initialisation removes reliance on implicit scoping.

---

## D2: How to drive `is_stale` in `test_reason_stale_with_cache`

**Decision:** Use real session/cache data — do NOT mock `is_session_stale`.

**Rationale:** Setting session `status` to `"status-01:created"` and cached issue label to `"status-04:plan-review"` drives `is_stale = True` purely from in-memory data (no network calls). This is still a pure unit test and tests slightly more end-to-end behaviour.

---

## D3: Add `test_does_not_skip_zombie_vscode_session` to Step 3 unpack fix list

**Decision:** Add this test to the list of tests requiring 2→3-tuple unpack fixes in Step 3.

**Rationale:** The test unpacks `session, git_status = result[0]`, which will raise `ValueError: too many values to unpack` after the return type change. It was omitted from the original Step 3 fix list.
