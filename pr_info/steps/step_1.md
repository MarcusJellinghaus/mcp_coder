# Step 1 — Move `git_repo` fixture to root `tests/conftest.py`

**Commit:** `test: move git_repo fixture to root conftest`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Move the `git_repo` fixture and the `setup_git_config` helper into root
> `tests/conftest.py`. Delete the two explicit imports of `git_repo` and their
> `.importlinter` ignore entries. Do not touch `tests/workflows/rebase/conftest.py`.
> Run all checks listed in the summary, then make one commit.

## Precondition

`git_repo` must be defined only in `tests/utils/conftest.py`. Check with
`search_files(glob="tests/**/*.py", pattern=r"def git_repo\b")`. If it is defined anywhere
else, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `tests/conftest.py`
- `tests/utils/conftest.py`
- `tests/cli/commands/test_define_labels.py`
- `tests/workflows/test_create_pr_integration.py`
- `.importlinter`

## WHAT

In `tests/conftest.py`:
```python
@pytest.fixture
def git_repo(tmp_path: Path) -> tuple[git.Repo, Path]: ...

def setup_git_config(repo: git.Repo) -> None: ...
```

In `tests/utils/conftest.py`, the signature changes from `(tmp_path)`:
```python
@pytest.fixture
def git_repo_with_files(git_repo: tuple[Repo, Path]) -> tuple[Repo, Path]: ...
```

## HOW

- Copy both bodies and docstrings unchanged, except use `git.Repo`. Root conftest already
  has `import git`; do not add `from git import Repo` there.
- Remove `git_repo` and `setup_git_config` from `tests/utils/conftest.py`. Keep
  `from git import Repo`, which `git_repo_with_files` and `verify_git_state` still use.
  Keep `create_sample_files` and `verify_git_state`.
- Delete `from tests.utils.conftest import git_repo`:
  - `test_define_labels.py:31`
  - `test_create_pr_integration.py:24`

  Pytest now provides the fixture through conftest discovery.
- In `.importlinter`, delete lines 476-480. That is the "Allowed: Importing shared
  fixtures…" comment, the TODO, the `ignore_imports =` key and both
  `-> tests.utils.conftest` entries. Unmatched ignores are errors, so this must land in
  the same commit.

## ALGORITHM (`git_repo_with_files`)

```
repo, project_dir = git_repo          # already initialised + user configured
sample_files = {...unchanged...}
create_sample_files(project_dir, sample_files)
repo.index.add(list(sample_files)); repo.index.commit("Initial commit with sample files")
return repo, project_dir
```

## DATA

Both fixtures still return `tuple[Repo, Path]`. The repo lives at
`tmp_path / "test_project"`, same as before.

## Tests (TDD)

This is a refactor of test infrastructure. The existing tests are the specification:
- `tests/utils/test_git_encoding_stress.py` (now resolves `git_repo` from root)
- `test_define_labels.py`
- `test_create_pr_integration.py`
- every user of `git_repo_with_files`

No new tests. Run:
- the unit pytest run
- `markers=["git_integration"]`
- `run_lint_imports_check` (must pass with the ignores removed)
- pylint, mypy
