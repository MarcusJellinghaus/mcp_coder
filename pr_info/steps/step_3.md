# Step 3: Point the existing docs at the toolkit pages; final checks

## LLM prompt

> Read `pr_info/steps/summary.md` (ground rules, files, Done-when) and this file,
> `pr_info/steps/step_3.md`. Implement Step 3 only: make the edits listed below
> to seven existing docs so they link `docs/configuration/toolkits.md` /
> `docs/architecture/toolkit-interface.md` and no longer claim Python or
> mcp-tools-py is the only path. Keep each edit minimal: change or add the
> sentence named, don't rewrite surrounding text, don't repeat facts the new
> pages own (link them). Docs only — do not change code. Then run the whole-issue
> "Done when" checks below, then pylint, pytest and mypy, and produce exactly one
> commit.

## WHERE / WHAT — edits per file

Relative link prefixes: from repo root `docs/configuration/toolkits.md`; from
`docs/architecture/` `../configuration/toolkits.md`; from
`docs/configuration/` `toolkits.md`; from `docs/repository-setup/` and
`docs/migration/` `../configuration/toolkits.md`; from
`docs/processes-prompts/processes/` `../../configuration/toolkits.md`.

**`README.md`**
1. "Quality gates on every step" bullet: drop "mcp-coder re-checks mypy itself
   once all steps are done" and replace "pylint, mypy and pytest run after each
   implementation step" with: the LLM is told to run the project's checks, and
   mcp-coder runs the configured toolkit's checks and tests after each step and
   as a final gate. Keep "every plan step carries its own tests…".
2. "The LLM reaches files, git, GitHub and the quality checks only through
   [MCP] servers (…)" bullet: files, git and GitHub through `mcp-workspace`;
   quality checks through the configured toolkit — `mcp-tools-py` is the Python
   toolkit's MCP server, the `command` toolkit grants exact `Bash(...)`
   commands. Keep the `.mcp.json` part and link `docs/configuration/toolkits.md`.
3. Status table: Experimental row adds "other stacks via the `command` toolkit;
   project setup still assumes Python"; Planned row keeps only "general LLM support".
4. Paragraph below the table: "Python is the supported target for now because
   `implement`, the installer and the architecture checks call Python tools" →
   name what still assumes Python: the installer and project setup. Drop
   `implement` and "the architecture checks".
5. "Set up a repository (once)": add a step before "Check it all with
   `mcp-coder verify`": configure a toolkit in `pyproject.toml` (or
   `mcp-coder.toml`), linking `docs/configuration/toolkits.md#configure-a-toolkit`.
6. Related projects: mcp-tools-py line framed as the Python toolkit and its MCP
   server (quality checks, formatting); mcp-coder-utils line adds "and the
   toolkit contract".

**`docs/architecture/architecture.md`**
1. §1 (line ~9) and §2 "Target repos are Python projects for now…" bullet:
   scope Python statements to the Python toolkit; the LLM gets quality checks
   through mcp-tools-py only with the Python toolkit, the `command` toolkit uses
   `Bash(...)` grants. Keep that the installer provisions a Python venv.
   In §1 (architecture.md:9), drop or rescope "the installer and architecture
   enforcement assume a Python target repo" the same way README edit 4 does:
   architecture checks run only through `PythonToolkit`'s `check@full`, so only
   the installer (and project setup) still assume Python. The two pages must not
   contradict each other.
2. §2 shims bullet ("code-quality tools come from `mcp-tools-py`"): quality
   tools are reached through the configured toolkit; mcp-coder-utils adds the
   toolkit contract.
3. §3: "MCP servers give the LLM file access and quality checks" and "Target
   repos are the (currently Python) repositories" — scope to the Python
   toolkit / name the `command` toolkit's `Bash(...)` grants. The context
   diagram may stay.
4. §4 "Orchestrator vs. worker": link "the bindings of the configured toolkit"
   to `../configuration/toolkits.md#bindings`; "The LLM also runs pylint, pytest
   and mypy during each task" → "The LLM also runs the toolkit's checks during
   each task, as its prompt tells it to." Replace the clause
   "(`[tool.mcp-coder.implement] check_type_hints = false` drops their
   `check@*` requests)" with a link to
   `../configuration/toolkits.md#until-the-next-breaking-release`; don't
   restate the fact.
5. §5 building blocks table: add a row `toolkits` — toolkits shipped with
   mcp-coder (`command`); tach `tools` layer, depends only on `mcp_coder.utils`;
   the `toolkits_isolation` contracts in `.importlinter` forbid core imports;
   core reaches them only through the `mcp_coder.toolkits` entry points. Shims
   row: add `utils/toolkit` (mcp-coder-utils toolkit contract); note
   `mcp_tools_py` only re-exports `resolve_steps`. Verify in `tach.toml`,
   `.importlinter` and `src/mcp_coder/mcp_tools_py.py`.
