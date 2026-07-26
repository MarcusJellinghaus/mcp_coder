# Step 2 — Failure keys, `CheckRunError`, `_run_all_checks`

Add the deterministic judging core to `workflows/rebase.py`: reduce each check result to
a flat set of failure keys so that **regression = verification − baseline** is a single
set difference. See [summary.md](./summary.md) ("Baseline concept").

## WHERE

- Modify: `src/mcp_coder/workflows/rebase.py` (add a `# --- Check baseline /
  comparison ---` section; nothing existing is touched)
- Create: `tests/workflows/rebase/test_checks.py`

## WHAT

```python
class CheckRunError(Exception):
    """A check failed to RUN (infrastructure), as opposed to reporting failures."""

FailureKey = tuple[str, ...]  # ("pytest", nodeid) | ("pylint"|"mypy", file, code, message)

def _pytest_failure_keys(results: dict[str, Any]) -> set[FailureKey]: ...
def _pylint_failure_keys(result: PylintResult) -> set[FailureKey]: ...
def _mypy_failure_keys(result: MypyResult) -> set[FailureKey]: ...
def _run_all_checks(project_dir: Path) -> set[FailureKey]: ...
```

## HOW

- Import the three wrappers from `mcp_coder.mcp_tools_py` (Step 1) and the library
  result types for annotations.
- Line numbers **never** enter pylint/mypy keys (a rebase shifts lines; merely-moved
  messages must not look new).
- Pytest: **failing outcomes are failure keys** — `failed`, `error`, and any
  unrecognized outcome. `skipped`/`xfailed` are **not** keys: a rebase can pull new
  self-skipping tests in from the base branch (e.g. integration tests skipping in the
  unattended runner), and a skip the LLM cannot "fix" must not read as a regression.
  Collection errors count as failure keys too.
- Infrastructure vs. findings:
  - pytest `error_info` non-empty, or `test_results` missing → `CheckRunError`
  - pylint `result.error` set → `CheckRunError`
  - mypy `result.error` set → `CheckRunError` (the library reports run failures by
    returning `MypyResult(error=...)`, it does not raise); any exception from the
    wrapper → `CheckRunError` too
  - findings (failed tests, lint messages, type errors) are **keys, not errors**.

## ALGORITHM

```
_pytest_failure_keys(results):
    if results.get("error_info") or results.get("test_results") is None: raise CheckRunError
    keys = {("pytest", t.nodeid) for t in report.tests or []
            if t.outcome not in ("passed", "skipped", "xfailed")}
    keys |= {("pytest", c.nodeid) for c in report.collectors or [] if c.outcome != "passed"}
    return keys

_pylint_failure_keys(result):
    if result.error: raise CheckRunError
    return {("pylint", m.path, m.message_id, m.message) for m in result.messages}

_mypy_failure_keys(result):
    if result.error: raise CheckRunError
    return {("mypy", m.file, m.code or "", m.message)
            for m in result.messages if m.severity == "error"}

_run_all_checks(project_dir):
    for wrapper, extractor in the three pairs:
        try: keys |= extractor(wrapper(project_dir))
        except CheckRunError: raise
        except Exception as exc: raise CheckRunError(f"{name}: {exc}") from exc
    return keys
```

## DATA

- Return: `set[tuple[str, ...]]`. First element identifies the checker; remaining
  elements identify the finding without line numbers.
- `_run_all_checks` unions all three sets; raises `CheckRunError` with a
  human-readable message naming the failing checker.

## TDD

Write `tests/workflows/rebase/test_checks.py` first — pure unit tests, no mocks of git,
construct library dataclasses (`PytestReport`, `Test`, `Collector`, `PylintMessage`,
`PylintResult`, `MypyMessage`, `MypyResult`) directly:

1. pytest keys: failed/error tests become keys, passed/skipped/xfailed do not;
   collector with non-passed outcome becomes a key; `error_info` → `CheckRunError`.
2. pylint keys: message → key without line/column; `error` set → `CheckRunError`.
3. mypy keys: only `severity == "error"`; `code=None` maps to `""`; `error` set →
   `CheckRunError`.
4. Line-insensitivity: two messages identical except line number produce the same key.
5. Regression semantics: `verification - baseline` flags only new keys (test with
   plain set literals — documents the comparison contract).
6. `_run_all_checks`: mock the three wrappers; union asserted; wrapper exception →
   `CheckRunError`.

## Commit

One commit. Suggested message:
`feat: add failure-key extraction and check runner for rebase baseline comparison`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement `pr_info/steps/step_2.md`
> exactly: add `CheckRunError`, the three `_*_failure_keys` extractors, and
> `_run_all_checks` to `src/mcp_coder/workflows/rebase.py`, keyed as specified (pytest by
> node ID with any non-passed outcome plus collection errors; pylint/mypy by
> file/code/message with line numbers ignored). Write
> `tests/workflows/rebase/test_checks.py` first (TDD, pure unit tests). Do not modify the
> existing orchestrator or any other function in `rebase.py`. Run pylint, pytest, and
> mypy via the MCP check tools and fix any findings before finishing.
