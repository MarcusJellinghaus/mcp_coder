# Step 3 — `verify` reports a leftover `labels-config` as retired

## LLM prompt

Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`. Steps 1–2 are
already committed. Write the test changes first, then the implementation. Run pylint, mypy
and the fast pytest set (see CLAUDE.md), format the code, and produce exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/verify_project_keys.py` — `_SETTINGS`, `_SCHEMA`,
  `_UNPARSEABLE`, `_classify`
- `tests/cli/commands/test_verify_project_keys.py` — class `TestScanProjectKeys`

## WHAT

### Tests first

`TestScanProjectKeys.test_valid_config_has_no_warnings`: remove the line
`'labels-config = "labels.json"\n'` from the `mcp-coder.toml` content.

Add to `TestScanProjectKeys`:
```python
def test_labels_config_is_retired_once_per_file(self, tmp_path: Path) -> None:
    for file_name in ("pyproject.toml", "mcp-coder.toml"):
        _write(tmp_path, file_name, '[tool.mcp-coder]\nlabels-config = "l.json"\n')

    warnings = scan_project_keys(tmp_path)

    assert warnings == [
        KeyWarning(
            "PROJECT", file_name, "[tool.mcp-coder] labels-config is retired and ignored"
        )
        for file_name in ("pyproject.toml", "mcp-coder.toml")
    ]
```
This covers: one row per file, labelled with the file, PROJECT section, no "defined in both"
row, no "did you mean" hint. Exit-code neutrality is structural (warning rows never feed `ok`)
and already covered by `TestProjectSectionWarnings`.

### Implementation

`verify_project_keys.py`:
- `_SETTINGS = ("format_code", "prompts")`
- Remove `"labels-config": None,` from `_SCHEMA`.
- `_UNPARSEABLE = "cannot be parsed; format_code and prompts use their defaults"`
- In `_classify`, directly after the `if key == "implement": ...` block (before the
  `_PYTHON_ONLY` check):
  ```python
  if key == "labels-config":
      return [
          KeyWarning("PROJECT", file_name, f"[{_TOP}] labels-config is retired and ignored")
      ]
  ```

## HOW

No new imports. `scan_project_keys` and `key_warning_rows` are unchanged; the PROJECT
section of `verify` already renders every PROJECT `KeyWarning` as a `[WARN]` row labelled
with its file.

## ALGORITHM

```
_classify(file_name, key, value):
    if key == "implement": ... (unchanged)
    if key == "labels-config": return [retired warning for file_name]
    ... (unchanged: python-only, unknown key + hint, inner keys)
```

## DATA

`KeyWarning(section="PROJECT", file=<file name>, message="[tool.mcp-coder] labels-config is retired and ignored")`.

## Done when

- New test passes; `tests/cli/commands/test_verify_project_keys.py` passes.
- `labels-config` in `src/` appears only in `verify_project_keys.py` (the retired check).
- pylint, mypy, fast pytest set pass.
