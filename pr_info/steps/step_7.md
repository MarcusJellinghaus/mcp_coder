# Step 7 — Exact title / cmdline matching (negative boundary rules)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_7.md`), then implement Step 7 only. Replace the substring matches in `_title_binds` and `_cmdline_scan` with negative-boundary regex matches, through one shared helper. Use the real title and command-line strings below verbatim as test fixtures. Write the tests first, then the implementation. Run the checks from the summary, then make one commit.

## Rationale

Substring matches let one session's window or folder keep another alive (`[#1342` binds #134; `mcp_coder_utils` binds `mcp_coder`; `mcp_coder_1342` matches `mcp_coder_134`). A match is rejected only when the name visibly continues, so unknown formats fail toward "active".

## WHERE / WHAT (`src/mcp_coder/workflows/vscodeclaude/detection.py`)

```python
import re

_NAME_CHAR = "a-z0-9_-"

def _contains_bounded(haystack: str, needle: str) -> bool:
    """Whether ``needle`` occurs in ``haystack`` not preceded/followed by a name char.

    Both arguments must already be lowercased. Any occurrence counts.
    """
    pattern = rf"(?<![{_NAME_CHAR}]){re.escape(needle)}(?![{_NAME_CHAR}])"
    return re.search(pattern, haystack) is not None
```

**`_title_binds`**
```python
issue_re = re.compile(re.escape(f"[#{issue_number}") + r"(?!\d)")
for _pid, title in snapshot.window_titles:
    if issue_re.search(title) and _contains_bounded(title.lower(), repo_name):
        return True
```
Docstring: the workspace title format is `[#N stage] title - repo_name`, and the repo name ends the string (there is no ` - Visual Studio Code` suffix). Describe the two boundary rules.

**`_cmdline_scan`**
- Replace `folder_str in cmdline_lower or folder_name in cmdline_lower` with `_contains_bounded(cmdline_lower, folder_str) or _contains_bounded(cmdline_lower, folder_name)`.

Comparisons stay lowercased as today. `re.escape` handles `.`, `-` and `\` in repo names and paths.

## Fixtures (verbatim)

Window titles:
```
[#1407 new] vscodeclaude: stale VSCode mai... - mcp_coder
[#1394 new] docs: fine-grained PAT list in... - mcp_coder
[#283 new] Configure the mcp-coder toolki... - mcp-tools-py
[#60 new] Truncation logic - mcp-tools-py
```

Main-process command line:
```
"C:\Users\Marcus\AppData\Local\Programs\Microsoft VS Code\Code.exe" C:\Users\Marcus\Documents\VSCC\mcp_coder_1342.code-workspace C:\Users\Marcus\Documents\VSCC\mcp_coder_1342\.vscodeclaude_status.txt
```
Store it lowercased in the fake snapshot's `cmdline_lower`, as `_get_vscode_processes` does.

## Tests (write first)

**`test_detection.py`**, parametrized. Pin `HAS_WIN32GUI=True` for title tests.

Title (`_title_binds`):

| title | issue | repo | binds |
|---|---|---|---|
| `[#1342 new] x - mcp_coder` | 134 | `o/mcp_coder` | no |
| `[#134 impl] x - mcp_coder` | 134 | `o/mcp_coder` | yes |
| `[#134] x - mcp_coder` | 134 | `o/mcp_coder` | yes |
| real `#1407` title | 1407 | `o/mcp_coder` | yes |
| `[#5 new] x - mcp_coder_utils` | 5 | `o/mcp_coder` | no |
| `[#5 new] fix mcp_coder_utils import - mcp_coder` | 5 | `o/mcp_coder` | yes |
| real `#60` title | 60 | `o/mcp-tools-py` | yes |
| real `#60` title | 60 | `o/mcp-tools` | no |

Cmdline (`_cmdline_scan`):
- Make the folder-name and full-path checks independent of host path semantics: pass `folder_path` with forward slashes (e.g. `"c:/x/mcp_coder_134"`, whose `Path(...).name` is the same on Linux and Windows).
- The full-path branch is tested separately with a forward-slash path that appears verbatim in a fake cmdline.

| cmdline | folder name | matches |
|---|---|---|
| real #1342 cmdline | `mcp_coder_134` | no |
| `… mcp_coder_1342-folder2 …` | `mcp_coder_134` | no |
| `… mcp_coder_1342-folder2 …` | `mcp_coder_1342` | no |
| real #1342 cmdline (`.code-workspace` form) | `mcp_coder_1342` | yes |
| real #1342 cmdline (`\mcp_coder_1342\` form, workspace arg removed) | `mcp_coder_1342` | yes |
| `"c:/x/mcp_coder_1342"` quoted / end of string | `mcp_coder_1342` | yes |

Unit tests for `_contains_bounded`: start/end of string, quotes, spaces, `.`, `\` and `/` neighbours are accepted; `_`, `-`, letters and digits are rejected.

## Commit

`fix(vscodeclaude): match window titles and cmdlines on name boundaries`
