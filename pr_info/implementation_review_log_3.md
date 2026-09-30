# Implementation review log 3 — #1047 I4.1 Groups & scenarios

Supervisor-driven review.

## Round 1 — 2026-09-30
**Findings**:
- `loader.py`: the post-merge group map re-expanded each key as a synthesised `@{n}` token; `ref_name` strips whitespace, so a key like `"git "` received `"git"`'s members. Fails closed but misreports `PermissionConfig.groups`.
**Decisions**: Accept — small, bounded correctness fix to the model I4.2 will read.
**Changes**: `expand.py` gains `expand_group(name, groups)` (exact key, no stripping); `loader.py` builds the group map via it; test `test_group_map_expands_by_exact_key`. Scenario sides unaffected.
**Status**: committed
