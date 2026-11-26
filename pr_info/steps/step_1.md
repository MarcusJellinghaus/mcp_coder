# Step 1 — Shim `mcp_coder.utils.fs` + import-linter, CLAUDE.md, architecture doc

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly. TDD: write the test first, then the shim. Make only the changes listed here. Run `run_format_code`, then pylint, pytest (`-n auto`, unit markers from CLAUDE.md), mypy, ruff, lint-imports, tach and vulture via the MCP tools. All must pass. This step is one commit.

## Precondition

The installed `mcp_coder_utils.fs` must export `write_text`, `dominant_newline` and `check_path_within`. Check with `get_library_source("mcp_coder_utils.fs")`. If any of them is missing, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- new `src/mcp_coder/utils/fs.py`
- new `tests/utils/test_fs_shim.py`
- `.importlinter`
- `.claude/CLAUDE.md`
- `docs/architecture/architecture.md`

## WHAT

### Test first — `tests/utils/test_fs_shim.py`

```python
"""The fs shim re-exports exactly the shared line-ending and containment helpers."""

from mcp_coder.utils import fs


def test_fs_shim_exports_only_the_shared_helpers() -> None:
    # read_file / normalize_path are not re-exported: their names clash with
    # local functions of different meaning.
    assert sorted(fs.__all__) == ["check_path_within", "dominant_newline", "write_text"]
```

### Shim — `src/mcp_coder/utils/fs.py`

Written like `utils/user_app_data.py`:

```python
"""Line-ending and path-containment shim — re-exports from mcp_coder_utils."""

from mcp_coder_utils.fs import check_path_within, dominant_newline, write_text

__all__ = ["check_path_within", "dominant_newline", "write_text"]
```

## HOW

- `.importlinter`, contract `mcp_coder_utils_isolation`:
  - add `mcp_coder.utils.fs -> mcp_coder_utils` to `ignore_imports`.
  - change the comment "should only be imported by the 3 shim files." to "should only be imported by the shim files listed in ignore_imports." (no count).
- `.claude/CLAUDE.md`, section "Shared Libraries":
  - Intro sentence → `This repo uses `mcp-coder-utils` for subprocess execution, logging, redaction, the toolkit contract, the user app data directory, and line endings / path containment. Shim modules in `src/mcp_coder/utils/` re-export the upstream API:`
  - Add three rows to the table:
    - `| `mcp_coder.utils.toolkit` | `mcp_coder_utils.toolkit` | `Toolkit`, `ToolkitInfo`, `ActionRequest`, `ActionResult`, `Finding`, `VerifyItem`, `validate_params` |`
    - `| `mcp_coder.utils.user_app_data` | `mcp_coder_utils.user_app_data` | `get_user_app_data_dir` |`
    - `| `mcp_coder.utils.fs` | `mcp_coder_utils.fs` | `write_text`, `dominant_newline`, `check_path_within` |`
- `docs/architecture/architecture.md` line 27: change "Shared subprocess, logging and redaction helpers and the toolkit contract come from `mcp-coder-utils`." to "Shared subprocess, logging and redaction helpers, line-ending and path-containment helpers, and the toolkit contract come from `mcp-coder-utils`." Leave the rest of the line unchanged.

## ALGORITHM

None (re-export only).

## DATA

`fs.__all__ == ["check_path_within", "dominant_newline", "write_text"]`

## Commit message

`feat(utils): add fs shim for mcp-coder-utils line endings and containment`
