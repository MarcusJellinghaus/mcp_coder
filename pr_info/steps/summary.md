# Issue #90 — CLI help single-source + DRY shared flags

## Goal

Kill two copy-paste sources of truth in the CLI:

1. **Command descriptions** are typed twice — once in each subparser's `help=`
   (`cli/parsers.py`, `cli/gh_parsers.py`) and again in the hand-written
   categorized overview (`cli/commands/help.py`). They have drifted, and
   `gh-tool checkout-issue-branch` is missing from the overview entirely.
2. **Shared flags** (`--project-dir`, `--llm-method`, `--mcp-config`,
   `--settings`, `--execution-dir`) are re-declared ~13× with unintentional
   wording/`metavar` drift.

All requirements of #90 are preserved. The three *original* complaints in the
issue are already fixed in the current code and need no action.

## Design decision: simpler than the issue's proposed mechanism

The issue proposes deriving overview descriptions by **introspecting the live
parser tree at render time** (a `_SubParsersAction` wrapper that captures
`(name, help=)`, threaded through two nesting levels), and — because that makes
`help.py` depend on the parser tree — **relocating `create_parser()` into a new
`cli/parser_factory.py`** to break a `help.py ↔ main.py` import cycle.

We achieve the same **requirements** with less machinery by exploiting a fact the
issue itself establishes: after the settled wording edits, **every leaf's
`help=` is exactly equal to its overview description**. So instead of two strings
kept in sync by capture, we use **one shared string**:

- A single `COMMAND_DESCRIPTIONS: dict[str, str]` (display-name → canonical
  wording) lives in the dependency-free module `cli/command_catalog.py`.
- Each subparser passes `help=COMMAND_DESCRIPTIONS["<name>"]` — same object, so
  drift is structurally impossible (identical guarantee to register-time
  capture).
- The overview renders from `COMMAND_DESCRIPTIONS` + a centralized ordered
  `COMMAND_CATEGORIES` map. It does **not** touch the parser tree.

Consequences (all net simplifications, requirements intact):

| Issue's mechanism | This design |
|---|---|
| `_SubParsersAction` wrapper, two-level threading, `prog`-prefix stripping, per-call idempotent registry | **Not needed** — no render-time introspection |
| `help.py → parser tree → import cycle` | **No cycle** — renderer has no parser dependency |
| Relocate `create_parser()` to new `cli/parser_factory.py`; re-export from `main.py`; churn ~20 test imports/patches | **`create_parser()` stays in `main.py`; `main.py` untouched** |

The tree-walk that the issue wanted in production is moved to where it belongs:
the **anti-drift test**, which may freely import both `create_parser` and
`get_help_text` (test code, no cycle).

### Requirements preserved

- Single source of truth for descriptions; cannot drift. ✔
- `gh-tool checkout-issue-branch` now shown. ✔
- Category membership + intra-category order are centralized and declarative
  (the settled TOOLS re-sort). ✔
- Anti-drift **test** asserts every non-group/non-suppressed leaf appears in
  `get_help_text()` and each shown description equals the parser's `help=`. ✔
- `get_help_text()` stays no-arg. ✔ Dead `Category.description` removed. ✔
- Shared flags DRY'd via opt-in per-flag helpers with per-call overrides. ✔
- Canonical wording; `metavar="METHOD"` on all `--llm-method`; `verify`
  `--mcp-config` override; `create-plan` detail → `--help` epilog. ✔
- `allow_abbrev` left ON; `define-labels --config` / `check`-specific flags left
  alone (out of scope). ✔

### Dependency direction note

The two catalog constants (`COMMAND_DESCRIPTIONS`, `COMMAND_CATEGORIES`) live in
a **dependency-free** module `cli/command_catalog.py` that imports nothing from
within `mcp_coder.cli` (only stdlib/typing). `parsers.py` / `gh_parsers.py`
import `COMMAND_DESCRIPTIONS` from `cli/command_catalog.py`, and
`cli/commands/help.py` imports both constants from there to render the overview.
Because the catalog is dependency-free there is **no coupling to the heavy
`commands` package** and no import cycle, so a module-level import in the parsers
is safe. `.importlinter` only constrains cross-top-package imports (`cli` vs
`workflows` …), so an intra-`cli` import is unaffected; `tach` will be verified
during implementation.

## Settled command descriptions (canonical `help=` == overview text)

**SETUP**: `init`, `verify`
**BACKGROUND DEVELOPMENT**: `create-plan`, `implement`, `create-pr`,
`coordinator`
**INTERACTIVE DEVELOPMENT**: `icoder`, `vscodeclaude launch`,
`vscodeclaude status`
**TOOLS** (re-sorted: families contiguous, gh-tool in lifecycle order):
`prompt`, `commit auto`, `check branch-status`, `check file-size`,
`gh-tool checkout-issue-branch`, `gh-tool set-status`,
`gh-tool get-base-branch`, `gh-tool define-labels`, `gh-tool issue-stats`,
`git-tool compact-diff`

