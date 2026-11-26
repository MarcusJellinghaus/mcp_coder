# Step 10: "applied" ignores review logs and is measured before `_after_steps`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_10.md`.
> Write the tests first, then the code. Run pylint, mypy, the fast pytest set
> (`-n auto`) and the git integration tests of the new file
> (`markers=["git_integration"]`, path `tests/workflows/review/test_round_applied.py`).
> Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/review/steps.py`: new `round_applied`
- `src/mcp_coder/workflows/review/core.py`: use it; drop `is_working_directory_clean`
- `tests/workflows/review/test_round_applied.py` (new)
- `tests/workflows/review/conftest.py`: `env` fixture seam
- `tests/workflows/review/test_core.py`: the two no-op tests (~lines 333 and 420)

## WHAT

```python
_REVIEW_LOG = re.compile(r"^pr_info/[^/]*_review_log_[^/]*\.md$")

def round_applied(project_dir: Path, sha_before: str | None) -> bool:
    """Return whether files other than review logs changed since ``sha_before``.

    Compares ``sha_before`` with the working tree (committed and uncommitted
    tracked changes). Untracked files need no check: commit_changes has just
    staged everything. An unknown SHA or a git error counts as applied.
    """
```

## HOW

- `steps.py` imports `git_diff` from `mcp_coder.mcp_workspace_git`, plus
  `re` and `sys`.
- Call `git_diff(project_dir, ["--name-only", sha_before], compact=False,
  max_lines=sys.maxsize)`. It returns `"No changes found"` for an empty diff
  and raises on failure.
- `core.py`:
  - import `round_applied` from `.steps`;
  - after the `push_changes` success check and before
    `_after_steps(..., is_dismiss=False)`: `applied = round_applied(project_dir, sha_before)`;
  - at the bottom: `changes="applied" if applied else "no-op"`;
  - delete the old `changed = …` expression and the `is_working_directory_clean` import.
- The top-of-loop flush stays above `sha_before`.
- `conftest.py` `env`: remove the `is_working_directory_clean` patch. Add
  `mocks.round_applied = MagicMock(return_value=True)`, patched as
  `core.round_applied`.
- `test_core.py` no-op tests: set `env.round_applied.return_value = False`
  instead of `env.is_working_directory_clean.return_value = True`.
- Precondition: if the git integration test shows that `git_diff` rejects a
  bare SHA argument (`ValueError` from argument validation), write one line to
  `pr_info/.blocked.txt` and stop.

## ALGORITHM

```
if sha_before is None: return True
try: out = git_diff(project_dir, ["--name-only", sha_before], compact=False, max_lines=sys.maxsize)
except Exception as exc: logger.warning("Could not diff the review round: %s", exc); return True
if out.strip() == "No changes found": return False
return any(line.strip() and not _REVIEW_LOG.match(line.strip()) for line in out.splitlines())
```

## DATA

`bool`: True = applied, False = no-op.

## Tests first (`test_round_applied.py`)

Unit tests (patch `steps.git_diff`):

- `sha_before=None` → True, and `git_diff` is not called.
- `"No changes found"` → False.
- `"pr_info/implementation_review_log_1.md\npr_info/plan_review_log_2.md"` → False.
- `"pr_info/implementation_review_log_1.md\nsrc/a.py"` → True.
- `git_diff` raising → True, with one WARNING.

`@pytest.mark.git_integration` (fixture `git_repo` from `tests/conftest.py`):

- Initial commit with `a.py`, then `sha = repo.head.commit.hexsha`.
  - Commit a new `pr_info/implementation_review_log_1.md` → False.
  - Rewrite that log (a reformat), commit → False.
  - Modify `a.py` without committing → True.
  - Commit `a.py` → True.

Core-level (`env` fixture, add to this file):

- **No-op round, then a rebase:** verdict `tasks` then `dismiss`, with
  `env.round_applied.return_value = False`. `round_applied` is called before
  `env.attempt_rebase_and_push` (recorded order), and the round-1 log contains
  `no-op`.
- **Applied round:** default True → round-1 log contains `applied`.

## Commit

`fix(review): count a round as applied only when non-log files changed`
