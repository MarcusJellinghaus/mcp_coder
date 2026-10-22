# Step 2 — Format `tools/` in CI, drop local formatter scripts

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`). Implement step 2 only:
> extend the CI formatter jobs to `tools`, delete the four formatter scripts, update the three docs as
> specified below, run the checks, and produce exactly one commit.

## WHERE

- `.github/workflows/ci.yml` (matrix `check` entries `black` and `isort`, ~lines 100-101)
- Delete: `tools/format_all.bat`, `tools/format_all.sh`, `tools/black.bat`, `tools/iSort.bat`
- `docs/repository-setup/python.md`
- `docs/repository-setup/README.md`
- `docs/processes-prompts/development-process.md`

## WHAT

No functions. CI config, file deletions and doc edits.

### 1. `.github/workflows/ci.yml`

```yaml
- {name: "black", cmd: "black --version && black --check src tests tools"}
- {name: "isort", cmd: "isort --version && isort --check --profile=black --float-to-top src tests tools"}
```

Keep the isort flags unchanged. Precondition: if the black/isort entries are gone because the ruff formatter
migration (#1174/#1175) landed, add `tools` to the ruff format / ruff `I` CI job targets instead. If no
formatter CI job exists, write one line to `pr_info/.blocked.txt` and stop.

### 2. Delete scripts

Use `mcp__mcp-workspace__delete_this_file` for each of the four files.

### 3. `docs/repository-setup/python.md`

- Key Sections table rows for `[tool.black]` and `[tool.isort]`: in the "Read by" column, remove
  `, tools/black.bat` and `, tools/iSort.bat` (leave `mcp__mcp-tools-py__run_format_code`).
- Replace the whole `### Formatting Tools` subsection body (note, script table, `format_all.sh` sample,
  trailing "config items these tools read" line) with one line:

  ```markdown
  Format via `mcp__mcp-tools-py__run_format_code` (formatter chosen by `[tool.mcp-tools-py] formatter`); the CI formatter jobs are the backstop and also cover `tools/`.
  ```

- Move the row `| \`ruff_check.sh/bat\` | Run ruff lint on src/tests/tools | Optional |` into the
  `### Quality Check Tools` table, with the category `Optional (CI runs it)` to match the other rows there.

### 4. `docs/repository-setup/README.md`

Remove the row `| \`tools/format_all.{sh,bat}\` | P | No | Yes | — |`.

### 5. `docs/processes-prompts/development-process.md`

Remove the bullet `- \`tools/format_all.bat\` - Run all formatting tools (ruff, black, isort)`.

## HOW

- Formatter-neutral doc wording, so it still holds after #1174/#1175.
- Do not touch `docs/repository-setup/github.md` (generic template stays `src tests`).
- Do not add `tools` to pytest `testpaths`.

## ALGORITHM

```
edit ci.yml black/isort targets -> "src tests tools"
delete 4 formatter scripts
apply the 3 doc edits
search_files pattern "format_all|black\.bat|iSort\.bat" -> expect 0 hits outside pr_info/
run format (default dirs + target_directories=["tools"] check_only), pylint, pytest, mypy
commit
```

## DATA

None.

## Verification (serves as the test)

1. `mcp__mcp-workspace__search_files(pattern="format_all|black\\.bat|iSort\\.bat")`: no hits except in `pr_info/`.
   Fix any remaining reference before continuing.
2. `mcp__mcp-tools-py__run_format_code`
3. `mcp__mcp-tools-py__run_format_code(target_directories=["tools"], check_only=True)`: black must report no
   changes. isort may report charmap errors for 3 `tools/mlflow/` files on Windows. That's a known local
   limitation; ignore it.
4. `mcp__mcp-tools-py__run_pylint_check`
5. `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])`
6. `mcp__mcp-tools-py__run_mypy_check`

## Commit

`chore(ci): format tools/ in CI, remove local formatter scripts`