| Command | Description |
|---|---|
| `init` | Initialize project: create config and deploy Claude skills |
| `verify` | Verify CLI installation, LLM provider, and MLflow configuration |
| `create-plan` | Generate implementation plan for a GitHub issue |
| `implement` | Execute implementation workflow |
| `create-pr` | Create pull request with AI-generated summary |
| `coordinator` | Monitor GitHub issues and dispatch automated workflows |
| `icoder` | Interactive terminal chat for LLM-assisted coding |
| `vscodeclaude launch` | Launch VSCode/Claude session for issues |
| `vscodeclaude status` | Show current VSCode/Claude sessions |
| `prompt` | Send prompt to configured LLM |
| `commit auto` | Auto-generate commit message using LLM |
| `check branch-status` | Check branch readiness status and optionally apply fixes |
| `check file-size` | Check file sizes against maximum line count |
| `gh-tool checkout-issue-branch` | Checkout or create a branch linked to a GitHub issue |
| `gh-tool set-status` | Update GitHub issue workflow status label |
| `gh-tool get-base-branch` | Detect base branch for current feature branch |
| `gh-tool define-labels` | Sync workflow status labels to GitHub |
| `gh-tool issue-stats` | Display issue statistics by workflow status |
| `git-tool compact-diff` | Generate compact git diff suppressing moved-code blocks |

`create-plan` epilog gains: *"Sets failure labels and posts comments on error."*

## Canonical shared-flag wording

- `--project-dir` (default): `Project directory: where source code lives (git
  operations, file modifications). Default: current directory`
  - `init` override: `Target project directory (default: current directory)`
  - `issue-stats` / `define-labels` override: `Project directory. Default:
    current directory` (issue-stats keeps `metavar="PATH"`)
- `--llm-method`: `LLM method override. If omitted, uses config
  default_provider or claude` + `metavar="METHOD"` on **all** parsers
- `--mcp-config` (default): `Path to MCP configuration file (e.g.,
  .mcp.linux.json)`
  - `verify` override: `Path to .mcp.json for MCP agent smoke test`
- `--settings`: `Path to Claude Code settings file
  (.claude/settings.local.json). Auto-detected from <project_dir>/.claude/ if
  omitted. Overrides Claude's cwd-based settings discovery.`
- `--execution-dir`: `Execution directory: where Claude subprocess runs (config
  discovery). Default: current directory`

## Files created / modified

**Created**
- `src/mcp_coder/cli/shared_args.py` — five per-flag helpers (Step 1)
- `src/mcp_coder/cli/command_catalog.py` — dependency-free `COMMAND_DESCRIPTIONS`
  + centralized ordered `COMMAND_CATEGORIES` catalog (Step 2)
- `tests/cli/test_shared_args.py` — helper + wiring assertions (Step 1)
- `tests/cli/test_help_anti_drift.py` — anti-drift lock (Step 3)
- `pr_info/steps/summary.md`, `step_1.md`, `step_2.md`, `step_3.md`

**Modified**
- `src/mcp_coder/cli/parsers.py` — flags via helpers (Step 1); leaf `help=` →
  `COMMAND_DESCRIPTIONS` (imported from `command_catalog.py`), canonical wording,
  create-plan epilog (Step 2)
- `src/mcp_coder/cli/gh_parsers.py` — same (Steps 1 & 2)
- `src/mcp_coder/cli/commands/help.py` — import `COMMAND_DESCRIPTIONS` +
  `COMMAND_CATEGORIES` from `command_catalog.py`, render from them (owns the
  rendering logic + `get_help_text()`), drop `Category`/`Command` NamedTuples +
  `Category.description` (Step 2)
- `tests/cli/commands/test_help.py` — rewritten for new shape (Step 2)

**Explicitly NOT modified**
- `src/mcp_coder/cli/main.py` — `create_parser()` and `get_help_text()` routing
  unchanged; no `parser_factory.py` created.

## Step overview

1. **Step 1** — DRY shared flags: new `cli/shared_args.py` + wire all parsers.
2. **Step 2** — Single-source descriptions: catalog constants in new
   dependency-free `command_catalog.py`, render `help.py` from them, point leaf
   `help=` at the dict, wording edits + epilog.
3. **Step 3** — Anti-drift test locking parity + full-coverage.

Each step = exactly one commit (tests + implementation + `pylint`/`pytest`/`mypy`
passing).
