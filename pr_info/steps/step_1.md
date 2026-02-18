# Step 1: Update `get_stale_sessions` to return a reason string

## LLM Prompt

```
See pr_info/steps/summary.md for full context.

Implement Step 1: update `get_stale_sessions` in
`src/mcp_coder/workflows/vscodeclaude/cleanup.py` to return a 3-tuple
`(session, git_status, reason)` instead of the current 2-tuple.

Do NOT yet modify `cleanup_stale_sessions` (that is Step 2).
Do NOT yet modify tests (that is Step 3).

Follow the spec in summary.md exactly.
```

---

## WHERE

**File:** `src/mcp_coder/workflows/vscodeclaude/cleanup.py`

---

## WHAT

### Function signature change

```python
# Before
def get_stale_sessions(
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> list[tuple[VSCodeClaudeSession, str]]:

# After
def get_stale_sessions(
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> list[tuple[VSCodeClaudeSession, str, str]]:
```

### Internal variable addition

```python
stale_sessions: list[tuple[VSCodeClaudeSession, str, str]] = []
```

---

## HOW

No new imports needed. All flags (`is_closed`, `is_blocked`, `is_ineligible`) are
already computed inside the function. The only structural change is:

1. Break the short-circuit `or` condition into an explicit `is_stale` bool.
2. Build a `reasons` list from the four flags.
3. Append `(session, git_status, reason)` instead of `(session, git_status)`.

---

## ALGORITHM

```
# Replace the short-circuit or-condition:
is_stale = (not is_closed and not is_blocked and not is_ineligible
            and is_session_stale(session, cached_issues=cached_for_stale_check))

if is_closed or is_blocked or is_ineligible or is_stale:
    reasons = []
    if is_closed:     reasons.append("closed")
    if is_blocked:    reasons.append("blocked")
    if is_ineligible: reasons.append("bot status")
    if is_stale:
        if cached_for_stale_check is not None and status_labels:
            reasons.append(f"stale → {status_labels[0]}")
        else:
            reasons.append("stale")
    reason = ", ".join(reasons)
    git_status = get_folder_git_status(Path(session["folder"]))
    stale_sessions.append((session, git_status, reason))
```

**Important:** `is_session_stale` is only called when `is_closed`, `is_blocked`, and
`is_ineligible` are all `False` — exactly as before (short-circuit preserved via explicit
guard).

Also add `status_labels: list[str] = []` before the `if cached_issues_by_repo:` block.
This makes the scoping explicit and prevents any theoretical `UnboundLocalError` if the
code is ever restructured. The reason-building logic reads `status_labels` only when
`cached_for_stale_check is not None`, which is safe, but the initialisation removes the
reliance on implicit scoping.

---

## DATA

**Return type:** `list[tuple[VSCodeClaudeSession, str, str]]`

Each tuple: `(session, git_status, reason)` where:
- `session`: unchanged `VSCodeClaudeSession` TypedDict
- `git_status`: one of `"Clean"`, `"Dirty"`, `"Missing"`, `"No Git"`, `"Error"`
- `reason`: non-empty string, e.g. `"closed"`, `"blocked"`, `"closed, blocked"`,
  `"stale → status-05:bot-pickup"`, `"stale"`
