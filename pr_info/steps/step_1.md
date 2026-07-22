# Step 1 — Bump `langgraph` / `langchain-core` floors in `[langchain-base]` (TDD)

**One commit:** regression-guard test + `pyproject.toml` floor bump + checks passing.

See [summary.md](./summary.md) for full context. This is the only step; the change
is packaging-metadata-only (no `src/` change, no new dependency).

---

## WHERE

- `tests/test_pyproject_config.py` — **modified** (add one test function).
- `pyproject.toml` — **modified** (`[project.optional-dependencies].langchain-base`).

## WHAT

Add one test to `tests/test_pyproject_config.py`:

```python
def test_pyproject_langchain_base_floors() -> None:
    """Verify [langchain-base] declares the floors that clear #1078's warning."""
```

It parses `pyproject.toml` with `tomllib` (same pattern as the existing tests in the
file) and asserts the `langchain-base` extra contains `langchain-core>=1.4.7` and
`langgraph>=1.2.9`.

## HOW

- Reuse the existing file's idiom: open `pyproject.toml` (path
  `Path(__file__).parent.parent / "pyproject.toml"`), `tomllib.load`, index into
  `config["project"]["optional-dependencies"]["langchain-base"]`.
- No new imports beyond the `tomllib` / `Path` already imported at the top of the file.
- `tomllib` strips comments, so the test asserts on version specifiers only — **not**
  on the `#1078` comment. The comment is still required in `pyproject.toml` (it is the
  self-documentation the issue mandates); it is simply verified by review, not by test.

## ALGORITHM

```
load pyproject.toml via tomllib
base = config["project"]["optional-dependencies"]["langchain-base"]
assert any entry == "langchain-core>=1.4.7"   in base   # honest declared floor
assert any entry == "langgraph>=1.2.9"        in base   # -> checkpoint>=4.1.0 fix
```

Then edit the `langchain-base` extra so both assertions pass:

```toml
langchain-base = [
    "langchain-core>=1.4.7",
    "langchain-mcp-adapters>=0.1.0",
    # >=1.2.9 -> langgraph-checkpoint>=4.1.0 (Reviver allowed_objects fix); see #1078
    "langgraph>=1.2.9",
    "httpx>=0.27.0",
]
```

- Leave `langchain-mcp-adapters>=0.1.0` and `httpx>=0.27.0` **unchanged** (out of scope).

## DATA

- Test returns `None`; asserts on `list[str]` from the parsed TOML.
- No runtime data structures, return-value, or API changes.

## Verification (run after the edit)

- `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "tests/test_pyproject_config.py"])`
  — the new test goes red before the `pyproject.toml` edit, green after.
- Full mandatory gate: `run_pylint_check`, `run_pytest_check` (unit subset), `run_mypy_check`.
- Formatting: black/isort do not touch `.toml`; run `mcp__mcp-tools-py__run_format_code` per CLAUDE.md as a no-op safety check.

## LLM Prompt

> Implement Step 1 as described in `pr_info/steps/step_1.md`, using `pr_info/steps/summary.md`
> for context. This is a packaging-metadata-only change for issue #1078 — do **not**
> modify anything under `src/`.
>
> 1. **Test first (TDD):** In `tests/test_pyproject_config.py`, add
>    `test_pyproject_langchain_base_floors` following the existing tests' idiom
>    (`tomllib` + `Path(__file__).parent.parent / "pyproject.toml"`). Assert that the
>    `langchain-base` extra contains `"langchain-core>=1.4.7"` and `"langgraph>=1.2.9"`.
>    Run it and confirm it fails against the current stale floors.
> 2. **Then edit `pyproject.toml`:** in the `[project.optional-dependencies].langchain-base`
>    extra, change `langchain-core>=0.3.0` → `langchain-core>=1.4.7` and
>    `langgraph>=0.2.0` → `langgraph>=1.2.9`, adding this comment on the line directly
>    above the `langgraph` pin:
>    `# >=1.2.9 -> langgraph-checkpoint>=4.1.0 (Reviver allowed_objects fix); see #1078`.
>    Leave `langchain-mcp-adapters` and `httpx` untouched.
> 3. Re-run the new test (now green), then run the mandatory quality gate
>    (pylint / pytest unit subset / mypy) and confirm all pass. Produce exactly one commit.
