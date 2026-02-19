# Step 2: Create `compact_diffs.py` core module + unit tests

## Goal

Implement the two-pass compact diff pipeline as a single, pure-function module.
All functions are small, independently unit-testable with synthetic data.
No I/O, no subprocess calls inside the module — those are delegated to
`get_branch_diff()`.

---

## WHERE

**Create:** `src/mcp_coder/utils/git_operations/compact_diffs.py`

**Create:** `tests/utils/git_operations/test_compact_diffs.py`

Do **not** modify `git_operations/__init__.py` — this module is internal.

---

## WHAT

### Data structures (module-level dataclasses)

```python
from dataclasses import dataclass, field

@dataclass
class Hunk:
    header: str                    # raw "@@ -a,b +c,d @@" line
    lines: list[str] = field(default_factory=list)

@dataclass
class FileDiff:
    headers: list[str] = field(default_factory=list)   # "diff --git ...", "index ...", etc.
    hunks: list[Hunk] = field(default_factory=list)
```

### Constants

```python
MIN_CONTENT_LENGTH: int = 10   # ignore short lines like "pass", "}" when matching moves
MIN_BLOCK_LINES: int = 3       # consecutive moved lines needed to emit a summary
```

### Functions — Layer 1: Parsing

```python
def parse_diff(text: str) -> list[FileDiff]:
    """Parse a plain unified diff string into FileDiff/Hunk objects."""
```

### Functions — Layer 2: ANSI detection (Pass 1)

```python
def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from a string."""

def is_moved_line(raw_line: str) -> bool:
    """True if the ANSI-coloured diff line is classified as moved by git.
    Looks for the 'dim' SGR attribute (code 2) in the ANSI codes.
    Only +/- lines can be moved; context lines and headers return False."""

def extract_moved_blocks_ansi(ansi_diff: str) -> set[str]:
    """Return the set of stripped line contents that git marked as moved
    (via --color-moved=dimmed-zebra). Uses is_moved_line() per line.
    Note: ANSI dim codes (\x1b[2m) are confirmed to work on Windows —
    no special environment setup is required."""
```

### Functions — Layer 3: Python cross-file matching (Pass 2)

```python
def is_significant_line(content: str) -> bool:
    """True if stripped content length >= MIN_CONTENT_LENGTH."""

def collect_line_occurrences(files: list[FileDiff]) -> tuple[set[str], set[str]]:
    """Return (removed_lines, added_lines) sets of significant stripped content."""

def find_moved_lines(files: list[FileDiff]) -> set[str]:
    """Return intersection of removed and added significant lines = moved."""
```

### Functions — Layer 4: Block analysis

```python
def format_moved_summary(count: int) -> str:
    """Return '# [moved: N lines not shown]' comment string."""
```

### Functions — Layer 5: Rendering

```python
def render_hunk(hunk: Hunk, moved_lines: set[str]) -> str:
    """Render a single hunk, replacing moved blocks >= MIN_BLOCK_LINES
    with a format_moved_summary() comment."""

def render_file_diff(file_diff: FileDiff, moved_lines: set[str]) -> str:
    """Render all hunks for one file; skip file entirely if all hunks are empty
    after moved-block suppression."""

def render_compact_diff(plain_diff: str, ansi_diff: str) -> str:
    """Top-level entry point.
    Combine Pass 1 (ANSI) and Pass 2 (Python) moved-line sets, then render."""
```

### Public entry point

```python
def get_compact_diff(
    project_dir: Path,
    base_branch: str,
    exclude_paths: Optional[list[str]] = None,
) -> str:
    """Obtain a compact diff by running get_branch_diff() twice and rendering.
    Returns compact diff string (may be empty if no changes)."""
```

---

## HOW

Integration:
- `get_compact_diff()` calls `get_branch_diff(ansi=False)` for Pass 2 parsing
  and `get_branch_diff(ansi=True)` for Pass 1 ANSI detection
