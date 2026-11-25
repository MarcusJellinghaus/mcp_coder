# Step 4 — Classifier: retry signatures and PIPE-NO-STATUS suppression

## LLM prompt
> Read `pr_info/steps/summary.md` (§4) and this file. Implement step 4 only: add the two
> retry signatures and the `no_status_suppressed_by` key to
> `tools/jenkins_issue_patterns.toml`, honour the key in
> `tools/jenkins_classify_logs.py`, and update `tools/jenkins_issue_analysis.md`.
> Write the tests first. Run ruff check, pylint, mypy and the fast unit tests
> (CLAUDE.md), format, and make one commit.

## WHERE
- `tools/jenkins_issue_patterns.toml`
- `tools/jenkins_classify_logs.py`
- `tools/jenkins_issue_analysis.md`
- `tests/tools/test_jenkins_classify_logs.py`

## WHAT

`jenkins_issue_patterns.toml`:
- `[classifier]`: after `no_status_id`, add

  ```toml
  # Ids that cancel the no_status_id: their match means the failure was recovered
  # inside the step (e.g. mcp-coder install retried uv and it succeeded), even though
  # the log still holds the first error that matched a pre_workflow signature.
  no_status_suppressed_by = ["MC-INSTALL-UV-RETRY-OK"]
  ```
- Two signatures, right after `ENV-PYPI-NETWORK`, **without** `pre_workflow`:

  ```toml
  [[signature]]
  id = "MC-INSTALL-UV-RETRY"
  regex = 'retrying once in'

  [[signature]]
  id = "MC-INSTALL-UV-RETRY-OK"
  regex = 'uv retry succeeded'
  ```

`jenkins_classify_logs.py`:
- `Patterns` gets `no_status_suppressed_by: frozenset[str]`.
- `load_patterns`: `no_status_suppressed_by=frozenset(data["classifier"]["no_status_suppressed_by"])`
  (strict, like the other `[classifier]` keys; a missing key is a `KeyError`, already
  reported by `main` as "Error loading patterns").
- `classify`: update the docstring's Returns ("… the no-status id when a pre-workflow
  signature matched and no suppressing id did").

## ALGORITHM

```
ids = matching signature ids; blocked reason appended as today
if patterns.pre_workflow & ids and not (patterns.no_status_suppressed_by & ids):
    ids.append(patterns.no_status_id)
return ids
```

## DATA
`classify()` still returns `list[str]`; recovered logs simply lack the no-status id.

## Tests (write first) — `tests/tools/test_jenkins_classify_logs.py`
Uses the real patterns file (`patterns` fixture). Log text constants:

```python
_PYPI_ERROR = "error: Failed to fetch: `https://pypi.org/simple/flask-cors/`\n"
_CACHE_ERROR = (
    "error: Failed to write to the client cache\n"
    "  Caused by: Failed to persist temporary file to "
    "C:\\Users\\builder\\AppData\\Local\\uv\\cache\\simple-v14\\pypi\\starlette.rkyv: "
    "Access is denied. (os error 5)\n"
)
_RETRY = "--- uv failed with a transient error ({}); retrying once in 10 s\n"
_RETRY_OK = "--- uv retry succeeded\n"
```

1. `test_classify_recovered_uv_retry_has_no_status_id` — parametrized over
   `(_PYPI_ERROR, "ENV-PYPI-NETWORK")` and `(_CACHE_ERROR, "ENV-UV-ACCESS-DENIED-CACHE")`;
   text = error + `_RETRY.format(id)` + `_RETRY_OK`; result contains the ENV id(s),
   `MC-INSTALL-UV-RETRY` and `MC-INSTALL-UV-RETRY-OK`, and **not**
   `PIPE-NO-STATUS-ON-PRE-WORKFLOW-FAILURE`.
2. `test_classify_failed_uv_retry_keeps_no_status_id` — `_PYPI_ERROR * 2` +
   `_RETRY.format("ENV-PYPI-NETWORK")` (no success line) → contains
   `MC-INSTALL-UV-RETRY` and `PIPE-NO-STATUS-ON-PRE-WORKFLOW-FAILURE`.
3. `test_retry_line_matches_no_env_signature(patterns)` — uses the module's `patterns`
   fixture like the other classifier tests;
   `jenkins_classify_logs.classify(_RETRY.format("ENV-PYPI-NETWORK"), patterns)
   == ["MC-INSTALL-UV-RETRY"]` (the retry line alone must not look like uv's error).

Existing tests (`test_classify_signature`, `test_main_tags_index_and_reports`,
`test_patterns_file_ids_are_unique`) must stay green unchanged.

## Docs — `tools/jenkins_issue_analysis.md`
Replace the `pre_workflow` rule (the bullet "`pre_workflow = true` marks failures before
the workflow runs. They also get the `PIPE-NO-STATUS-…` id …") with:

- `pre_workflow = true` marks failures before the workflow runs. They also get the
  `PIPE-NO-STATUS-…` id, because nothing sets a `*-failed` label — unless an id listed
  in `[classifier] no_status_suppressed_by` matched (e.g. `MC-INSTALL-UV-RETRY-OK`: uv
  failed, the install retried and recovered).
- Recovered builds don't fail: to count them, download logs with
  `--status success,unstable`.
