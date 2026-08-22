# Step 1 — `update_gitignore`: return value + foreign-file safety

**Depends on:** nothing. **Blocks:** step 2.

Prepare `update_gitignore` for its new caller. `mcp-coder init` is the first
caller that runs against repos we do not control, so the function must report
what it appended and must behave correctly on `.gitignore` files it did not
write. No caller changes in this step — `session_launch.py` keeps calling it and
ignoring the result.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | Modify `update_gitignore` (currently at line ~367) |
| `tests/workflows/vscodeclaude/test_workspace.py` | 3 new tests; 2 existing tests gain a return-value assertion |

Do **not** modify `templates.py`, `session_launch.py`, or
`workflows/vscodeclaude/__init__.py` (the `update_gitignore` re-export there
needs no change).

## WHAT

```python
def update_gitignore(folder_path: Path) -> list[str]:
```

Signature changes from `-> None` to `-> list[str]`.

## DATA

Returns the pattern lines appended, in `GITIGNORE_ENTRY` order. Empty list when
the file was already up to date. Comment lines are never part of the return
value — only pattern lines, matching the existing `missing` computation.

Examples:

| Situation | Return |
|-----------|--------|
| No `.gitignore` yet | all 5 `.vscodeclaude_*` lines |
| Old 4-entry block committed | `[".vscodeclaude_session.json"]` |
| Fully up to date | `[]` |

## HOW

Four edits inside the existing function body — no restructuring, no new helper.

1. `return` → `return []` at the `if not missing:` early exit.
2. Replace the `if / else` that builds `addition` and add one guard after it.
3. Add `newline=""` to the `open("a", ...)` call.
4. `return missing` after the `with` block writes.

Keep the local `from .templates import GITIGNORE_ENTRY` and the append-only
write. Append-only is deliberate: a read-modify-write would translate every line
ending in the file on Windows and produce a whole-file diff.

The open call gains `newline=""`:
`gitignore_path.open("a", encoding="utf-8", newline="")`. Without it, Python's
text-mode translation turns every written `\n` into `\r\n` on Windows — the new
block would land CRLF inside an otherwise-LF `.gitignore`, and the
missing-trailing-newline guard would re-terminate the last *existing* line as
CRLF. `newline=""` writes the literal `\n` we build, on every platform, so line
endings elsewhere in the file never change.

## ALGORITHM

Only the block from `if not missing:` onward changes:

```
if not missing:                    -> return []
if marker line already present:     addition = "\n".join(missing) + "\n"
else:                               addition = GITIGNORE_ENTRY.lstrip("\n")
                                    if existing_content: addition = "\n" + addition
if existing_content and not existing_content.endswith("\n"):
                                    addition = "\n" + addition
append addition; return missing
```

`lstrip("\n")` is what makes a from-scratch file start at
`# VSCodeClaude session files (auto-generated)` instead of a blank line; the
blank separator is re-added only when there is existing content to separate
from. The final guard is what stops entries being glued onto a last line that
lacks its newline. Both branches of `addition` end with `"\n"`, so the file
always ends with a newline.

Resulting code:

```python
    if not missing:
        return []

    # Fresh repo (no marker yet): write the full block for a clean comment
    # header. Otherwise append just the missing pattern lines.
    if ".vscodeclaude_status.txt" in existing_lines:
        addition = "\n".join(missing) + "\n"
    else:
        addition = GITIGNORE_ENTRY.lstrip("\n")
        if existing_content:
            addition = "\n" + addition  # blank line before the new block

    # Never glue onto a last line that lacks its newline.
    if existing_content and not existing_content.endswith("\n"):
        addition = "\n" + addition

    # newline="" disables text-mode translation: the literal "\n" above is what
    # reaches the file, so a LF .gitignore stays LF on Windows.
    with gitignore_path.open("a", encoding="utf-8", newline="") as f:
        f.write(addition)

    return missing
```

Docstring gains a `Returns:` section and a one-line note that the function is
append-only by design.

## Tests (write first)

In `tests/workflows/vscodeclaude/test_workspace.py`, same class as the existing
`test_update_gitignore_*` tests.

**New — fresh file:**

```python
def test_update_gitignore_fresh_file_starts_with_header(self, tmp_path: Path) -> None:
    """A .gitignore created from scratch starts at the comment header."""
    added = update_gitignore(tmp_path)

    content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert content.startswith("# VSCodeClaude session files (auto-generated)\n")
    assert content.endswith("\n")
    assert added == [
        ".vscodeclaude_status.txt",
        ".vscodeclaude_analysis.json",
        ".vscodeclaude_session.json",
        ".vscodeclaude_start.bat",
        ".vscodeclaude_start.sh",
    ]
```

**New — existing file with no trailing newline:**

```python
def test_update_gitignore_no_trailing_newline(self, tmp_path: Path) -> None:
    """Entries never get glued onto a last line that lacks its newline."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc", encoding="utf-8")  # no trailing newline

    update_gitignore(tmp_path)

    content = gitignore.read_text(encoding="utf-8")
    assert content.splitlines()[0] == "*.pyc"
    assert "# VSCodeClaude session files (auto-generated)" in content.splitlines()
    assert content.endswith("\n")
```

**New — existing line endings are preserved (byte level):**

This is the test for the issue's "content already in the file is never
rewritten / line endings elsewhere must not change" requirement. It must use
`read_bytes()`: `read_text()` applies universal-newline translation and would
turn a `\r\n` back into `\n`, masking exactly the behaviour under test.

```python
def test_update_gitignore_preserves_existing_line_endings(self, tmp_path: Path) -> None:
    """Existing bytes are untouched and the appended block uses LF."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_bytes(b"*.pyc\n")  # LF file, trailing newline present

    update_gitignore(tmp_path)

    raw = gitignore.read_bytes()
    assert raw.startswith(b"*.pyc\n")  # existing bytes unchanged, still LF
    assert b"\r\n" not in raw  # appended block uses LF too, also on Windows
    assert raw.endswith(b"\n")
```

**Amend `test_update_gitignore_appends_missing_entry_on_upgrade`** — capture the
call and add `assert added == [".vscodeclaude_session.json"]`.

**Amend `test_update_gitignore_up_to_date_unchanged`** — capture the second call
and add `assert added == []` alongside the existing byte-equality assertion.

The existing `test_update_gitignore_adds_entry`, `..._creates_file`, and
`..._idempotent` tests stay as they are and must keep passing.

## Checks

Run all three MCP checks; all must pass before commit.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.
>
> Implement step 1 only: give
> `src/mcp_coder/workflows/vscodeclaude/workspace.py::update_gitignore` a
> `list[str]` return value, the two newline guards, and the `newline=""` open
> flag described in the step, following TDD — write the three new tests and the
> two test amendments in `tests/workflows/vscodeclaude/test_workspace.py` first,
> watch them fail, then change the function.
>
> Keep the change minimal: no restructuring of the function, no new helpers, and
> keep the append-only `open("a", ..., newline="")` write. Do not touch `templates.py`,
> `session_launch.py`, `workflows/vscodeclaude/__init__.py`, or the init command
> — those come in step 2.
>
> Use MCP tools for all file operations. After the change run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and
> `mcp__tools-py__run_pytest_check` with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`.
> Fix any issue before finishing. This step is one commit.
