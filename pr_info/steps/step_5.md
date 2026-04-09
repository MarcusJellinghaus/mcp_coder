# Step 5 — Snapshot updates

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Update Textual SVG snapshots that changed due to the new `#input-hint` widget in the layout.

## WHERE

- **Modify:** `tests/icoder/__snapshots__/test_snapshots/*.svg` — regenerated baselines

## WHAT

The `#input-hint` Static widget changes the layout of every snapshot (it appears below InputArea). All existing snapshot SVGs need regeneration.

## HOW

```bash
pytest tests/icoder/test_snapshots.py --snapshot-update
```

Then verify the regenerated SVGs:
- Contain the hint text `\ + Enter = newline` in the initial state snapshot
- Don't contain secrets, env vars, or local paths
- Show correct layout (hint below input area, right-aligned)

## ALGORITHM

```
1. Run snapshot tests with --snapshot-update
2. Review generated SVGs for correctness
3. Verify no sensitive data leaked
4. Stage and commit
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md.

Update the Textual snapshot baselines.

1. Run: pytest tests/icoder/test_snapshots.py --snapshot-update
2. Verify the SVGs look correct (hint visible in initial state, hidden when text present).
3. Run all code quality checks (pylint, pytest, mypy). Fix any issues.
4. Commit: "test(icoder): update snapshots for input hint widget (#754)"
```
