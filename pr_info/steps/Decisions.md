# Decisions

Decisions agreed during plan review discussion.

---

## D1 — Simplified `load_labels_config` branch logic

**Decision:** Use the simplified single-branch form instead of an explicit `if/else`.

```python
if isinstance(config_path, Path) and not config_path.exists():
    raise FileNotFoundError(f"Label configuration not found: {config_path}")
text = config_path.read_text(encoding="utf-8")
```

**Rationale:** Both `Path` and `Traversable` expose `.read_text()`. The branch only needs
to guard the `FileNotFoundError` for the `Path` case. The `if/else` form duplicated
the `.read_text()` call unnecessarily.

---

## D2 — No `ignore_labels` validation

**Decision:** Do not add validation for the `ignore_labels` key in `load_labels_config`.

**Rationale:** Out of scope for this bug fix. The existing behaviour (no validation of
`ignore_labels`) is preserved intentionally.

---

## D3 — Mypy checks covered by CLAUDE.md

**Decision:** No explicit "run mypy" instruction needs to be added to the step files.

**Rationale:** CLAUDE.md already mandates running all three quality checks (pylint,
pytest, mypy) after every code change. Adding it to individual steps would be redundant.

---

## D4 — No grep safety gate before Step 3

**Decision:** Do not add an explicit grep check for `Path(get_labels_config_path(...))`
callers at the start of Step 3.

**Rationale:** The existing test suite and mypy strict checks will catch any caller that
wraps the return value in `Path(...)`. A manual grep step is unnecessary overhead.
