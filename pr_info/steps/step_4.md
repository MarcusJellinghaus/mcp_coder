# Step 4 — `update_gitignore` writes via `write_repo_text`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md` exactly. TDD: update and add the tests first, then change `update_gitignore`. Run `run_format_code`, then pylint, pytest (`-n auto`, unit markers from CLAUDE.md), mypy, ruff, lint-imports, tach and vulture via the MCP tools. All must pass. This step is one commit.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/workspace.py` (`update_gitignore`)
- `tests/workflows/vscodeclaude/test_workspace.py`: 680 lines, close to the 750-line limit, so **do not add a new test function**; parametrize the existing one.
- `tests/cli/commands/test_init_gitignore.py`

## WHAT

### Tests first — `tests/workflows/vscodeclaude/test_workspace.py`

Replace `test_update_gitignore_preserves_existing_line_endings` with a parametrized version:

```python
@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_update_gitignore_preserves_existing_line_endings(
    self, tmp_path: Path, newline: bytes
) -> None:
    """Existing bytes are untouched and the appended block uses the file's ending."""
    gitignore = tmp_path / ".gitignore"
    seed = b"*.pyc" + newline
    gitignore.write_bytes(seed)

    update_gitignore(tmp_path)

    raw = gitignore.read_bytes()
    assert raw.startswith(seed)
    assert raw.endswith(newline)
    # Only the seed's ending remains as a line break - no mixed file.
    rest = raw.replace(newline, b"")
    assert b"\r" not in rest and b"\n" not in rest
```

### Tests first — `tests/cli/commands/test_init_gitignore.py`

Add one test to `TestExecuteInitGitignore`. Follow the setup of `test_gitignore_block_written_and_second_run_is_noop`: patch `get_config_file_path` / `create_default_config`, `_make_source`, monkeypatch `_find_claude_source_dir`, `just_skills=False`.

```python
def test_crlf_gitignore_stays_crlf(...) -> None:
    """Both .gitignore writers of init follow a CRLF file's ending."""
    gitignore = project / ".gitignore"
    gitignore.write_bytes(b"*.pyc\r\n")

    assert execute_init(args) == 0

    raw = gitignore.read_bytes()
    assert b".vscodeclaude_session.json" in raw   # update_gitignore ran
    assert b".scratch/" in raw                    # ensure_scratch_gitignored ran
    assert b"\n" not in raw.replace(b"\r\n", b"")  # no lone LF
```

### Implementation — `update_gitignore`

Replace

```python
    # newline="" disables text-mode translation: the literal "\n" above is what
    # reaches the file, so a LF .gitignore stays LF on Windows.
    with gitignore_path.open("a", encoding="utf-8", newline="") as f:
        f.write(addition)
```

with

```python
    write_repo_text(gitignore_path, addition, append=True)
```

- `write_repo_text` is already imported in this module (`from ...utils.text_io import write_repo_text`).
- Keep the logic that prepends `"\n"`. The universal-newline `read_text` keeps the `endswith("\n")` check correct for CRLF files.
- The docstring has no text about keeping an LF file LF; remove any such text that remains.

## HOW

- `execute_init` appends to the same `.gitignore` twice: first `update_gitignore`, then `ensure_scratch_gitignored`, which already uses `write_repo_text` since step 3. After this step both writers follow one rule.
- Do **not** touch `create_startup_script` (`.bat`, text mode) or the `tasks.json` write.

## ALGORITHM

```
addition = missing entries (+ "\n" prefixes as before; LF in memory)
write_repo_text(.gitignore, addition, append=True)   # converted to the file's dominant ending
```

## DATA

Unchanged: returns `list[str]`, the pattern lines that were appended.

## Commit message

`fix(vscodeclaude): append to .gitignore in its dominant line ending`
