# Step 5 — per-`CIStatus` messages in `check_ci_proven_gate`

Part of issue #1183. Read `pr_info/steps/summary.md` first.

## Precondition

`check_ci_proven_gate` in `src/mcp_coder/workflows/review/gates.py` must
still end with the single generic `ci_unknown` message shown below. If its
shape has changed materially, write one line to `pr_info/.blocked.txt`
describing the mismatch and stop.

```python
return "ci_unknown", (
    f"CI status is `{status.value}` — could not prove CI ran green. "
    f"Check the GitHub token and whether this repo has a CI workflow."
)
```

## Goal

Replace that one message with a per-`CIStatus` lookup so the failure comment
names the actual cause: only `UNAVAILABLE` should still mention the GitHub
token. `PENDING`, `UNKNOWN`, and `NOT_CONFIGURED` each get their own hedged
wording (per the table in the issue), and any other/future status falls
through to a generic, token-free fallback.

## TDD order

1. Split the existing parametrized test in `tests/workflows/review/
   test_gates.py::TestCheckCiProvenGate::test_unprovable_states_are_ci_unknown`
   into one test per status (below), plus a new fallback test — all written
   first, so the per-status ones fail against today's single message.
2. Implement the dict + `.get(..., fallback)` lookup and the docstring
   update until all pass.

## WHERE

`src/mcp_coder/workflows/review/gates.py` — add a module-level mapping
right above `check_ci_proven_gate` (near the existing `MAX_LISTED_TASKS`
constant), and change the function's final `return` to use it.

## WHAT

```python
_CI_UNKNOWN_MESSAGES: dict[CIStatus, str] = {
    CIStatus.PENDING: (
        "CI has not finished for the latest commit — re-run the review "
        "once CI completes."
    ),
    CIStatus.UNKNOWN: (
        "CI status could not be collected (GitHub lookup failed) — re-run "
        "the review; if it persists, check GitHub API availability and "
        "rate limits."
    ),
    CIStatus.UNAVAILABLE: (
        "CI status is unavailable — check the GitHub token and its "
        "permissions."
    ),
    CIStatus.NOT_CONFIGURED: (
        "No CI runs were found, or status could not be collected — re-run "
        "the review; if it persists, check that the repo has a CI "
        "workflow."
    ),
}

_CI_UNKNOWN_GENERIC_MESSAGE = (
    "could not be proven green — re-run the review; if it persists, "
    "investigate the CI status collector."
)
```

`check_ci_proven_gate`'s signature is unchanged
(`(project_dir: Path) -> tuple[str | None, str | None]`).

## HOW

`CIStatus` is already imported in `gates.py`'s module
(`mcp_coder.checks.branch_status`) — no new import needed beyond adding the
dict. `check_ci_proven_gate`'s final branch becomes:

```python
message = _CI_UNKNOWN_MESSAGES.get(status, _CI_UNKNOWN_GENERIC_MESSAGE)
return "ci_unknown", f"CI status is `{status.value}` — {message}"
```

Update the function's docstring: it currently says every non-`PASSED`,
non-`FAILED` status's "fix is to check the token / whether CI exists" — that
sentence must change to describe the per-status table instead (token only
for `UNAVAILABLE`).

## ALGORITHM

Not applicable beyond the dict lookup above — no new branching logic, just
replacing one fixed string with a lookup + fallback.

## DATA

Return type unchanged: `tuple[str | None, str | None]`. `_CI_UNKNOWN_MESSAGES`
is a new private module-level `dict[CIStatus, str]`.

## Tests to add / change

`tests/workflows/review/test_gates.py`, inside `TestCheckCiProvenGate`:

- Delete the single parametrized `test_unprovable_states_are_ci_unknown`
  (which currently asserts `"GitHub token" in details` for all four
  statuses — that assertion is no longer true for 3 of the 4).
- Add four individual tests, each using the existing `_patch_ci` helper:
  - `test_pending_message` — `CIStatus.PENDING` → `reason == "ci_unknown"`,
    `"has not finished"` in details, `"GitHub token" not in details`.
  - `test_unknown_message` — `CIStatus.UNKNOWN` → `"could not be collected"`
    in details, `"GitHub token" not in details`.
  - `test_not_configured_message` — `CIStatus.NOT_CONFIGURED` →
    `"No CI runs were found"` in details, `"GitHub token" not in details`.
  - `test_unavailable_message_mentions_token` — `CIStatus.UNAVAILABLE` →
    `"GitHub token" in details` (the one status that keeps the token
    wording).
  - Every one of the four also asserts `ci_status.value in details` (the
    existing `f"CI status is \`{status.value}\` — ..."` prefix is kept).
- Add `test_generic_fallback_for_unlisted_status` — monkeypatch
  `gates.collect_branch_status` to return a `SimpleNamespace(ci_status=
  SimpleNamespace(value="WEIRD"))` and `gates.assess_ci` to return
  `"undeterminable"` directly (so the test does not depend on a real,
  unlisted `CIStatus` member existing); assert `reason == "ci_unknown"`,
  `"WEIRD" in details`, and `"GitHub token" not in details`.

## Commit

One commit: the test changes above + the dict/lookup implementation +
docstring update, passing pylint/pytest/mypy.

## LLM prompt

> Implement Step 5 of `pr_info/steps/summary.md` (issue #1183) exactly as
> described in `pr_info/steps/step_5.md`. Follow TDD: replace the single
> parametrized test with the five tests described (four per-status + one
> generic-fallback), confirm they fail against today's single message, then
> add `_CI_UNKNOWN_MESSAGES` / `_CI_UNKNOWN_GENERIC_MESSAGE` to
> `gates.py` and update `check_ci_proven_gate`'s final return and docstring
> until all pass. Run pylint/pytest/mypy; all must pass. Make exactly one
> commit.
