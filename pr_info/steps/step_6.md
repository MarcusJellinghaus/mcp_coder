# Step 6 — Documentation

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md` only.
> Docs only. Keep additions short and in the style of the surrounding text. Run the
> fast unit pytest set (some tests check docs). Run the formatter, then make one commit.

## WHERE / WHAT
- `docs/configuration/config.md`
  - In the "Configuring Your Project for Automated Workflows" example (around lines 882–895),
    add `post_install_checks` to the `[tool.mcp-coder.install]` TOML block, with one
    sentence: install runs each argv after provisioning (venv bin dir first, then
    `PATH`; cwd = the project); any failure fails the install; nothing runs when the key is absent.
  - Line 23 table: add `post-install checks (`[tool.mcp-coder.install]`)` to the
    `pyproject.toml` row.
- `docs/cli-reference.md` `### install` (around line 125): one bullet or paragraph saying that
  declared `post_install_checks` run after the version report; failure → exit 1;
  `--check` only prints them.
- `docs/repository-setup/README.md` "Target-Repo Contracts":
  - intro line 97: "checks all four rows" → "checks all five rows"
  - new row: `| post-install checks | `[tool.mcp-coder.install] post_install_checks`, optional | install exits 1; malformed value warned at launch |`
- `docs/repository-setup/python.md` "Key Sections" table (around line 25): add a row
  `| `[tool.mcp-coder.install]` | mcp-coder install process (`pyproject_config.py`) | `extras`, `post_install_checks` |`
- `docs/architecture/architecture.md`
  - line 260: "the five phases: venv, pip+uv bootstrap, main install, GitHub overrides, version report"
    → "the six phases: …, version report, post-install checks"
  - line 261: add `tests/install/test_install_post_checks.py` to the test list.

## HOW / ALGORITHM / DATA
None. This step is text only.
