# Step 3: Core logic — pyproject.toml reading + github install generation

> **Context**: See `pr_info/steps/summary.md` for the full plan.
> This step implements the core feature: reading `[tool.mcp-coder.from-github]`
> from a project's `pyproject.toml` and generating `uv pip install` commands
> in the startup script when `from_github=True`.

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 3.

Add `from_github: bool = False` parameter to `create_startup_script()` in
workspace.py. When True, read `[tool.mcp-coder.from-github]` from the cloned
repo's pyproject.toml and inject `uv pip install` commands into the .bat script.
Write tests first (TDD), then implement. Run all three code quality checks.
```

## Files to Modify

### Tests (write first)

**`tests/workflows/vscodeclaude/test_workspace_startup_script.py`** — Add tests:

- `test_create_startup_script_from_github_injects_install_commands`:
  Create a tmp_path with a `pyproject.toml` containing `[tool.mcp-coder.from-github]`
  with both `packages` and `packages-no-deps`. Call `create_startup_script(from_github=True)`.
  Assert the `.bat` content contains:
  - `uv pip install "pkg1" "pkg2"` (with deps)
  - `uv pip install --no-deps "pkg3"` (no deps)
  - A second `uv pip install -e . --no-deps` (restore editable)
  - `GitHub override` or similar marker comment

- `test_create_startup_script_from_github_false_no_github_section`:
  Call `create_startup_script(from_github=False)`. Assert the `.bat` content
  does NOT contain `GitHub override`.

- `test_create_startup_script_from_github_missing_config_section`:
  Create a `pyproject.toml` WITHOUT `[tool.mcp-coder.from-github]`. Call with
  `from_github=True`. Assert no error, no github install lines in output
  (graceful degradation — just logs a warning).

- `test_create_startup_script_from_github_empty_packages`:
  Create a `pyproject.toml` with empty `packages = []` and `packages-no-deps = []`.
  Call with `from_github=True`. Assert no github install commands in output.

- `test_create_startup_script_from_github_only_packages`:
  Config has `packages` but no `packages-no-deps`. Assert only the with-deps
  install line is generated (plus restore editable).

- `test_create_startup_script_from_github_only_packages_no_deps`:
  Config has `packages-no-deps` but no `packages`. Assert only the no-deps
  install line is generated (plus restore editable).

**`tests/workflows/vscodeclaude/test_workspace.py`** — Update existing test:
- `test_create_startup_script_windows`: Verify it still works with default
  `from_github=False` (backward compatibility).

### Implementation

**`src/mcp_coder/workflows/vscodeclaude/workspace.py`**

- WHERE: `create_startup_script()` function
- WHAT: Add `from_github: bool = False` parameter; when True, read pyproject.toml
  and build github install batch commands
- HOW: After building `venv_section`, conditionally append github install lines

```python
def create_startup_script(
    ...,
    from_github: bool = False,     # ← NEW
) -> Path:
```

### Algorithm (pseudocode)

```python
# Injection point: AFTER `venv_section = VENV_SECTION_WINDOWS.format(...)`
# but BEFORE `STARTUP_SCRIPT_WINDOWS.format(venv_section=venv_section, ...)`
# and `INTERVENTION_SCRIPT_WINDOWS.format(venv_section=venv_section, ...)`.
#
# This means the github override applies to BOTH normal and intervention mode
# scripts, since both consume the `venv_section` variable.
github_install_section = ""
if from_github:
    pyproject_path = folder_path / "pyproject.toml"
    if pyproject_path.exists():
        import tomllib
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)
        gh_config = config.get("tool", {}).get("mcp-coder", {}).get("from-github", {})
        packages = gh_config.get("packages", [])
        packages_no_deps = gh_config.get("packages-no-deps", [])
        if packages or packages_no_deps:
            lines = ["", "REM === GitHub override installs ==="]
            if packages:
                quoted = " ".join(f'"{p}"' for p in packages)
                lines.append(f"uv pip install {quoted}")
            if packages_no_deps:
                quoted = " ".join(f'"{p}"' for p in packages_no_deps)
                lines.append(f"uv pip install --no-deps {quoted}")
            lines.append("uv pip install -e . --no-deps")
            github_install_section = "\n".join(lines)

# Inject after venv_section, before it's consumed by format():
venv_section = venv_section + github_install_section
```

## Data

- Input: `[tool.mcp-coder.from-github]` from `pyproject.toml`
  - `packages`: `list[str]` — package specs with `@ git+https://...`
  - `packages-no-deps`: `list[str]` — package specs installed with `--no-deps`
- Output: batch script lines injected into the startup `.bat` file

## Verification

- All existing `test_workspace.py` tests pass (new param defaults to False)
- New tests pass for all from_github scenarios
- pylint, mypy, pytest all green
