# Step 5 — `verify` warnings for unknown, retired, misplaced and conflicting keys

See `pr_info/steps/summary.md` (design change 4).

## WHERE

- New `src/mcp_coder/cli/commands/verify_project_keys.py`
- `src/mcp_coder/cli/commands/verify_sections.py` — `_print_project_section` (both branches)
- `src/mcp_coder/cli/commands/verify.py` — PROMPTS section
- New `tests/cli/commands/test_verify_project_keys.py`

## WHAT

```python
# verify_project_keys.py
_TOP = "tool.mcp-coder"
_SETTINGS = ("format_code", "labels-config", "prompts")   # decision-1 settings
_PYTHON_ONLY = frozenset({"install", "install-from-github"})
_LEGACY_IMPLEMENT_KEYS = frozenset({"format_code", "check_type_hints"})  # have own rows
# key -> known inner keys; None = scalar, or validated elsewhere (toolkit, setup)
_SCHEMA: dict[str, frozenset[str] | None] = {
    "format_code": None,
    "labels-config": None,
    "toolkit": None,
    "setup": None,
    "prompts": frozenset({"system-prompt", "project-prompt", "claude-system-prompt-mode"}),
    "install": frozenset({"extras", "post_install_checks"}),
    "install-from-github": frozenset({"packages", "packages-no-deps"}),
}

class KeyWarning(NamedTuple):
    section: str   # "PROMPTS" or "PROJECT"
    file: str      # row label, e.g. "mcp-coder.toml"
    message: str

def scan_project_keys(project_dir: Path) -> list[KeyWarning]: ...

def key_warning_rows(project_dir: Path, section: str, symbols: dict[str, str], indent: int = 2) -> list[Row]:
    """[WARN] rows for one verify section."""
    # [Row(w.file, symbols["warning"], w.message, indent, wrap=True) for w in scan if w.section == section]
```

## ALGORITHM (`scan_project_keys`)

```
defined = {}                                   # setting -> [files]
for file in MCP_CODER_CONFIG_FILES:
    try: data = load_toml(project_dir / file, strict=True)
    except TomlReadError: warn(PROJECT, file, "cannot be parsed; format_code, labels-config and prompts use their defaults"); continue
    table = data.get("tool", {}); table = table.get("mcp-coder", {}) if isinstance(table, dict) else None
    if not isinstance(table, dict): same "cannot be parsed" warning; continue
    for key, value in table.items(): classify (below); record file in defined[key] if key in _SETTINGS
for setting, files in defined.items() with len(files) == 2:
    warn(PROMPTS if setting == "prompts" else PROJECT, "mcp-coder.toml",
         f"[tool.mcp-coder] {setting} is defined in both pyproject.toml and mcp-coder.toml; default used")
```

Classify one `key` of `[tool.mcp-coder]` in `file`:
- `key == "implement"`:
  - in `mcp-coder.toml` → `"[tool.mcp-coder.implement] is retired and ignored"`;
  - in `pyproject.toml`, when it is a dict → one warning per inner key not in
    `_LEGACY_IMPLEMENT_KEYS`: `"[tool.mcp-coder.implement] {k} is retired and ignored"`.
- `key in _PYTHON_ONLY` and `file == "mcp-coder.toml"` →
  `"[tool.mcp-coder.{key}] is Python-only; ignored in mcp-coder.toml"`. Don't scan its inner keys.
- `key not in _SCHEMA` → `"unknown key [tool.mcp-coder] {key}"`, plus
  `" — " + hint` when `unknown_key_hint(_TOP, key, [*_SCHEMA, "implement"])` returns one.
- `_SCHEMA[key]` is a frozenset and `value` is a dict → for each inner key not in
  it: `"unknown key [tool.mcp-coder.{key}] {k}"` plus a hint from
  `unknown_key_hint(f"{_TOP}.{key}", k, known)`. Section is `PROMPTS` when
  `key == "prompts"`, else `PROJECT`.

All warnings use `file` as the row label, except the conflict warning.

## HOW

- Imports:
  - `from ...config.toml_utils import MCP_CODER_CONFIG_FILES, TomlReadError, load_toml`;
  - `from ...utils.config_hints import unknown_key_hint`;
  - `from .verify_formatting import Row`.
- `_print_project_section` (both branches): just before `out.close()`, call
  `out.add(*key_warning_rows(project_dir, "PROJECT", symbols))`. Don't touch `ok`.
- `verify.py`: just before `out.section("PROMPTS", prompt_lines)`, call
  `prompt_lines.extend(key_warning_rows(project_dir, "PROMPTS", symbols))`.
  Don't touch `prompts_ok`.
- Keep the module's docstring short: it says what the scan reports and that its
  rows are warnings only, because the exit code must not change.

## DATA

`list[KeyWarning]` in file order, then the conflict warnings. `list[Row]` for rendering.

## Tests (write first) — `tests/cli/commands/test_verify_project_keys.py`

Unit tests on `scan_project_keys(tmp_path)`:
- `[tool.mcp-coder.setpu]` in `pyproject.toml`, and again in `mcp-coder.toml`
  (parametrize) → a PROJECT warning containing `setpu` and `did you mean setup?`,
  labelled with that file;
- `project_prompt` inside `prompts` → a PROMPTS warning containing
  `did you mean project-prompt?`;
- `[tool.mcp-coder.implement]` with `foo = 1` in `pyproject.toml` → a retired
  warning for `foo`;
- `implement` with only `format_code` / `check_type_hints` in `pyproject.toml`
  → no warning;
- any `implement` table in `mcp-coder.toml` → a retired warning;
- `[tool.mcp-coder.install]` in `mcp-coder.toml` → a Python-only warning;
- `install` in `pyproject.toml` with `extra = "x"` → an unknown-key warning
  (hint `extras`);
- malformed `mcp-coder.toml` → a PROJECT warning labelled `mcp-coder.toml`;
- `format_code` in both files → a PROJECT conflict warning; `prompts` in both
  files → a PROMPTS conflict warning;
- a fully valid config (known keys, toolkit, setup) → `[]`.

Integration:
- `_print_project_section` on a `pyproject.toml` containing
  `[tool.mcp-coder.setpu]` → the output has a `[WARN]` row with `setup`, and the
  function returns the same value as without the bad table. Reuse the
  `_stub_toolkit` pattern from `test_verify_project_section.py`.
- `execute_verify` on a tmp project with `project_prompt` inside `prompts` → the
  PROMPTS section has the `[WARN]` row, and the exit code equals the exit code
  of the same project without that key. Follow the `_run_verify` /
  `_make_verify_mocks` pattern of `test_verify_prompts_context.py`.

## Checks

pylint, mypy, pytest (fast set), lint-imports, tach, vulture,
`check_file_size`; then `run_format_code`. One commit:
`feat(verify): warn about unknown and misplaced [tool.mcp-coder] keys`.

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md` with
> TDD:
> - write `tests/cli/commands/test_verify_project_keys.py` first;
> - create `cli/commands/verify_project_keys.py` with `_SCHEMA`, `KeyWarning`,
>   `scan_project_keys` and `key_warning_rows`;
> - add the PROJECT rows at the end of `_print_project_section` (both branches)
>   and the PROMPTS rows in `verify.py`.
>
> Warnings must never change `ok`, `prompts_ok` or the exit code. Run pylint,
> mypy, pytest, lint-imports, tach, vulture and the file-size check. Commit once.
