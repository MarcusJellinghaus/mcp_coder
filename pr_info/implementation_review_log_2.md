# review-implementation review log 2

Issue #1114 — Jenkins permission errors: strip HTML, diagnose 403/404, add verify check.
Continues from `implementation_review_log_1.md` (4 rounds; round 4 stopped for a rebase).

## Round 1 — 2026-08-25

**Checks**: pytest 5059 passed / 2 skipped (fast suite, all marker exclusions) · pylint clean ·
mypy strict clean · ruff clean · lint-imports 21/21 kept · vulture clean · file-size 832 files pass.
The stale-`.venv` gap that prevented pytest in all four rounds of log 1 is resolved, so this is the
first round whose findings are test-verified.

**Findings** (14; none high, 6 medium):
- `diagnostics.py:281-286` (M) — 404 ancestor walk claims "'X' is readable; 'Y' under it is not" as
  soon as any ancestor answers 200, discarding `unreached`; a 5xx/transport-failed probe of `Y` is
  reported as a denial. Round 3 fixed this class on the fall-through path only.
- `docs/repository-setup/jenkins.md:160` (M) — "A failed run prints a traceback" is false for
  `coordinator --all`/`--repo` after this PR dropped `exc_info=True` at `commands.py:328`.
- `test_verify_jenkins.py:356-369` (M) — 403 job-row test asserts only the docs pointer, which every
  diagnosis ends with; `diagnose_404` or a dropped `original_error` would still pass.
- `verify_jenkins.py:175-178` (M) — `_probe_job` transport-failure and unmodelled-status arms untested.
- `verify_jenkins.py:210-211` (M) — `if not result: return {}` uncovered; a regression would print an
  empty `=== JENKINS JOBS ===` header and fail nothing.
- `test_diagnostics.py:352-375` (M) — does not assert *which* ancestor is named, leaving the
  `unreached is None` guard untested.
- `diagnostics.py:112-113` (L) — claim that the no-marker fallback leaks raw markup.
- `diagnostics.py:165-166` (L) — the `returned HTTP {status} - "{text}"` variant never exercised.
- `diagnostics.py:215-226` (L) — CSRF-disabled Jenkins returns 404 on `/crumbIssuer`, firing the
  inconclusive branch for what is probably a Job/Build gap.
- `test_client_errors.py:280`, `test_verify_jenkins.py:301/:313`, `test_diagnostics.py:70-78` (L) —
  vacuous assertions.
- `test_client.py:336-359` (L) — docstring claims more than the assertion checks.
- `test_verify_jenkins.py:198-224` (L) — no socket guard; hermetic only while `Session.mount(None)` raises.

**Decisions**:
- Accepted 11: findings 1-6, 8, 9, 10, 11, 12 above. Finding 1 is the same overclaim class the issue's
  Decisions table exists to prevent; finding 6 is a plainly false sentence shipped in this PR; the rest
  are bounded test-quality fixes closing genuine coverage gaps or removing assertions that cannot fail.
- Verify-first 1: the raw-markup fallback claim contradicted the `_TAG_RE` claim in another finding.
  Engineer probed it — `_TAG_RE.sub` runs unconditionally on all paths, so **no change needed**.
- Skipped 2: the CSRF-disabled misdirection (message is inconclusive, not wrong; not the default on
  supported Jenkins — speculative per the knowledge base) and the redundant `"crumb"` assertion
  (harmless, documents a security intent).
- Not reopened: round 4's dismissed items (traceback loss for non-Jenkins exceptions at
  `commands.py:328`; `diagnose_403`'s Job/Build steer on a Job/Read row).