6. Link both new pages once (e.g. at the end of §4's orchestrator bullet or
   below the §5 table): [toolkits](../configuration/toolkits.md),
   [toolkit interface](toolkit-interface.md).

**`docs/repository-setup/python.md`** — the `[tool.mcp-coder.toolkit]` row in
"Key Sections": link it to `../configuration/toolkits.md`.

**`docs/configuration/config.md`**
1. Line ~25 table row, "toolkit selection (`[tool.mcp-coder.toolkit]` …)": link
   to `toolkits.md`.
2. Line ~27 "The formatter itself is selected by `[tool.mcp-tools-py] formatter`
   …": prefix with "With the Python toolkit (`mcp-tools-py`),"; other toolkits
   format through their own `format` action ([toolkits](toolkits.md)).

**`docs/repository-setup/README.md`**
1. Under "Quick Setup Checklist", add before the `mcp-coder verify` line:
   `- [ ] Configure a toolkit in `[tool.mcp-coder.toolkit]` ([Toolkits](../configuration/toolkits.md#configure-a-toolkit))`.
2. A pointer for non-Python repos (one sentence, e.g. under "Overview" or above
   the Detail table): use a root `mcp-coder.toml` and the `command` toolkit
   ([Command toolkit](../configuration/toolkits.md#command-toolkit)).
3. "Files Shared With Other Projects" table: add a row
   `| `mcp-coder.toml` | G | No | No | Not in this repo; non-Python repos only. Template: [toolkits.md](../configuration/toolkits.md#npm) |`
   (the npm example lives under `## Examples` → `### npm` after Step 1).

**`docs/processes-prompts/processes/05-implementation.md`**
1. Quality gates bullet "All code changes are validated through **pylint** →
   **pytest** → **mypy**, by the LLM and by routine when implementation is
   done." → mcp-coder runs the configured bindings; the LLM runs the toolkit's
   checks.
2. Process bullet ending "Overrides: [migration note](…)": add
   "and [bindings](../../configuration/toolkits.md#bindings)". In the same
   bullet, replace "`[tool.mcp-coder.implement] check_type_hints = false` drops
   the `check@*` requests." with a link to
   `../../configuration/toolkits.md#until-the-next-breaking-release`; don't
   restate the fact.

**`docs/migration/multi-language.md`** — add one line under the title:
"Configuration reference: [toolkits](../configuration/toolkits.md)."

**No change:** `docs/configuration/claude-code.md`,
`docs/getting-started/installation.md`, `docs/environments/environments.md`,
`docs/repository-setup/claude-code.md`.

## HOW

- Use `mcp__mcp-workspace__edit_file` with the exact current sentence as
  `old_string`; read the surrounding lines first.
- Anchors used: `#configure-a-toolkit`, `#command-toolkit`, `#bindings`,
  `#npm`, `#until-the-next-breaking-release` — confirm each heading exists in
  `toolkits.md` (`search_files` for `^##+ `; `#npm` is a `###` heading).

## ALGORITHM

```
for each file in the list: read it, apply its edits with edit_file, re-read the result
confirm every new link target file and anchor heading exists
run the whole-issue Done-when checks below
fix anything that fails; run pylint, pytest, mypy; commit
```

## DATA — verification (replaces tests; whole-issue Done-when)

- `search_files(pattern="command-toolkit\\.md")` → matches only under `pr_info/`.
- `search_files(pattern="toolkits\\.md")` → hits in `README.md`,
  `docs/README.md`, `architecture.md`, `toolkit-interface.md`, `python.md`,
  `config.md`, `repository-setup/README.md`, `05-implementation.md`,
  `multi-language.md`.
- `search_files(glob="README.md", pattern="re-checks mypy|Other programming languages|architecture checks")` → no match.
- `search_files(glob="docs/processes-prompts/processes/05-implementation.md", pattern="\\*\\*pylint\\*\\* →")` → no match.
- `search_files(glob="docs/configuration/toolkits.md", pattern="^## (Configure a toolkit|Command toolkit)$")` → 2 matches.
- `search_files(pattern="(?i)proposed", glob="docs/**/toolkit*.md")` → no match;
  "planned" / "#1199" only in the transitional section of `toolkits.md`.
- `check_file_size` passes.
- pylint, pytest (`-n auto`, fast unit marker filter from CLAUDE.md) and mypy pass.

## Blocked

If `docs/configuration/toolkits.md` or `docs/architecture/toolkit-interface.md`
does not exist (Steps 1–2 not done), write one line to `pr_info/.blocked.txt`
and stop.

## Commit

`docs: link the toolkit pages from existing docs` — body lists any
plan-vs-code discrepancies.
