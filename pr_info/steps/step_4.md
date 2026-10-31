# Step 4 — Launch-time writers for untrusted sessions

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md`.
> Write the tests first, then the code. Run pylint, mypy and the fast pytest set (`-n auto`), and check the file size of
> `workspace.py` (it must stay within the CI limit). Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/workspace.py` — `create_startup_script`, `create_status_file`
- `tests/workflows/vscodeclaude/test_workspace_untrusted.py` — **new**

`create_workspace_file` is **not** changed. The caller (step 5) passes a blank `issue_title`.

## WHAT

```python
def create_startup_script(..., skip_github_install: bool = False,
                          untrusted_body: bool = False) -> Path
def create_status_file(..., is_intervention: bool,
                       untrusted_body: bool = False) -> None
```

The existing `issue_title` parameter now carries the **display title**: the caller passes `""` for untrusted sessions.
Update both docstrings to say so.

## HOW

- `create_startup_script`: pass `untrusted_body=untrusted_body` into `SessionSpec(...)`. Nothing else changes.
  The spec `title` is whatever the caller passed (blank when untrusted).
- `create_status_file`: choose `UNTRUSTED_STATUS_FILE_TEMPLATE` when `untrusted_body`, else `STATUS_FILE_TEMPLATE`.
  `.format(...)` uses keyword arguments; `str.format` ignores unused kwargs, so one call serves both templates.
  The "Last automated note" block (`_fetch_marked_comment`) is still appended; it contains trusted authors' text only.

## ALGORITHM

```
template = UNTRUSTED_STATUS_FILE_TEMPLATE if untrusted_body else STATUS_FILE_TEMPLATE
content = template.format(<existing kwargs>)
...append note, write (unchanged)...
```

## DATA

`.vscodeclaude_session.json`: `"title": ""`, `"untrusted_body": true` for untrusted sessions.

## Tests (`test_workspace_untrusted.py`)

Use the `mock_vscodeclaude_config` fixture, and patch `_fetch_marked_comment` where needed.

- `create_startup_script(..., issue_title="", untrusted_body=True)` → spec JSON has `title == ""` and
  `untrusted_body is True`. Default call → `untrusted_body is False`.
- `create_status_file(..., untrusted_body=True)` → contains `Issue #123` and the URL, no `Branch:`, no title text;
  the note block is still appended when `_fetch_marked_comment` returns text; with `is_intervention=True` the
  intervention line is present.
- `create_workspace_file(..., issue_title="")` → `window.title` still starts with `[#123 ` and ends with `- <repo>`,
  and still matches the window-detection pattern (import the pattern / matcher used by `detection.py`).
