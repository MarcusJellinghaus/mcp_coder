# Step 2 — Enforce GitHub label length limits in `validate_labels_config()`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Write the tests first, then the validator change, run the code quality checks
> from CLAUDE.md, and produce one commit. Step 1 must already be committed.

Precondition: step 1 is done (`labels.json` no longer contains
`code-review-ci-undeterminable`). If it still does, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- `tests/config/test_label_config.py` → class `TestValidateLabelsConfig`
- `src/mcp_coder/config/label_config.py` → `validate_labels_config()`

## WHAT

Signature unchanged:

```python
def validate_labels_config(labels_config: dict[str, Any]) -> None
```

New tests (methods of `TestValidateLabelsConfig`):

```python
@pytest.mark.parametrize(("field", "length"), [("name", 51), ("description", 101)])
def test_field_too_long_raises(self, field: str, length: int) -> None

@pytest.mark.parametrize(("field", "length"), [("name", 50), ("description", 100)])
def test_field_at_limit_passes(self, field: str, length: int) -> None
```

## HOW

### Tests first

Each test builds a one-label config in the style of the existing tests, then
overrides one field:

```python
label = {
    "internal_id": "long_label",
    "name": "a",
    "color": "000000",
    "description": "a",
    "category": "human_action",
    "default": True,
}
label[field] = "x" * length
config = {"workflow_labels": [label]}
```

- too-long: `pytest.raises(ValueError, match=rf"long_label.*{field}.*{length}")`
- at-limit: `validate_labels_config(config)` does not raise

`pytest` is already imported; no new imports.

### Implementation

After the existing promotable loop, add one loop:

```python
for label in labels:
    name_len = len(label["name"])
    if name_len > 50:
        raise ValueError(
            f"Label '{label['internal_id']}' name is {name_len} characters "
            f"(GitHub limit: 50)"
        )
    desc_len = len(label.get("description", ""))
    if desc_len > 100:
        raise ValueError(
            f"Label '{label['internal_id']}' description is {desc_len} "
            f"characters (GitHub limit: 100)"
        )
```

Extend the docstring `Checks:` list:

```
4. Each label name is at most 50 characters (GitHub limit)
5. Each label description is at most 100 characters (GitHub limit)
```

## ALGORITHM

```
for each label in workflow_labels:
    if len(name) > 50: raise ValueError(internal_id, len, 50)
    if len(description or "") > 100: raise ValueError(internal_id, len, 100)
```

## DATA

Returns `None`; raises `ValueError` with a message containing the `internal_id`,
field, actual length and limit. No new constants or types.

## Checks

- pylint, pytest (fast unit set, `-n auto`), mypy — all pass.
  `test_valid_config_passes` now also covers the bundled `labels.json` lengths.
- Commit: `feat(label_config): validate GitHub label name/description length`
