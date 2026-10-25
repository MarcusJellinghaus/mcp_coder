# Step 7 — Consistency test + HTML matrix rewrite

## LLM prompt

> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_7.md`).
> TDD:
> 1. Write `tests/docs/__init__.py` and `tests/docs/test_workflow_matrix.py` exactly as specified. Run them; they must **fail** against the current HTML (old `status:xxx` names, missing labels).
> 2. Hand-rewrite `docs/processes-prompts/github_Issue_Workflow_Matrix.html` until the tests pass. Reuse the existing CSS and markup patterns.
> Run pylint, mypy, pytest and the file-size check, then format, then commit as one commit.

## WHERE

```
tests/docs/__init__.py                                  (new, empty)
tests/docs/test_workflow_matrix.py                      (new)
docs/processes-prompts/github_Issue_Workflow_Matrix.html (rewrite)
```

## WHAT — test

```python
"""Consistency checks between labels.json and the HTML workflow matrix."""

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
LABELS_JSON = REPO_ROOT / "src" / "mcp_coder" / "config" / "labels.json"
MATRIX_HTML = REPO_ROOT / "docs" / "processes-prompts" / "github_Issue_Workflow_Matrix.html"
LABEL_NAME_RE = re.compile(r'class="label-name">([^<]+)<')


def _labels() -> list[dict[str, Any]]: ...
def _html() -> str: ...
def _cards() -> dict[str, str]: ...          # label name -> card HTML block

def test_every_label_has_a_card() -> None: ...
def test_every_card_label_exists_in_labels_json() -> None: ...
def test_vscodeclaude_commands_on_card() -> None: ...
```

## ALGORITHM

```
_labels: json.loads(LABELS_JSON.read_text(encoding="utf-8"))["workflow_labels"]
_cards: for block in _html().split('class="label-card')[1:]:
            m = LABEL_NAME_RE.search(block); if m: cards[m.group(1).strip()] = block
test 1: missing = {l["name"] for l in _labels()} - set(LABEL_NAME_RE.findall(html)); assert not missing
test 2: unknown = set(findall) - {names}; assert not unknown
test 3: for l with l.get("vscodeclaude", {}).get("commands"):
            for cmd in commands: assert cmd in _cards()[l["name"]], (l["name"], cmd)
```

- No pytest marker: it is a plain unit test.
- Splitting on `class="label-card` skips the CSS `.label-card {` rule. Cards do not nest, so each block holds exactly one card.
- Test 3 must fail clearly (`KeyError` → use `.get(name, "")`) when a card is missing.

## DATA

- `_cards()` returns `dict[str, str]`.
- Assertion messages name the offending labels or commands (sorted lists).

## WHAT — HTML rewrite

Keep `<style>`, header and column headers. Rows, in order, with four cells each (human / pickup / busy / failed):

| Row label (with workflow name) | Human | Pickup | Busy | Failed stack |
|---|---|---|---|---|
| Planning — `create-plan` | 01 | 02 | 03 | 03f, 03f-timeout, 03f-mcp, 03f-prereq |
| Implementation — `implement` | 04 | 05 | 06 | 06f, 06f-prep, 06f-ci, 06f-timeout, 06f-mcp, 06f-nochange, 06f-blocked |
| PR creation — `create-pr` | 07 | 08 | 09 | 09f, 09f-timeout, 09f-mcp |
| Complete (`workflow-row-final`) | 10 | empty | empty | empty |
| PR follow-up: merge conflict — `fix-conflict` | empty | 71 | 72 | 73, 74 |
| PR follow-up: failing CI — `fix-ci` | empty | 81 | 82 | 83, 84 |
| PR follow-up: review comments — `/pr_comment_triage` | 91 | empty | empty | empty |
| Automated plan review — `review-plan` (optional) | empty | 14 | 14i | 14f, 14f-timeout, 14f-mcp |
| Automated code review — `review-implementation` (optional) | empty | 17 | 17i | 17f, 17f-ci, 17f-timeout, 17f-mcp, 17f-tasks, 17f-ci-unknown |

This gives 46 cards with one `.label-name` each. Drop the `→4` / `→7` escalation cards.

Per card:
- `label-name` = the exact `labels.json` `name`.
- `label-description` = the `labels.json` `description`, unchanged.
- One new element when there is anything to show:

  ```html
  <div class="label-commands">
    <div>&#x25b6; Auto: <code>/issue_analyse</code> → <code>/discuss</code></div>
    <div>&#x270b; Manual / exit: <code>/issue_approve</code> → 02 …</div>
  </div>
  ```

  - **Auto line:** only for labels with `vscodeclaude.commands`, copied in order.
  - **Manual / exit line:**
    - 01: `/issue_analyse_supervisor` → 02, `/issue_update`, `/issue_approve` → 02.
    - 04: `/plan_review`, `/discuss`, `/plan_update`, `/plan_approve` → 05, `/issue_approve` → 05.
    - 07: `/implementation_review`, `/implementation_finalise`, `/implementation_new_tasks`, `/implementation_approve` → 08, `/implementation_needs_rework` → 05, `/issue_approve` → 08.
    - 91: exits via `/pr_comment_triage` → 10.
    - Each failure card: "fix → `set-status` <retry label>" (retry label from the owner doc).
    - 10: none.
    - Re-verify the target labels in each `SKILL.md`.
- **Transitions:** put success / failure exits as text in the row's description line under each `row-label`. For example `fix-conflict`: "72 → 10 settled/not dirty or unknown after successful rebase; → 74 dirty / no PR / unknown after failed rebase; → 73 crash; branch undetermined → exit 1, stays 72". Same for `fix-ci` and the review lanes. Write escalations there too ("escalate → 04" / "→ 07").

CSS additions:
- one `.label-commands { … }` rule (small font, top margin);
- `.status-<slug>` rules for the 14 new cards, where slug = `internal_id` with `_` → `-` and the colour comes from `labels.json`.

Color Reference: one swatch per distinct `labels.json` colour (16). Add `#fda4af` and `#fb7185`, and list the labels using each colour.

## Checks

- `run_pytest_check(extra_args=["-n", "auto", "tests/docs"])`: 3 tests pass. Then run the fast unit suite from CLAUDE.md.
- `run_pylint_check`, `run_mypy_check`.
- `check_file_size` (`max_lines=750`). If the HTML exceeds 750 lines, trim whitespace and comments first. If it still exceeds the limit, write one line to `pr_info/.blocked.txt` and stop.
- Format, then commit: `docs(matrix): rewrite workflow matrix to match labels.json and add consistency test`.
