# Step 4 — README badge lines

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 4** exactly as described in
> `pr_info/steps/step_4.md`. Insert the three badge lines under the `# MCP Coder` title in
> `README.md`, copying the Markdown below verbatim. Run the checks listed below, run the formatter,
> and produce exactly one commit.

## Precondition

`README.md` line 1 is `# MCP Coder`. If not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `README.md` — directly after line 1 (`# MCP Coder`)

## WHAT

Insert between `# MCP Coder` and `**What is MCP Coder?**` — each line is one physical line, with a
blank line before, between and after the three lines (otherwise they merge into one row):

```markdown
# MCP Coder

[![CI](https://github.com/MarcusJellinghaus/mcp_coder/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/MarcusJellinghaus/mcp_coder/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/mcp-coder)](https://pypi.org/project/mcp-coder/) [![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/MarcusJellinghaus/mcp_coder/main/pyproject.toml)](https://pypi.org/project/mcp-coder/) [![License](https://img.shields.io/github/license/MarcusJellinghaus/mcp_coder)](LICENSE)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![mypy](https://img.shields.io/badge/mypy-strict-blue)](https://mypy.readthedocs.io/) [![pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint) [![architecture](https://img.shields.io/badge/architecture-import--linter%20%C2%B7%20tach%20%C2%B7%20pycycle%20%C2%B7%20deptry%20%C2%B7%20vulture-blue)](docs/architecture/architecture.md) [![coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/MarcusJellinghaus/9a7892066964f11765a07d74285ad104/raw/mcp_coder-coverage.json)](https://github.com/MarcusJellinghaus/mcp_coder/actions/workflows/ci.yml)

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/MarcusJellinghaus/mcp_coder/badge)](https://scorecard.dev/viewer/?uri=github.com/MarcusJellinghaus/mcp_coder) [![CodeQL](https://github.com/MarcusJellinghaus/mcp_coder/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/MarcusJellinghaus/mcp_coder/actions/workflows/github-code-scanning/codeql)

**What is MCP Coder?**
```

Notes on the URLs (do not "fix" them):
- Shields static badge paths: literal `-` is `--` (`import--linter`), space is `%20`, `·` is `%C2%B7`.
- The coverage URL carries the literal gist ID `9a7892066964f11765a07d74285ad104`.
- Scorecard shows `invalid repo path` until the first publish after merge; coverage shows `pending`
  until the first `main` run — both expected.

## HOW

Pure Markdown; `LICENSE` (Step 1) and `docs/architecture/architecture.md` (exists) are relative links.

## ALGORITHM

None (static Markdown).

## DATA

Three Markdown paragraphs: line 1 metadata (4 badges), line 2 quality tooling (5 badges), line 3
security (2 badges).

## Verification

- Re-read `README.md` lines 1–9: title, blank, line 1, blank, line 2, blank, line 3, blank,
  `**What is MCP Coder?**`. Every badge is `[![alt](image)](link)` with balanced brackets.
- Run `mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_pytest_check` (fast unit set
  from CLAUDE.md, with `-n auto`), `mcp__mcp-tools-py__run_mypy_check` — all pass.
- `mcp__mcp-tools-py__run_format_code`, then commit:
  `docs(readme): add metadata, tooling and security badges`
