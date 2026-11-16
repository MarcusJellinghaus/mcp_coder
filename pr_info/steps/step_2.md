# Step 2: `check-sensitive-files` job in `ci.yml`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` only.
> Edit `.github/workflows/ci.yml` as specified. No Python changes, so no new tests; still
> run pylint, mypy and pytest (`-n auto`, fast unit-test markers) to confirm green. One commit.

## Precondition

`tools/check_sensitive_files.py` exists (step 1), `ci.yml` has the `check-forbidden-folders`
job, and `python tools/read_github_deps.py --specs` lists a spec starting with
`mcp-workspace ` (check `[tool.mcp-coder.install-from-github] packages` in `pyproject.toml`).
If any of these is missing, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

`.github/workflows/ci.yml`: new job directly after `check-forbidden-folders`, before the
`push-checks` comment block.

## WHAT

```yaml
  # PR only, advisory: warns when a PR changes sensitive files (#1431); never fails on findings.
  # HEAD^1 is the base tip of GitHub's merge commit (needs fetch-depth: 2).
  check-sensitive-files:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 2

      - name: Install uv
        uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3

      - name: Set up Python 3.11
        uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0
        with:
          python-version: 3.11

      - name: Install mcp-workspace
        run: |
          SPEC=$(python tools/read_github_deps.py --specs | grep '^mcp-workspace ')
          uv pip install --system "$SPEC"

      - name: Run check-sensitive-files
        run: python tools/check_sensitive_files.py --base HEAD^1 --head HEAD
```

## HOW

- Copy the action SHAs and version comments from the existing jobs in the same file; if
  they differ from the block above, use the ones in the file.
- Job-level `if` only: the `ci.yml` header forbids step-level skips.
- With deps (no `--no-deps`): importing `mcp_workspace.file_tools.access_rules` runs
  `file_tools/__init__.py`, which imports the whole file-tools package.
- `grep` with no match fails the step (bash `-e`), so a missing spec fails loudly.
- Keep the job name `check-sensitive-files` stable (future required-check name).

## ALGORITHM

None (workflow config).

## DATA

None. Verification: the PR's own CI run shows the warning annotations and summary table
(the PR adds the script and edits `ci.yml`, both on the watch list) — checked by the
reviewer in the GitHub UI.

## Commit

`ci: add advisory check-sensitive-files job for PRs (#1431)`
