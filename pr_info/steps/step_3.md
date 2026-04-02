# Step 3: Snapshot Regeneration + Documentation

> **Context:** See `pr_info/steps/summary.md` for full issue context (Issue #683).

## Goal

Regenerate all 3 snapshot baselines after the visual changes from steps 1–2. Add documentation comments explaining the snapshot testing workflow.

## LLM Prompt

```
Implement Step 3 of Issue #683 (see pr_info/steps/summary.md for context).

Three changes:
1. Regenerate snapshot baselines using mcp__tools-py__run_pytest_check with extra_args=["--snapshot-update", "-m", "textual_integration"].
   (These are Windows-only tests with the textual_integration marker.)
2. Verify the generated SVGs do NOT contain environment variables, secrets, or local file paths.
3. Add documentation:
   - In test_snapshots.py: expand the module docstring to explain the snapshot concept (golden SVGs, --snapshot-update to regenerate, Windows-only).
   - In pyproject.toml: add a comment near the textual_integration marker mentioning --snapshot-update.

Run all quality checks after.
```

## WHERE

| File | Action |
|------|--------|
| `tests/icoder/__snapshots__/test_snapshots/test_snapshot_initial_state.svg` | Regenerated |
| `tests/icoder/__snapshots__/test_snapshots/test_snapshot_after_help.svg` | Regenerated |
| `tests/icoder/__snapshots__/test_snapshots/test_snapshot_after_conversation.svg` | Regenerated |
| `tests/icoder/test_snapshots.py` | Add documentation comments |
| `pyproject.toml` | Add comment near marker |

## WHAT

### `test_snapshots.py` — expanded module docstring

```python
"""SVG snapshot tests for iCoder TUI (Windows-only).

Snapshot tests compare rendered TUI output against golden SVG baselines
stored in __snapshots__/. When the UI changes intentionally, regenerate
baselines with:

    pytest tests/icoder/test_snapshots.py --snapshot-update

Baselines are Windows-only to avoid cross-platform rendering drift.
Verify regenerated SVGs contain no secrets, env vars, or local paths.
"""
```

### `pyproject.toml` — comment near marker

Add a comment line above or next to the `textual_integration` marker definition.

## Verification

- All 3 snapshot tests must pass after regeneration (use mcp__tools-py__run_pytest_check with markers=["textual_integration"])
- SVG files must not contain environment variables, secrets, or local file paths
- All quality checks via MCP tools (pylint, mypy, pytest unit tests, lint imports, vulture) must pass

## Commit

`test(icoder): regenerate snapshot baselines and add snapshot docs`
