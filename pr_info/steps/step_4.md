# Step 4 — Config Section TOML-Style Regrouping

## Goal

Regroup the flat `verify_config()` entries by their `[section]` label at render time. Each `[section]` header appears once, items indented below, blank line between sections. `verify_config()` return shape is unchanged.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement Step 4 as a single commit: replace the flat config-printing loop inside `execute_verify` in `src/mcp_coder/cli/commands/verify.py` with a grouping loop keyed on `entry["label"]`. Write tests first using `capsys` to validate grouping, blank-line separation, and key extraction. Run pylint, pytest, mypy.

## WHERE

- **Modify:** `src/mcp_coder/cli/commands/verify.py` (inside `execute_verify`, the config block only)
- **Modify tests:** `tests/cli/commands/test_verify.py` — add `TestConfigGrouping` class

## WHAT

Replace the existing block:
```python
config_result = verify_config()
lines = ["\n=== CONFIG ==="]
for entry in config_result["entries"]:
    status = entry["status"]
    symbol = {...}.get(status, " ")
    lines.append(f"  {entry['label']:<20s} {symbol} {entry['value']}")
print("\n".join(lines))
```

With a grouping loop that:
1. Prints `_pad("CONFIG")` + blank line.
2. Iterates entries preserving original order; groups by `entry["label"]`.
3. Emits `  [section]` once per group.
4. For each entry, splits `entry["value"]` on first space → `key`, `rest`.
5. Emits `    {key:<18s} {symbol} {rest}`.
6. Blank line between groups.

## HOW

- Uses `STATUS_SYMBOLS` (added in Step 1) and `_pad` (added in Step 2).
- "Config file" label (first entry, when present) — keep as a top-level row (no group header). Detect via `entry["label"] == "Config file"` or `not entry["label"].startswith("[")`.
- Use `itertools.groupby` or a simple "last_label" tracker.

## ALGORITHM

```
print(_pad("CONFIG"))
last_label = None
for entry in entries:
    label = entry["label"]
    if label.startswith("["):
        if label != last_label:
            if last_label is not None: print()  # blank line between groups
            print(f"  {label}")
            last_label = label
        key, _, rest = entry["value"].partition(" ")
        print(f"    {key:<18s} {symbol_for(entry['status'])} {rest}")
    else:
        # top-level rows like "Config file", "Expected path", "Hint"
        print(f"  {label:<20s} {symbol_for(entry['status'])} {entry['value']}")
```

## DATA

- Consumed: `config_result["entries"]` → `list[dict[str, str]]` with keys `label`, `status`, `value`.
- Produced: stdout lines; no return value.

## Tests to Add

```python
class TestConfigGrouping:
    def _entries(self):
        return [
            {"label": "Config file", "status": "ok", "value": "/path/config.toml"},
            {"label": "[github]", "status": "ok", "value": "token configured (config.toml)"},
            {"label": "[github]", "status": "ok", "value": "test_repo_url configured (config.toml)"},
            {"label": "[jenkins]", "status": "ok", "value": "server_url configured (config.toml)"},
        ]

    @patch(_VERIFY + ".verify_config")
    def test_section_header_emitted_once(self, mock_cfg, capsys, ...):
        mock_cfg.return_value = {"entries": self._entries(), "has_error": False}
        # minimal mocking to reach and print the config block
        out = _capture_execute_verify(capsys)
        assert out.count("[github]") == 1
        assert out.count("[jenkins]") == 1

    def test_items_indented_under_section(self, ...):
        # lines starting with "    token" and "    test_repo_url" appear

    def test_blank_line_between_sections(self, ...):
        # validate an empty line between [github] group and [jenkins] group

    def test_key_extracted_from_value(self, ...):
        # "    token" appears, not "    token configured (config.toml)"

    def test_config_file_row_outside_groups(self, ...):
        # "Config file" label has no preceding "[..." header
```

## Verification

All three checks must pass.
