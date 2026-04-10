# Step 3: Regenerate Snapshot SVGs

> See [summary.md](summary.md) for full context and architectural decisions.

## LLM Prompt

Regenerate iCoder snapshot baselines for issue #752. Read `pr_info/steps/summary.md` for context, then implement this step. The `BusyIndicator` widget was added to the layout in steps 1-2, which changes all snapshot baselines. Regenerate and verify them.

## WHERE

- **Modify**: `tests/icoder/__snapshots__/test_snapshots/*.svg` (8 files)

## WHAT

Regenerate all 8 snapshot SVG files. The new `BusyIndicator` widget adds a `✓ Ready` row to the layout, shifting all baselines.

### Affected snapshots

1. `test_snapshot_initial_state.svg`
2. `test_snapshot_after_help.svg`
3. `test_snapshot_after_conversation.svg`
4. `test_snapshot_long_line_wraps.svg`
5. `test_snapshot_input_area_grows.svg`
6. `test_snapshot_autocomplete_all_commands.svg`
7. `test_snapshot_autocomplete_filtered.svg`
8. `test_snapshot_autocomplete_no_match.svg`
9. `test_snapshot_multi_chunk_streaming.svg`

## HOW

1. Run snapshot tests with `--snapshot-update` flag to regenerate baselines
2. Verify the regenerated SVGs contain the `✓ Ready` indicator text
3. Verify no secrets, env vars, or local paths leaked into SVGs
4. Run snapshot tests again (without `--snapshot-update`) to confirm they pass

### Commands

```bash
# Regenerate
pytest tests/icoder/test_snapshots.py --snapshot-update

# Verify they pass
pytest tests/icoder/test_snapshots.py
```

## ALGORITHM

```
1. Run pytest --snapshot-update on snapshot test file
2. Inspect generated SVGs for "✓ Ready" text presence
3. Inspect generated SVGs for no secrets/paths
4. Run pytest again without --snapshot-update to confirm pass
5. Run full quality checks (pylint, mypy, pytest)
```

## DATA

No code changes — only SVG file regeneration.

## TESTS

No new tests. Existing 8 snapshot tests are regenerated and must all pass.

## Commit

```
test(icoder): regenerate snapshot baselines for BusyIndicator (#752)
```