- `render_compact_diff()` merges both moved-line sets (union) before rendering
- No imports outside stdlib + the project's own `get_branch_diff`

---

## ALGORITHM

### `render_hunk()` core logic
```
output = [hunk.header]
i = 0
while i < len(hunk.lines):
    if line is context (starts with ' '): append as-is; i++; continue
    gather consecutive lines with same sign (+/-) into block
    count significant moved lines in block
    if block >= MIN_BLOCK_LINES AND ALL significant lines are moved:
        append format_moved_summary(len(block))
    else:
        append block lines as-is
    i += len(block)
return joined output (or "" if only the header remains)
```

### `render_compact_diff()` core logic
```
plain_files = parse_diff(plain_diff)
ansi_moved  = extract_moved_blocks_ansi(ansi_diff)  # Pass 1
py_moved    = find_moved_lines(plain_files)          # Pass 2
all_moved   = ansi_moved | py_moved
output = []
for each file_diff in plain_files:
    rendered = render_file_diff(file_diff, all_moved)
    if rendered: output.append(rendered)
return "\n".join(output)
```

---

## DATA

`get_compact_diff()` returns `str`:
- Compact unified diff with moved blocks replaced by `# [moved: N lines not shown]`
- Empty string if `get_branch_diff()` returns empty (no diff / error)

---

## TESTS (`test_compact_diffs.py`)

All tests use **synthetic string inputs only** — no git repos, no fixture files.

```python
class TestParseHunkHeader:             # parse "@@ -1,5 +1,3 @@" correctly
class TestParseDiff:                   # parse a 2-file synthetic diff into FileDiff list
class TestStripAnsi:                   # strip ANSI codes from string
class TestIsMovedLine:                 # context/header lines → False; dim-coded +/- → True
class TestExtractMovedBlocksAnsi:      # set of moved line contents from ANSI diff
class TestIsSignificantLine:           # short lines False, long lines True
class TestCollectLineOccurrences:      # correct removed/added sets from FileDiff list
class TestFindMovedLines:              # intersection of removed+added
class TestFormatMovedSummary:          # "# [moved: 5 lines not shown]"
class TestRenderHunk:                  # moved blocks suppressed; small blocks kept
class TestRenderFileDiff:              # file skipped when all hunks empty
class TestRenderCompactDiff:           # end-to-end: 10-line synthetic diff → compact output
                                       # + test_render_compact_diff_empty_input: render_compact_diff("", "") == ""
```

Each test class has 1–3 focused test methods. No `@pytest.mark.git_integration`
(pure unit tests, no git repo required).

---

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement Step 2 exactly as specified.

Files to create:
  src/mcp_coder/utils/git_operations/compact_diffs.py
  tests/utils/git_operations/test_compact_diffs.py

Implementation rules:
1. Use the exact function signatures and dataclass definitions from step_2.md.
   Note: find_first_nonblank_line() is NOT in the spec — do not implement it.
2. All functions must be pure (no side effects) except get_compact_diff(),
   which calls get_branch_diff() from diffs.py.
3. render_hunk() suppresses a block when block >= MIN_BLOCK_LINES AND ALL
   significant lines in the block are moved (100% threshold, not 80%).
4. Windows compatibility: no LC_ALL env var usage anywhere in this file.
5. Do not add this module to git_operations/__init__.py — it is internal.
6. Follow the existing code style in diffs.py (type hints, logging, docstrings).

Test rules:
1. All tests use synthetic string inputs — no git repos, no fixtures.
2. Organize into the test classes listed in step_2.md.
   Note: TestFindFirstNonblankLine is NOT in the list — do not create it.
3. Each test class has 1–3 focused test methods.
4. TestRenderCompactDiff must include test_render_compact_diff_empty_input
   asserting that render_compact_diff("", "") returns "".
5. No @pytest.mark.git_integration marker needed.

Run the tests after implementing to verify they all pass.
```
