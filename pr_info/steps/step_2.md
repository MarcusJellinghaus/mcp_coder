# Step 2 — Coordinator trust gate

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`
> only (step 1 is done: the shim exports `is_trusted_author`,
> `get_trusted_commenters`, `ReviewThreadData`). TDD: update/add the tests
> first, then the code. Run pylint, mypy and the fast unit tests (see
> CLAUDE.md) until they pass, run `run_format_code`, and make exactly one
> commit.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/checks.py`
  (`_check_review_comments`, `check_pr_health`)
- `tests/workflows/vscodeclaude/test_checks_review_comments.py`
- `tests/workflows/vscodeclaude/test_checks.py`

## WHAT

```python
def _check_review_comments(
    issue: IssueData,
    pr: PullRequestData,
    pr_manager: PullRequestManager,
    issue_manager: IssueManager,
    repo_name: str,
    review_label_name: str,
    created_label_name: str,
    trusted: frozenset[str],
) -> bool:
```

Same contract as today (never raises, returns True iff escalation attempted).
Update the docstring: only trusted authors' items escalate; untrusted items
produce at most one `OUTPUT` line.

`check_pr_health`: inside the existing setup `try`, add
`trusted = get_trusted_commenters()`; pass `trusted` as the last argument of
the `_check_review_comments` call. No other changes.

## HOW

- Extend the `...mcp_workspace_github` import in `checks.py` with
  `get_trusted_commenters`, `is_trusted_author`.
- Reuse `_escalate`, `_review_comments_watermark`, `is_marked` as-is.
- Keep the whole body inside the existing `try/except` and use early returns.
  Only extract a helper if pylint flags complexity.

## ALGORITHM

```
if not is_trusted_author(pr["user"], pr["author_association"], trusted):
    log OUTPUT "%s #%d: untrusted PR author @%s — review comments not checked"; return False
fb = get_pr_feedback(pr["number"]); ok = lambda login, assoc: is_trusted_author(login, assoc, trusted)
if any(ok(t["author"], t["author_association"]) for t in fb["unresolved_threads"]): escalate; return True
items = [(r author, assoc, submitted_at) for reviews] + [(c author, assoc, created_at) for unmarked comments]
watermark = _review_comments_watermark(get_issue_events(...), ...) if items else None
new = [i for i in items if ts is None or watermark is None or ts > watermark]
if any trusted in new: escalate; return True
logins = dict.fromkeys(untrusted thread authors + untrusted authors in new)
if logins: log OUTPUT "%s #%d: untrusted PR feedback from @a, @b — review manually"
return False
```

`OUTPUT` lines are prefixed with `repo_name` like the existing
`PR-health: ...` line, e.g.
`PR-health: <repo> #N: untrusted PR feedback from @a, @b — review manually`.

## DATA

- `trusted`: lowercased logins `frozenset[str]` from `get_trusted_commenters()`.
- `items`: `list[tuple[str, str | None, str | None]]` — `(login, association, timestamp)`.
- Return: `bool` (unchanged).

## Tests

### `test_checks_review_comments.py`

- `PR`: complete `PullRequestData` with `user="owner"`,
  `author_association="OWNER"` (replace `cast(PullRequestData, {"number": 1})`).
- Add `_thread(author="reviewer", association="MEMBER") -> ReviewThreadData`
  (complete dict); replace `{"body": "fix this"}` with `_thread()`.
- `_review` / `_comment` builders: add `author` and `association` keyword
  params (defaults `"reviewer"` / `"MEMBER"`).
- `_call(issue, pr_manager, issue_manager, trusted=frozenset(), pr=PR)` passes
  `trusted` (and allows an untrusted PR).
- Autouse fixture patching
  `mcp_coder.workflows.vscodeclaude.checks.get_trusted_commenters` →
  `frozenset()`.
- New tests (use `caplog` for `OUTPUT` lines; untrusted = association
  `"NONE"`):
  - untrusted thread only → `False`, `OUTPUT` line with `@login`,
    `get_issue_events` not called;
  - untrusted review only (new) → `False`, `OUTPUT` line;
  - untrusted comment only (new) → `False`, `OUTPUT` line;
  - trusted parametrized: OWNER, COLLABORATOR, allowlisted login
    (association `"NONE"`, `trusted=frozenset({"friend"})`) → `True`;
  - mixed trusted + untrusted → `True`, no "untrusted PR feedback" line;
  - missing association (`None`), login not allowlisted → untrusted;
  - untrusted PR author → `False`, `get_pr_feedback` not called, `OUTPUT`
    line;
  - `get_issue_events` called at most once with several reviews + comments;
  - untrusted review/comment older than watermark → no `OUTPUT` line;
  - untrusted thread plus an untrusted review/comment older than the
    watermark (events contain a status-91 → status-10 relabel, so
    `get_issue_events` is called and a watermark is set) → `False`,
    `OUTPUT` line still lists the thread author;
  - same untrusted login on thread + comment → listed once.

### `test_checks.py`

- `_make_pr` defaults: `user="owner"`, `author_association="OWNER"`.
- `_default_mocks`: `find_pull_request_by_head.return_value = [_make_pr()]`
  (replace the partial dict); update the tests that override it with partial
  dicts to `[_make_pr(mergeable_state=...)]`.
- `_patch_env`: patch `f"{CHECKS}.get_trusted_commenters"` with a `MagicMock`
  returning `frozenset()`; expose it so a test can assert calls.
- New: two status-10 issues in one `check_pr_health` call →
  `get_trusted_commenters` called exactly once.
