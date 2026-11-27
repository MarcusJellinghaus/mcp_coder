# Step 5 — `script-directories` key and docs

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_5.md`), then implement
> step 5 only. Config key and docs; no Python code. Run the checks below and commit
> (one commit).

## Tests

None. The installed mcp-tools-py ignores the key until mcp-tools-py#308 ships, so its
effect is verified after merge (see the summary). Its presence is checked below.

## WHERE / WHAT / HOW

### `pyproject.toml`, `[tool.mcp-tools-py]` (~line 198)

Add one line after `formatter = "ruff"`, with no comment, and keep the other keys:

```toml
script-directories = ["tools"]
```

Don't add `tools` to `[tool.setuptools.packages.find] where` or to
`[tool.pytest.ini_options] testpaths`.

### `docs/configuration/toolkits.md` (~line 157, the "Its own settings stay in `[tool.mcp-tools-py]`" bullet)

Add `script-directories` to the listed keys and one sentence: folders of scripts that get the
formatter, ruff, pylint and mypy, but not vulture, bandit, deptry, coverage or pytest; needs
mcp-tools-py with #308 (earlier versions ignore it).

### `docs/repository-setup/python.md`

- Key Sections table (~line 19): add a row after the `formatter` row:
  `| [tool.mcp-tools-py] script-directories | mcp-tools-py's checks and formatter, mcp-coder's toolkit (format and check); needs mcp-tools-py with #308 | Script folders (e.g. tools) that get the formatter, ruff, pylint and mypy, but not vulture, bandit, deptry, coverage or pytest |`
  (format the key and folder name as code like the other rows)
- Line 91: replace "the CI formatter jobs are the backstop and also cover `tools/`" with:
  local formatting covers `tools/` too once mcp-tools-py with #308 is installed
  (`script-directories`); the CI formatter jobs are the backstop.

### `docs/repository-setup/quality-and-security-checks.md`

- `## Types` (~line 74): "mypy strict over `src`, `tests` and `tools`, CI job `mypy`."
- `## Pylint` (~line 82): "CI job `pylint`, over `src`, `tests` and `tools`." Match the
  wording of the Formatting section.

## ALGORITHM / DATA

None.

## Checks before commit

1. `search_files(pattern="script-directories", glob="pyproject.toml")`: exactly one hit,
   under `[tool.mcp-tools-py]`
2. `run_format_code(target_directories=["src", "tests", "tools"])`
3. `run_ruff_check`, `run_mypy_check`, `run_pylint_check`, each with
   `target_directories=["src", "tests", "tools"]`: clean
4. Fast unit-test run from `.claude/CLAUDE.md` (with `-n auto`): pass. That includes the
   tests that parse `pyproject.toml`.

If any check fails because of the new key (e.g. a config validation test rejects the
unknown key), write one line to `pr_info/.blocked.txt` naming the failing check and stop.

Commit message: `chore(config): declare tools as script directory`
