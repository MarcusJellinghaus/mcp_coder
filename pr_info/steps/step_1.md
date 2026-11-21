# Step 1 — PROJECT `.mcp-file-access` row

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`
> exactly. TDD: write the test first, see it fail, then implement. Keep the
> change minimal. Run the checks listed below; all must pass. One commit.

## Precondition

The dev env must have upstream `.mcp-file-access` support
(`mcp_coder.mcp_workspace.FILE_ACCESS_SUPPORTED is True`; the existing test in
`tests/cli/commands/test_init_file_access.py` asserts it). If it is False, write
one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/cli/commands/verify_sections.py`
- `src/mcp_coder/cli/commands/verify_exit_code.py`
- `tests/cli/commands/test_verify_project_section.py`
- `docs/repository-setup/repo.md`
- `docs/cli-reference.md`

## 1. Tests first — `test_verify_project_section.py`

- Module docstring: add the `.mcp-file-access` row to the list of covered rows,
  e.g. `"""Tests for the PROJECT section's .mcp-file-access, format_code, Formatter, Toolkit, leftover-key rows."""`.
- Add one class `TestFileAccessRow` with one parametrized test, crossed over the
  branch (`with_pyproject` True / False) and these six states:

  | rules file | `FILE_ACCESS_SUPPORTED` | expected fragments (in order of the row) | section returns |
  |---|---|---|---|
  | absent | True | `.mcp-file-access [OK] not present (gitignore defaults)` | True |
  | absent | patched False | `.mcp-file-access [OK] not present (gitignore defaults)` | True |
  | `read-write /.scratch/\n` | True | `.mcp-file-access [OK] valid` | True |
  | `writable /.scratch/\n` | True | `.mcp-file-access [ERR] invalid (`, `unknown level 'writable'` | False |
  | directory (`mkdir`) | True | `.mcp-file-access [ERR] invalid (is a directory)` | False |
  | `writable /.scratch/\n` | patched False | `.mcp-file-access [WARN] not checked (mcp-workspace in this environment does not support .mcp-file-access)` | True |

- Passing baseline per branch (so a False return can only come from the row):
  - `with_pyproject=True`: write `pyproject.toml` with `[tool.black]\n`.
  - `with_pyproject=False`: patch
    `mcp_coder.cli.commands.verify_sections._uses_mcp_tools_py` to return False.
  - The module's autouse `_stub_toolkit` fixture stays in effect.
- Patch the flag with
  `patch("mcp_coder.cli.commands.verify_sections.FILE_ACCESS_SUPPORTED", supported)`.
- Assertions per case:
  1. Position: the line right after the row whose stripped text starts with
     `"Language "` starts with `"  .mcp-file-access "` (indent 2).
  2. Content: wrapped rows span several lines, and `textwrap` may break at a
     hyphen. Compare with all whitespace removed:
     `_squash = lambda s: "".join(s.split())`; each expected fragment's squashed
     form is `in _squash("\n".join(lines))`.
  3. `_print_project_section(...)` return value equals the expected value.
- Use real `tmp_path` files; do not assert the upstream log warning.

Run it — the new cases fail (no row yet).

## 2. Implementation — `verify_sections.py`

### HOW (imports)

```python
from ...mcp_workspace import FILE_ACCESS_SUPPORTED, validate_access_rules
```

Module-level, next to the other `...` imports, so tests can patch
`verify_sections.<name>`.

### WHAT

```python
def _file_access_row(
    project_dir: Path, symbols: dict[str, str], out: SectionBuilder
) -> bool:
    """Add the ``.mcp-file-access`` row (indent 2) to *out*.

    Args: project_dir, symbols, out (same wording as the sibling helpers).

    Returns:
        False if the rules file is invalid (row added as [ERR]).
    """
```

### ALGORITHM

```
ok = True
if not (project_dir / ".mcp-file-access").exists(): OK, "not present (gitignore defaults)"
elif not FILE_ACCESS_SUPPORTED: WARN, "not checked (mcp-workspace in this environment does not support .mcp-file-access)"
elif problems := validate_access_rules(project_dir): ERR, f"invalid ({'; '.join(problems)})", ok = False
else: OK, "valid"
out.add(Row(".mcp-file-access", marker, value, wrap=True)); return ok
```

Use `symbols["success" | "warning" | "failure"]`, never literal markers. A
comment on the flag branch: the old-version stand-in always returns `[]`.

### Integration in `_print_project_section`

- Both branches: directly after the `Language` row,
  `file_access_ok = _file_access_row(project_dir, symbols, out)`.
  - No-pyproject branch: before the `ok = not _uses_mcp_tools_py(...)` line.
  - Pyproject branch: before `out.add("")` / `out.add("  [Python]")`.
- Both returns become `return ok and file_access_ok` (`ok` is assigned fresh
  after the row, so it must not carry the row's result).
- Docstring first line: `Print the PROJECT section: language detection, the
  ``.mcp-file-access`` rules file and tool config.`

### DATA

`_file_access_row` returns `bool`; `_print_project_section` still returns
`bool` (False if any row is `[ERR]`).

## 3. Docstrings — `verify_exit_code.py`

Verify this list against `_print_project_section`, `_format_code_row`,
`_formatter_row`, `_toolkit_rows`, `setup_rows` before writing it:

- Summary paragraph: replace "when the project's formatter configuration is
  invalid" with "when the PROJECT section reports an ``[ERR]`` row".
- `project_ok` arg: "Whether the PROJECT section printed no ``[ERR]`` row:
  format_code, formatter resolution, leftover
  ``[tool.mcp-coder.implement] format_code`` key, Toolkit (load or verify
  failure, or an error item), Setup (invalid config or an unresolvable
  command), or an invalid ``.mcp-file-access``. False → exit 1,
  provider-independent."
- Comment above `if not project_ok:` → `# An [ERR] row in the PROJECT section is
  provider-independent (exit 1).`

## 4. Docs

- `docs/repository-setup/repo.md`, section "MCP file access rules": keep the
  `f626cf8` bullet as is. Add after it:
  `- **An invalid file** (unknown level, unparsable line, not UTF-8, a directory
  at the path) makes mcp-workspace refuse every MCP write. \`mcp-coder verify\`
  shows it as \`[ERR]\` in the PROJECT \`.mcp-file-access\` row and exits 1.`
- `docs/cli-reference.md` line ~203: change "project configuration" to
  "project configuration (including the `.mcp-file-access` rules file; an
  invalid file exits 1)". Leave the smoke-test sentence for step 2.

## Checks

1. `run_pytest_check(extra_args=["-n", "auto", "tests/cli/commands/"])`. Other
   `test_verify*.py` files call the real `_print_project_section` on `tmp_path`
   and now see an extra `[OK] not present` row; adjust only tests that count
   rows exactly.
2. Fast unit suite (marker filter from `.claude/CLAUDE.md`), pylint, mypy,
   `run_lint_imports_check`.
3. `run_format_code`, then commit:
   `feat(verify): report .mcp-file-access validity in the PROJECT section`
