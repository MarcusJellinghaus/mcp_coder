# Step 5 — Verify: MCP edit smoke test in `.scratch/` with gitignore pre-check

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md`.
> Use TDD: update and add tests in `tests/cli/commands/test_verify_mcp_edit_smoke.py` first, then change the shim, `verify.py`, `tach.toml` and `.gitignore`.
> Never delete `.scratch/` recursively.
> Run pylint, pytest (fast unit set, `-n auto`), mypy, lint-imports and tach. All must pass.
> Run the formatter, then make exactly one commit.

## Precondition

`mcp_workspace.file_tools.directory_utils.is_path_gitignored` must exist with signature `(path: str, project_dir: Path) -> bool`. Check with `mcp__mcp-tools-py__get_library_source`.

If it is missing or has a different signature, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/mcp_workspace.py` — re-export
- `src/mcp_coder/cli/commands/verify.py` — `_run_mcp_edit_smoke_test`
- `tach.toml` — add `{ path = "mcp_coder.mcp_workspace" }` to `mcp_coder.cli` `depends_on`, with a short comment like the neighbours
- `.gitignore` — delete the line `.mcp_coder_verify.md`
- `tests/cli/commands/test_verify_mcp_edit_smoke.py`

## WHAT

- Shim:
  - change the import to `from mcp_workspace.file_tools.directory_utils import is_path_gitignored, list_files as _list_files`;
  - add `__all__ = ["is_path_gitignored", "list_files"]` so the re-export is explicit for linters;
  - update the module docstring ("file listing and gitignore utilities").
- `verify.py`:
  - add `from ...mcp_workspace import is_path_gitignored` as a module global, so tests can patch `mcp_coder.cli.commands.verify.is_path_gitignored`;
  - add the module constant `_SMOKE_TEST_FILE = ".scratch/mcp_coder_verify.md"` (POSIX on all platforms);
  - the signature of `_run_mcp_edit_smoke_test` is unchanged.

## ALGORITHM

```
if is_path_gitignored(_SMOKE_TEST_FILE, project_dir):      # before anything is created
    return _format_row(label, warning, f"skipped: {_SMOKE_TEST_FILE} is gitignored", indent=2)
scratch_dir = project_dir / ".scratch"; test_file = project_dir / _SMOKE_TEST_FILE
created_scratch = not scratch_dir.exists()
try: scratch_dir.mkdir(exist_ok=True); write_lf_text(test_file, "A\n\nC\n")
     prompt_llm(f"Edit the file {_SMOKE_TEST_FILE} to insert ...", ...); <existing A<B<C check>
except Exception: <existing warning row>
finally: test_file.unlink(missing_ok=True)
         if created_scratch: with contextlib.suppress(OSError): scratch_dir.rmdir()   # non-empty -> kept
```

- The prompt text stays the same apart from the path: `"Edit the file .scratch/mcp_coder_verify.md to insert a line 'B' between 'A' and 'C'"`.
- A leftover file from an earlier hard kill is simply overwritten and then deleted.

## DATA

The function still returns one formatted row string. The new possible value is `[WARN] skipped: .scratch/mcp_coder_verify.md is gitignored`.

## Tests (`tests/cli/commands/test_verify_mcp_edit_smoke.py`)

- Replace both `tmp_path / ".mcp_coder_verify.md"` uses with `tmp_path / ".scratch" / "mcp_coder_verify.md"`. The `prompt_llm` side effects that write `B` must write to the new path.
- Assert that the prompt (first positional argument of the `prompt_llm` mock) contains `.scratch/mcp_coder_verify.md` with forward slashes.
- `.scratch/` already exists with `other.txt` → after the run, `other.txt` and `.scratch/` still exist and the test file is gone.
- No `.scratch/` before the run → after the run `.scratch/` does not exist.
- No `.scratch/` before the run, and the `prompt_llm` side effect creates `.scratch/agent.txt` and writes `B` → after the run `.scratch/agent.txt` survives, the test file is gone, and the row says `edit verified`.
- Gitignored case:
  - write `tmp_path / ".gitignore"` containing `.scratch/`;
  - use the real `is_path_gitignored`, not a patch;
  - expect the row to contain `skipped: .scratch/mcp_coder_verify.md is gitignored`, `prompt_llm` not called, and `not (tmp_path / ".scratch").exists()`.
- The existing execute_verify-level tests in this file must keep passing. If one runs with a `project_dir` whose `.gitignore` ignores `.scratch`, patch `mcp_coder.cli.commands.verify.is_path_gitignored` to return `False` there.
