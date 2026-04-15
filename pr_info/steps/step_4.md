# Step 4: Delete `testdata/` Folder

> **Context:** Read `pr_info/steps/summary.md` first. This is the cleanup step.

## Goal
Delete the entire `testdata/` folder. The JSON test data has served its purpose as visual acceptance tests during design. The rendering expectations are now encoded in unit tests in `test_stream_renderer.py`. The rendering scripts (`render_testdata.py`, `render_nice.py`) are development tools that are no longer needed.

## WHERE

| Path | Action |
|------|--------|
| `testdata/` | Delete entire folder |

## WHAT — Files being deleted

### Rendering scripts (2 files)
- `testdata/render_testdata.py` — feeds JSON through current renderer
- `testdata/render_nice.py` — reference implementation / target renderer

### Design document (1 file)
- `testdata/design.md` — design notes (superseded by issue #820)

### Non-tool test data (3 files)
- `testdata/conversation_simple_edit.json`
- `testdata/msg_result_final.json`
- `testdata/msg_system_init.json`
- `testdata/response_text_only.json`

### Tool JSON inputs (14 files)
- `testdata/tool_edit_file.json`
- `testdata/tool_edit_file_large.json`
- `testdata/tool_edit_file_multi.json`
- `testdata/tool_list_directory.json`
- `testdata/tool_list_symbols.json`
- `testdata/tool_permission_denied.json`
- `testdata/tool_read_file.json`
- `testdata/tool_read_file_large.json`
- `testdata/tool_run_mypy.json`
- `testdata/tool_run_pylint.json`
- `testdata/tool_run_pytest.json`
- `testdata/tool_save_file.json`
- `testdata/tool_save_file_error.json`
- `testdata/tool_search_files.json`

### Rendered outputs (42 files: 14 × 3 variants each)
- `*_raw.txt` — current rendering output
- `*_nice_compact.txt` — target compact rendering
- `*_nice_full.txt` — target full rendering

## HOW

Check whether any production code imports from `testdata/`. If none (expected), delete the entire folder.

Verify that tests still pass after deletion — no test should depend on testdata files.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Implement Step 4: Delete the entire testdata/ folder.
First verify no production code or test imports reference testdata/.
Then delete all files and the folder itself.

After deletion, run all three code quality checks to confirm nothing breaks.
```
