# Step 5 — Version label `mcp-coder v…` + matching doc string

## LLM Prompt

> Read `pr_info/steps/summary.md` and then implement `pr_info/steps/step_5.md`.
> This step is a one-line code change to the status-bar version label,
> a tiny test that pins the new format, and a one-row doc edit.
>
> After the change, run all three quality checks (pylint, pytest, mypy)
> and confirm they pass before producing the single commit for this step.

## WHERE

| Path | Action |
|------|--------|
| `src/mcp_coder/icoder/ui/app.py` | One-line change inside `compose()` |
| `tests/icoder/ui/test_app.py` | One small test asserting the new prefix |
| `docs/icoder/icoder.md` | One-row update in the Status Line table |

## WHAT

Single change inside `ICoderApp.compose()`:

```python
yield Static(f"v{version}", id="status-version")          # before
yield Static(f"mcp-coder v{version}", id="status-version")  # after
```

Doc table row in `docs/icoder/icoder.md` (currently around line 12):

```markdown
| Version | Centre | `v<version>` |               <!-- before -->
| Version | Centre | `mcp-coder v<version>` |     <!-- after  -->
```

## HOW

- The `#status-version` widget is styled `width: auto`, so the longer
  string does not break the layout. No CSS change required.
- `_get_version()` already handles both runtime-info and metadata
  fallback paths — leave it alone.

## ALGORITHM

N/A — single-token f-string edit.

## DATA

- The `Static` widget's text becomes `f"mcp-coder v{version}"` rather
  than `f"v{version}"`.

## Tests

In `tests/icoder/ui/test_app.py`:

1. **Version label has the prefix** —
   `test_status_version_label_has_mcp_coder_prefix`:
   - construct an `ICoderApp` with a `RuntimeInfo` that pins
     `mcp_coder_version="9.9.9"`;
   - inside `app.run_test()`, await pilot pause;
   - locate `app.query_one("#status-version", Static)`;
   - assert `str(widget.render())` starts with `"mcp-coder v9.9.9"` (or
     equivalently, contains `"mcp-coder v9.9.9"`).

That single test pins the user-visible string. No other test changes
are required; the `_get_version()` fallback path is already covered.

## Acceptance

- All three quality checks green.
- The new test passes; existing snapshot tests still pass (status-version
  is `width: auto` and no snapshot pins this exact string today). If a
  snapshot regression appears, regenerate it as part of this commit and
  call out the regen in the commit message.
- Heads-up: if a textual snapshot test fails due to the new label string,
  regenerate the snapshot in this same commit. Run
  `mcp__mcp-tools-py__run_pytest_check` with `markers=['textual_integration']`
  to surface any snapshot regression.
- Single commit, e.g.
  `feat(icoder): prefix status-bar version label with "mcp-coder"`.
