# Step 1 — DRY shared CLI flags (`cli/shared_args.py`)

> Read `pr_info/steps/summary.md` first. This step implements the
> **"Canonical shared-flag wording"** section. It is one commit.

## Objective

Replace the ~13 copy-pasted `--project-dir` / `--llm-method` / `--mcp-config` /
`--settings` / `--execution-dir` declarations with five opt-in, override-capable
helpers, applying the single canonical wording and standardizing
`metavar="METHOD"` on every `--llm-method`. Parsed argument values (dest,
defaults, choices) stay **identical** — only `--help` text/metavar is unified.

## WHERE

- **Create** `src/mcp_coder/cli/shared_args.py`
- **Create** `tests/cli/test_shared_args.py`
- **Modify** `src/mcp_coder/cli/parsers.py`
- **Modify** `src/mcp_coder/cli/gh_parsers.py`

## WHAT — function signatures (`shared_args.py`)

```python
import argparse
from ..llm.types import SUPPORTED_PROVIDERS

_PROJECT_DIR_HELP = (
    "Project directory: where source code lives (git operations, file "
    "modifications). Default: current directory"
)
_LLM_METHOD_HELP = (
    "LLM method override. If omitted, uses config default_provider or claude"
)
_MCP_CONFIG_HELP = "Path to MCP configuration file (e.g., .mcp.linux.json)"
_SETTINGS_HELP = (
    "Path to Claude Code settings file (.claude/settings.local.json). "
    "Auto-detected from <project_dir>/.claude/ if omitted. "
    "Overrides Claude's cwd-based settings discovery."
)
_EXECUTION_DIR_HELP = (
    "Execution directory: where Claude subprocess runs (config discovery). "
    "Default: current directory"
)

def add_project_dir_arg(
    parser: argparse.ArgumentParser,
    *,
    help: str = _PROJECT_DIR_HELP,
    metavar: str | None = None,
) -> None: ...

def add_llm_method_arg(
    parser: argparse.ArgumentParser,
    *,
    help: str = _LLM_METHOD_HELP,
    metavar: str = "METHOD",
) -> None: ...

def add_mcp_config_arg(
    parser: argparse.ArgumentParser,
    *,
    help: str = _MCP_CONFIG_HELP,
) -> None: ...

def add_settings_arg(parser: argparse.ArgumentParser) -> None: ...

def add_execution_dir_arg(parser: argparse.ArgumentParser) -> None: ...
```

## HOW — integration

Each helper body is a single `parser.add_argument(...)` mirroring today's args:

- `--project-dir`: `type=str, default=None, help=help, metavar=metavar`
- `--llm-method`: `choices=sorted(SUPPORTED_PROVIDERS), default=None,
  metavar=metavar, help=help`
- `--mcp-config`: `type=str, default=None, help=help`
- `--settings`: `type=str, default=None, help=_SETTINGS_HELP`
- `--execution-dir`: `type=str, default=None, help=_EXECUTION_DIR_HELP`

Then in `parsers.py` / `gh_parsers.py`, replace the inline `add_argument` blocks
with helper calls. Add `from .shared_args import (...)` to `parsers.py` and
`from .shared_args import add_project_dir_arg` to `gh_parsers.py`.

Per-command wiring (which helpers + overrides):

| Command (parser) | project-dir | llm-method | mcp-config | settings | execution-dir |
|---|---|---|---|---|---|
| `prompt` | default | yes | default | yes | yes |
| `commit auto` | default | yes | — | — | yes |
| `implement` | default | yes | default | yes | yes |
| `create-plan` | default | yes | default | yes | yes |
| `create-pr` | default | yes | default | yes | yes |
| `verify` | default | yes | **override** | yes | — |
| `check branch-status` | default | yes | default | yes | yes |
| `check file-size` | default | — | — | — | — |
| `icoder` | default | yes | default | yes | yes |
| `init` | **override** | — | — | — | — |
| `gh-tool get-base-branch` | default | — | — | — | — |
| `gh-tool define-labels` | **override** | — | — | — | — |
| `gh-tool issue-stats` | **override** + `metavar="PATH"` | — | — | — | — |
| `gh-tool checkout-issue-branch` | default | — | — | — | — |
| `gh-tool set-status` | default | — | — | — | — |
| `git-tool compact-diff` | default | — | — | — | — |

Overrides:
- `init`: `add_project_dir_arg(p, help="Target project directory (default: current directory)")`
- `issue-stats`: `add_project_dir_arg(p, help="Project directory. Default: current directory", metavar="PATH")`
- `define-labels`: `add_project_dir_arg(p, help="Project directory. Default: current directory")`
- `verify`: `add_mcp_config_arg(p, help="Path to .mcp.json for MCP agent smoke test")`

Leave untouched: `define-labels --config`, all `check`-specific flags, every
command-specific flag, and `allow_abbrev` (stays ON).

## ALGORITHM

None beyond one `add_argument` per helper — deliberately trivial (KISS).

## DATA

Helpers return `None` (mutate the parser in place), matching the existing
`add_*_parser` style. All resulting `args` attributes (`project_dir`,
`llm_method`, `mcp_config`, `settings`, `execution_dir`) keep the same names,
defaults (`None`), and `--llm-method` choices.

## TDD — write tests first (`tests/cli/test_shared_args.py`)

Build a bare parser per test, apply a helper, then assert via `parse_args`
and/or `format_help()`:

1. `add_project_dir_arg` → `args.project_dir is None` default; canonical help
   substring in `format_help()`; override string honored; `metavar="PATH"`
   honored.
2. `add_llm_method_arg` → default `None`; valid provider parses; invalid exits
   (SystemExit); `METHOD` appears in help.
3. `add_mcp_config_arg` → default `None`; canonical + override wording.
4. `add_settings_arg` / `add_execution_dir_arg` → default `None`; canonical
   wording present.
5. Integration guard (uses full `create_parser()`): every parser that owns
   `--llm-method` shows `METHOD` in its `format_help()` — enumerate
   `prompt`, `commit auto`, `implement`, `create-plan`, `create-pr`, `verify`,
   `check branch-status`, `icoder`.

Existing `tests/cli/test_main.py` and `tests/cli/test_parsers.py` must remain
green unchanged (parsed values are unaffected by this step).

## Checks

Run and pass: `run_pylint_check`, `run_mypy_check`,
`run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not
claude_cli_integration and not claude_api_integration and not
formatter_integration and not github_integration and not langchain_integration"])`.
Note: `help` is a builtin-shadowing kwarg name; it matches argparse's own API, so
keep it (add `# pylint: disable=redefined-builtin` on the helper defs if pylint
flags `W0622`).

## LLM prompt for this step

> Implement **Step 1** of `pr_info/steps/summary.md` (see
> `pr_info/steps/step_1.md`). Using the MCP workspace tools, create
> `src/mcp_coder/cli/shared_args.py` with the five per-flag helpers and canonical
> wording constants exactly as specified, then refactor
> `src/mcp_coder/cli/parsers.py` and `src/mcp_coder/cli/gh_parsers.py` to call
> them per the wiring table (including the `init`, `issue-stats`, `define-labels`,
> and `verify` overrides and `metavar="METHOD"` everywhere). Follow TDD: write
> `tests/cli/test_shared_args.py` first. Do not change parsed values, defaults, or
> choices — only `--help` text/metavar. Do not touch `main.py`. Run
> `run_pylint_check`, `run_pytest_check` (with `-n auto` and the fast-exclusion
> markers), and `run_mypy_check`; fix everything until all pass. One commit.
