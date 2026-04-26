# Step 3 — Snapshot update

> **Ref:** [summary.md](summary.md) • Issue #896

## Goal

Regenerate SVG snapshot baselines that may have changed due to the auto-grow height calculation now using visual (wrapped) line count instead of logical line count.

## WHERE

- `tests/icoder/__snapshots__/test_snapshots/*.svg` — regenerated files

## WHAT

Run snapshot tests with `--snapshot-update` to capture the new rendering baselines:

```
pytest tests/icoder/test_snapshots.py --snapshot-update
```

## HOW

The snapshots affected are likely:

- `test_snapshot_input_area_grows.svg` — multiline input auto-grow height may differ
- `test_snapshot_long_line_wraps.svg` — if the long line wrapping affects input area height

Other snapshots (`test_snapshot_initial_state`, `test_snapshot_after_help`, etc.) should be unaffected since they don't involve multiline input content.

## Verification

After regeneration:

1. Review each updated SVG to confirm it looks correct (no secrets, no local paths)
2. Run all snapshot tests without `--snapshot-update` to confirm they pass
3. Run full test suite to confirm no regressions

## Commit message

```
test(icoder): update snapshot baselines for wrapped auto-grow (#896)
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement step 3: regenerate snapshot SVG baselines.

1. Run snapshot tests with --snapshot-update to regenerate baselines
2. Review updated SVGs for correctness (no secrets/local paths)
3. Run full test suite to confirm everything passes
```
