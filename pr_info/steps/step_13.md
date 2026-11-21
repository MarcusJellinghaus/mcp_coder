# Step 13 — Docs: install pages and remaining mentions (Scope 8)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_13.md`).
> Implement Step 13 only: documentation sweep. Every page that says
> mcp-tools-py installs with mcp-coder, shows `pip install mcp-coder` for a
> Python repo, describes `check_type_hints`, the template probe or the
> launchers' mcp-tools-py check, gets updated. Run the fast pytest set. One commit.

## WHERE / WHAT

Search first: `search_files` for `pip install mcp-coder`, `check_type_hints`,
`mcp-tools-py`, `DEFAULT_TEST_COMMAND` over `*.md` (and `docs/**`).

- `README.md` (~line 67): Python repos `pip install "mcp-coder[python]"`.
- `docs/getting-started/installation.md` (~lines 11, 20, 44): same; explain
  that non-Python repos don't need the extra.
- `docs/environments/environments.md`: mcp-tools-py comes with the `python`
  extra, not with mcp-coder.
- `docs/configuration/config.md`:
  - line ~25: drop the `[tool.mcp-coder.implement]` / `check_type_hints` mention;
  - line ~986: the template no longer probes mcp-tools-py; Windows runs
    `mcp-coder verify --project-dir %WORKSPACE%\repo`.
- `docs/configuration/optional-dependencies.md`: add a `python` row
  (`mcp-tools-py`; needed for `toolkit = "mcp-tools-py"`; included in `dev`).
- `docs/repository-setup/python.md`:
  - `toolkit` default → "required";
  - remove the "`mcp-coder verify` shows the resolved steps" claim (Formatter
    row is gone; `verify` shows the toolkit's `formatter` / tool items);
  - the `check_type_hints` row (~line 22) → retired; bindings are the switch.
- `docs/repository-setup/` pages describing the launchers' mcp-tools-py check:
  missing mcp-tools-py now warns and continues.
- Install docs (where `mcp-coder install` / `--extras` are described): Python
  repos keep mcp-tools-py through `dev` → `python`. `--extras ""` omits
  mcp-tools-py only with `--source pypi`, with `--skip-overrides`, or when the
  repo's `[tool.mcp-coder.install-from-github] packages` doesn't list it;
  `--source git` / `local` install those packages whatever the extras.
  Document this for non-Python repos.
- `mlflow-integration.md` / other `pip install mcp-coder[...]` lines for other
  extras stay.

## HOW / ALGORITHM / DATA

Markdown edits only.

## Done when

Install docs show `mcp-coder[python]` for Python repos; no doc describes
`check_type_hints` as a live setting, the template probe, or mcp-tools-py as
installed with mcp-coder.
