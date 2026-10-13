# Summary: Surface automated failure/handoff comments in `.vscodeclaude_status.txt`

Issue: #1184

## Problem

When an automated workflow (review round-limit/escalate handoff, or a hard
failure in `review`, `implement`, `create_pr`, `create_plan`) hands off to a
human, it posts a plain-text explanation as a GitHub issue comment, but
nothing surfaces that comment where the developer actually looks next:
`.vscodeclaude_status.txt`, opened automatically when they launch a
VSCode+Claude session for the issue. Today they have to go read GitHub
manually.

## Design

Two independent pieces, in this order:

1. **A consistent marker.** Every automated failure/handoff comment gets a
   `❌` somewhere on its first line. Six posting call sites exist across four
   workflows; two already carry a `❌` (no change), four need one added. The
   marker goes *inside* a markdown heading where one exists
   (`## ❌ Implementation Failed`), never prefixed before it — prefixing
   would stop GitHub from rendering the line as a heading. This is the only
   change to what gets posted to GitHub; no new comment format, no new
   labels.

2. **A status-file scan at session-launch time.** `create_status_file` (the
   function that writes `.vscodeclaude_status.txt`) fetches the issue's last
   3 comments, scans from most recent backwards for the first whose first
   line contains `❌`, and — only when one is found — appends its full text
   to the status file as a new block after the existing banner. The banner
   itself is untouched. A fetch failure (network, auth, rate limit) is
   swallowed with a logged warning; the status file then looks exactly like
   it does today, and session launch is never blocked by this.

The scan logic (which comment, if any, is "the" automated note) is kept as
one pure function taking a plain list of comment dicts, so the error-prone
part — scanning a bounded window in reverse order against an oldest-first
list — is unit-tested without mocking any GitHub client. The network call
and failure-swallowing live in a thin wrapper around it.

## Architectural / design changes

- No new abstractions, modules, or configuration. This is a formatting
  change to six existing comment-building call sites, plus one new
  best-effort read (`IssueManager.get_comments`) added to an existing
  write-only function (`create_status_file`), which was previously pure
  (no network I/O). That function now does one bounded, swallowed network
  call.
- The parse rule ("first line contains `❌`") is deliberately loose, not
  `startswith`, because the marker sits inside a markdown heading for three
  of the six sites and at the very start for the other three. One rule
  covers both.
- `_route_to_human` (the round-limit/escalate handoff) is not technically a
  failure — it returns `0` and applies no failure label — but reuses `❌`
  anyway rather than inventing a second marker. Accepted, known semantic
  looseness, traded for one simple parse rule across all six sites.
- `/check_branch_status` surfacing the same note is explicitly out of
  scope — that lives in the separate mcp-workspace repo
  ([mcp-workspace#309](https://github.com/MarcusJellinghaus/mcp-workspace/issues/309)).

## Folders / modules / files touched

**Modified:**
- `src/mcp_coder/workflows/review/handoff.py` — `_route_to_human` marks its comment.
- `src/mcp_coder/workflows/implement/failure_reporting.py` — `format_failure_comment` heading.
- `src/mcp_coder/workflows/create_pr/helpers.py` — `format_failure_comment` heading.
- `src/mcp_coder/workflows/create_plan/core.py` — `_format_failure_comment` heading, and the `run_guarded` crash-net `comment_header`.
- `src/mcp_coder/workflows/create_pr/core.py` — the `run_guarded` crash-net `comment_header`.
- `src/mcp_coder/workflows/vscodeclaude/templates.py` — new status-file note block template.
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` — new pure scan helper, new fetch wrapper, `create_status_file` wiring.
- `tests/workflows/review/test_handoff_route.py`
- `tests/workflows/implement/test_failure_reporting.py`
- `tests/workflows/create_pr/test_failure_handling.py`
- `tests/workflows/create_plan/test_failure_handling.py`
- `tests/workflows/vscodeclaude/test_templates.py`
- `tests/workflows/vscodeclaude/test_workspace.py`

**Not touched (confirmed already correct or out of scope):**
- `workflows/review/handoff.py::_fail` — already prefixes `❌ `.
- `workflows/implement/core.py`, `workflows/review/core.py` — their `run_guarded` calls already pass a `build_comment` closure reusing the real (now-marked) formatter, or already bake `❌` into `comment_header`.
- `workflows/vscodeclaude/session_launch.py` — calls `create_status_file` unchanged; no signature change.
- `plan_review_supervisor` / `implementation_review_supervisor` — already see full issue comments via `github_issue_view`.

## Steps

1. [step_1.md](./step_1.md) — Mark all six comment-posting sites with `❌`.
2. [step_2.md](./step_2.md) — Pure building blocks: scan-rule helper + status-file note template.
3. [step_3.md](./step_3.md) — Wire the comment fetch into `create_status_file`.