**Changes**: 6 files — `diagnostics.py` (ancestor walk now claims a segment unreadable only when its
own probe returned 401/403/404, else names the incomplete probe; `_DENIED_STATUSES` extracted),
`docs/repository-setup/jenkins.md` (traceback sentence corrected against `commands.py`/`main.py`
and `log_function_call`'s own `exc_info=True`), and four test files. Post-change: pytest 5068 passed /
2 skipped, pylint / mypy / ruff / lint-imports all clean.

**Status**: committed

## Round 2 — 2026-08-25

**Checks**: pytest 5068 passed / 2 skipped · pylint clean · mypy strict clean · ruff clean ·
lint-imports 21/21 kept · file-size 832 files pass · CI PASSED on `3b52653`. Vulture's 3 hits are
pytest fixtures (false positives). The reviewer independently re-verified round 1's fixes against
the code, and confirmed `probe_session`'s `_auths[0][1]` assumption against the installed
python-jenkins source.

**Findings** (3; none high, 1 medium):
- `test_verify_jenkins.py:376-377` (M) — `assert "Windows-Agents" in row["error"]` /
  `assert "Executor" in ...` cannot fail: all five `diagnose_404` branches open with
  `f"404 on '{job_path}' - …"`. The test is documented as pinning the ancestor walk, but reverting
  the `child.status not in _DENIED_STATUSES` guard added in `3b52653` leaves it green — so the
  behaviour that commit changed has no verify-path test.
- `client.py:282-294` (L) — a 401 is routed to `diagnose_403`, three of whose terminal messages
  hardcode "403 Forbidden".
- `test_diagnostics.py:195, 233, 358` (L) — three assertions strictly implied by the line above them.

**Decisions**:
- Accepted 1: the medium. It guards the exact change made last round, and `test_diagnostics.py:359`
  already shows the correct pattern (assert the quoted segment, which only the narrowing branch emits).
- Skipped 2: the 401 wording — the reviewer could not construct a realistic path to it (the probes
  reuse the same credentials, so a genuine 401 hits the early return at `diagnostics.py:207`), and
  threading the real status through `diagnose_403` would ripple across its signature, both callers
  and their tests; meaningful scope for an unreachable case. The implied assertions — same
  harmless-noise class skipped last round, and the reviewer proposed no action.

**Changes**: `tests/cli/commands/test_verify_jenkins.py` — assertions rewritten to bite on the
narrowing branch, verified by breaking `diagnostics.py:289` and watching the test fail.

**Status**: committed

## Round 3 — 2026-08-25

**Checks**: pytest 5068 passed / 2 skipped · pylint clean · mypy strict clean · ruff clean ·
lint-imports 21/21 kept · file-size 832 files pass · CI PASSED on `e79fded`.

**Findings**: none.

The reviewer verified rather than assumed: traced the `diagnose_404` ancestor walk for 2-, 3- and
4-segment paths and confirmed `child is None` only on the first iteration (where the leaf's own 404
is the premise), so every "under it is not" claim is backed by a real 401/403/404 on that segment;
confirmed `e79fded`'s assertions are emitted only by the narrowing branch; re-read the installed
python-jenkins source to confirm `probe_session`'s `_auths[0][1]` assumption and that
`_maybe_add_auth` / `_auth_resolved` are untouched; confirmed every `execute_verify` call site in the
test tree is hermetic; confirmed `job_url_path()` and `base_url` are behaviour-preserving and the
409 `HTTPError` branch survives correctly ordered after `except JenkinsException`.

**Decisions**: nothing to accept. The one adjacent case considered — `_DENIED_STATUSES` includes 401,
so an auth failure during the ancestor walk would render as "lacks Job/Read" — is the same
unreachable-in-practice class as the already-rejected 401 labelling finding, since the probes reuse
the credentials that just produced the 404.

**Changes**: none.

**Status**: no changes needed

## Final Status

Three rounds this run (six across both logs). Two commits produced:

| Commit | Scope |
|---|---|
| `3b52653` | 404 segment overclaim fix in `diagnostics.py`, `jenkins.md` traceback sentence, 10 test-quality fixes |
| `e79fded` | `test_job_404_names_both_segments` tightened to pin the ancestor walk |

Round 3 produced zero findings, which is what closed the loop.

**Final check results** (supervisor-run): lint-imports **21 kept / 0 broken** across 700 files and
3595 dependencies, including `Layered Architecture`, `Jenkins Operations Independence` and the
widened `Requests Library Isolation`. Vulture reports 3 hits at 60% confidence
(`_neutral_jenkins_verify`, `_live_jenkins_verify`, `fixture_access_denied_html`) — all pytest
fixtures resolved by injection, false positives; no whitelist added and nothing in the repo gates on
vulture. Engineer-run: pytest 5068 passed / 2 skipped, pylint / mypy strict / ruff clean, file-size
832 files within 750 lines. CI PASSED on `e79fded`.

**Note on this run's value**: all four rounds in log 1 ran without pytest, blocked by a stale `.venv`
(`mcp_workspace.checks.branch_status_rendering`). That gap is resolved, so this run is the first
whose findings and fixes were verified against a green 5068-test suite.

**Outstanding, not code**: the branch is 2 commits behind `origin/main` (`6959984`, `87a1b8a` —
reference config and CLAUDE.md, conflict-free) and no PR exists yet. Four commits earlier on the
branch (`3d2f53d`, `c035723`, `b04c016`, `2b02e19`) have a literal ` ``` ` as their subject line —
worth rewording if the rebase squashes anything, but out of scope for this review.
