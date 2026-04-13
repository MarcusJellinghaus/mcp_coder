# Step 2: Return native TOML types and validate at load time

**Commit message:** `config: return native TOML types from get_config_values with schema validation`

> Read `pr_info/steps/summary.md` for full context. This is Step 2: the core behavior change in `user_config.py`.

## Goal

Make `_get_nested_value()` return native TOML types instead of strings.
Add schema-driven type validation in `get_config_values()`.
Replace `_get_standard_env_var()` with schema lookup.

## WHERE

`src/mcp_coder/utils/user_config.py`

## WHAT — Changes

### 1. `_get_nested_value()` — return native type

```python
def _get_nested_value(
    config_data: dict[str, Any], section: str, key: str
) -> str | bool | int | list | None:
```

**Change:** Delete lines 184-185 (`return str(value) if value is not None else None`), replace with `return value`.

### 2. `get_config_values()` — update signature + add validation

```python
def get_config_values(
    keys: list[tuple[str, str, str | None]],
) -> dict[tuple[str, str], str | bool | int | list | None]:
```

**Add after `_get_nested_value()` call:** schema validation block.

### 3. Delete `_get_standard_env_var()` — replace with schema lookup

In `get_config_values()`, replace:
```python
actual_env_var = env_var or _get_standard_env_var(section, key)
```
with:
```python
field_def = _get_field_def(section, key)
actual_env_var = env_var or (field_def.env_var if field_def else None)
```

## ALGORITHM — validation in `get_config_values`

```
value = _get_nested_value(config_data, section, key)
if value is not None:
    field_def = _get_field_def(section, key)
    if field_def is not None and not isinstance(value, field_def.field_type):
        raise ValueError(
            f"Config error in [{section}] {key}: "
            f"expected {field_def.field_type.__name__}, "
            f"got {type(value).__name__} ('{value}'). "
            f"Check your config.toml — use native TOML types."
        )
results[(section, key)] = value
```

## DATA — return type change

**Before:** `dict[tuple[str, str], str | None]`
**After:** `dict[tuple[str, str], str | bool | int | list | None]`

## Tests

`tests/utils/test_user_config.py` — modify and add:

### Modify existing test

`test_get_config_values_converts_non_string_to_string` → rename to `test_get_config_values_preserves_native_types`:

```python
def test_get_config_values_preserves_native_types(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Native TOML types (int, bool) are preserved, not converted to string."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        "[settings]\ntimeout = 30\ndebug = true", encoding="utf-8"
    )
    monkeypatch.setattr(
        "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
    )

    result = get_config_values([
        ("settings", "timeout", None),
        ("settings", "debug", None),
    ])

    assert result[("settings", "timeout")] == 30
    assert result[("settings", "debug")] is True
```

### Add new tests

```python
class TestConfigTypeValidation:
    """Tests for schema-driven type validation in get_config_values."""

    def test_string_in_bool_field_raises_valueerror(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TOML string 'true' in a bool field raises ValueError."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[mlflow]\nenabled = "true"\n', encoding="utf-8"
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        with pytest.raises(ValueError, match="expected bool.*got str"):
            get_config_values([("mlflow", "enabled", None)])

    def test_string_in_int_field_raises_valueerror(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TOML string "3" in an int field raises ValueError."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[vscodeclaude]\nworkspace_base = "/tmp"\nmax_sessions = "3"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        with pytest.raises(ValueError, match="expected int.*got str"):
            get_config_values([("vscodeclaude", "max_sessions", None)])

    def test_native_bool_in_bool_field_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Native TOML bool in a bool field passes validation."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("[mlflow]\nenabled = true\n", encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        result = get_config_values([("mlflow", "enabled", None)])
        assert result[("mlflow", "enabled")] is True

    def test_unknown_section_key_no_validation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Keys not in schema pass through without validation."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('[custom]\nfoo = "bar"\n', encoding="utf-8")
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        result = get_config_values([("custom", "foo", None)])
        assert result[("custom", "foo")] == "bar"

    def test_env_var_bypasses_type_validation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env var values are strings and bypass schema type validation."""
        monkeypatch.setenv("GITHUB_TOKEN", "env_token_string")

        # github.token is type str in schema, env var is also str — no issue
        result = get_config_values([("github", "token", None)])
        assert result[("github", "token")] == "env_token_string"

    def test_valueerror_message_includes_context(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ValueError message includes section, key, expected type, actual type, value."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[mlflow]\nenabled = "yes"\n', encoding="utf-8"
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        with pytest.raises(ValueError, match=r"\[mlflow\].*enabled.*bool.*str.*yes"):
            get_config_values([("mlflow", "enabled", None)])

    def test_wildcard_section_validates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """coordinator.repos.* fields are validated against wildcard schema."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            '[coordinator.repos.myrepo]\nrepo_url = "https://example.com"\n'
            'update_issue_labels = "true"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mcp_coder.utils.user_config.get_config_file_path", lambda: config_file
        )

        with pytest.raises(ValueError, match="expected bool.*got str"):
            get_config_values([
                ("coordinator.repos.myrepo", "update_issue_labels", None)
            ])
```

### Update `get_cache_refresh_minutes` tests

The `get_cache_refresh_minutes` function currently does `int(value)` on a string.
After this step, `value` will be a native `int` from TOML. Update the function:

```python
def get_cache_refresh_minutes() -> int:
    config = get_config_values([("coordinator", "cache_refresh_minutes", None)])
    value = config[("coordinator", "cache_refresh_minutes")]
    if value is None:
        return 1440
    if isinstance(value, int):
        if value <= 0:
            logger.warning(...)
            return 1440
        return value
    # Env var case: value is str
    try:
        result = int(value)
        ...
```

The test `test_get_cache_refresh_minutes_from_config` already uses native TOML (`cache_refresh_minutes = 60`) which will now return `int` 60 directly — test should still pass. The parameterized test with `'"not_a_number"'` will now raise `ValueError` at load time (string in int field) — update that test case.

### Update `tests/cli/test_utils.py`

- Delete `from mcp_coder.utils.user_config import _get_standard_env_var` import (line 16)
- Delete `test_get_standard_env_var_mcp_config` test — it tests a function being removed
- Alternatively, replace with a test that verifies the schema has the correct env var mapping for `mcp.default_config_path`

## Checklist
- [ ] `_get_nested_value()` returns native types (remove `str()` conversion)
- [ ] `get_config_values()` return type updated
- [ ] Schema validation added in `get_config_values()`
- [ ] `_get_standard_env_var()` deleted, replaced by schema lookup
- [ ] `get_cache_refresh_minutes()` updated for native int
- [ ] `tests/cli/test_utils.py`: remove `_get_standard_env_var` import and test
- [ ] Existing tests updated, new validation tests added
- [ ] All checks pass (pylint, pytest, mypy)
