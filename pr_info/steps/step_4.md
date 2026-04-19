# Step 4: Add PROJECT section to verify command

## Context
See `pr_info/steps/summary.md` for full design. This step adds an informational PROJECT section to `mcp-coder verify`.

## WHERE
- `src/mcp_coder/cli/commands/verify.py` — add `_print_project_section()` and call it from `execute_verify()`
- `tests/cli/commands/test_verify.py` — add tests for new section

## WHAT

### New function
```python
def _print_project_section(project_dir: Path, symbols: dict[str, str]) -> None:
    """Print the PROJECT section showing language detection and tool config."""
```

### Output format (Python detected):
```
=== PROJECT ==========================================
  pyproject.toml       [OK] found
  Language             [OK] Python (detected)

  [Python]
    format_code        [OK] enabled
    check_type_hints   [WARN] not configured (default: disabled)
```

### Output format (non-Python):
```
=== PROJECT ==========================================
  pyproject.toml       [WARN] not found
  Language             [OK] (none detected)
```

## HOW

### New import in verify.py:
```python
from ...utils.pyproject_config import get_implement_config
```

### Implementation:
```python
def _print_project_section(project_dir: Path, symbols: dict[str, str]) -> None:
    print(_pad("PROJECT"))
    pyproject_exists = (project_dir / "pyproject.toml").exists()
    if pyproject_exists:
        print(f"  {'pyproject.toml':<20s} {symbols['success']} found")
        print(f"  {'Language':<20s} {symbols['success']} Python (detected)")
        config = get_implement_config(project_dir)
        print()
        print("  [Python]")
        # format_code
        if config.format_code:
            print(f"    {'format_code':<18s} {symbols['success']} enabled")
        else:
            print(f"    {'format_code':<18s} {symbols['warning']} not configured (default: disabled)")
        # check_type_hints
        if config.check_type_hints:
            print(f"    {'check_type_hints':<18s} {symbols['success']} enabled")
        else:
            print(f"    {'check_type_hints':<18s} {symbols['warning']} not configured (default: disabled)")
    else:
        print(f"  {'pyproject.toml':<20s} {symbols['warning']} not found")
        print(f"  {'Language':<20s} {symbols['success']} (none detected)")
```

### Call site in `execute_verify()`:
Insert `_print_project_section(project_dir, symbols)` after the ENVIRONMENT section (before CONFIG section).

## ALGORITHM
```
print header "PROJECT"
if pyproject.toml exists:
    print "found", "Python (detected)"
    read implement config
    print format_code status (enabled or "not configured")
    print check_type_hints status (enabled or "not configured")
else:
    print "not found", "(none detected)"
```

## DATA
- Input: `project_dir: Path`, `symbols: dict[str, str]`
- Output: prints to stdout (no return value)
- Informational only — does not affect exit code

## TESTS (write first)
Add to `tests/cli/commands/test_verify.py`:
1. `test_project_section_python_both_enabled` — pyproject.toml with both `true` → shows `[OK] enabled` for both
2. `test_project_section_python_defaults` — pyproject.toml exists but no implement section → shows `[WARN] not configured` for both
3. `test_project_section_non_python` — no pyproject.toml → shows `[WARN] not found` and `(none detected)`

## LLM PROMPT
```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_4.md.

Add _print_project_section() to verify.py and call it from execute_verify()
after the ENVIRONMENT section. The section is informational only (no exit code
impact). Write tests first, then implement.
```
