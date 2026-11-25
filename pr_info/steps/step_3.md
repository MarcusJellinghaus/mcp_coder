# Step 3 — `repository-setup/README.md`: non-Python section, `verify` text, final sweep

## LLM prompt

> Read `pr_info/steps/summary.md`, then this file. Implement Step 3 only:
> - fix the stale statements in `docs/repository-setup/README.md`;
> - add the `## Non-Python Repos` section;
> - run the final anchor and phrase sweep over `docs/` and the root `README.md`.
>
> Docs only. Run the full checks at the end, then make one commit.

## WHERE

- Modify `docs/repository-setup/README.md`.
- Sources:
  - `src/mcp_coder/cli/commands/verify_sections.py::_print_project_section`
    (row order)
  - `verify_toolkit_rows.py` (the Toolkit row label)
  - `cli/commands/init.py` (links `#adapting-deployed-files-non-python-repos`)

## WHAT

1. **The top non-Python paragraph** ("Non-Python repos: use a root
   `mcp-coder.toml`…") moves into the new section below. Delete it from the
   Overview.
2. **New `## Non-Python Repos`,** directly after `## Quick Setup Checklist`.
   Five short bullets, each one or two sentences plus a link:
   - **Config.** A root `mcp-coder.toml` with the `command` toolkit
     ([Command toolkit](../configuration/toolkits.md#command-toolkit)) and
     `[tool.mcp-coder.setup]` ([Project setup](../configuration/setup.md)).
     All keys: [Project config](../configuration/project-config.md).
   - **`verify` PROJECT rows** for a repo with only `mcp-coder.toml`, in order:
     - `Project config` (`[OK] mcp-coder.toml`; `[WARN] none` only without any
       project config file);
     - `.mcp-file-access`;
     - `format_code`;
     - `Toolkit` naming its source (e.g. `command (mcp-coder.toml)`) with its
       action groups;
     - `Setup`, with a sub-row per unresolved step
       ([Check the config](../configuration/setup.md#check-the-config));
     - the key-warning rows labelled with the file.

     The `legacy format_code` and `check_type_hints` rows don't appear: they
     read `pyproject.toml` only. Check the order and the labels against
     `_print_project_section` and `toolkit_rows`.
   - **Setup commands** must be lockfile-frozen:
     [Changed files](../configuration/setup.md#changed-files).
   - **Exit codes.** `npm run` passes a script's exit code on unchanged, also
     across `&&`. Tools that exit with a count need a range:
     [`exit_codes`](../configuration/toolkits.md#defaults) and the
     dependency-cruiser note in
     [Step fields](../configuration/toolkits.md#step-fields).
   - **JUnit reports:** [npm example](../configuration/toolkits.md#npm).
3. **`## Adapting Deployed Files (Non-Python Repos)` → `###` under
   `## Non-Python Repos`.** Keep the heading text unchanged, so the anchor
   `#adapting-deployed-files-non-python-repos` stays. The content is
   unchanged; it is the fifth item ("adapting the deployed skills").
4. **Files Shared table, `mcp-coder.toml` row.** "Not in this repo; any repo
   may keep `toolkit`, `setup`, `format_code` and `prompts` here (only
   `install` / `install-from-github` are `pyproject.toml`-only). Templates: …".
   Keep the existing template links.
5. **Testing Your Setup, step 0.** "It checks your `config.toml` (including
   unknown keys), the project config (`[tool.mcp-coder]` keys, toolkit, setup),
   git, GitHub, …". Keep the rest of the sentence.
6. **Leave the clean-tree ignore list unchanged.** Add nothing about it beyond
   the `reports/` note already in `toolkits.md#npm`.

## ALGORITHM (final sweep, whole change)

```
for phrase in ["two separate configuration files", "Union of all `Bash(...)` grants",
               "non-Python repos only", "every config key"]:
    search_files(pattern=phrase, glob="**/*.md") -> expect no hits in docs/ or README.md
for anchor in ["prompt-configuration", "key-sections", "environment-variable-overrides",
               "adapting-deployed-files-non-python-repos", "target-repo-contracts",
               "step-to-request-table", "configure-a-toolkit", "toolmcp-codertoolkit",
               "check-the-config", "changed-files",
               # project-config.md anchors this PR creates
               "prompts", "checked-by-verify", "retired-keys",
               # toolkits.md anchors the Non-Python section links to
               "npm", "defaults", "step-fields", "mcp-tools-py"]:
    search_files(pattern=anchor) -> each link's target heading exists with that slug
```

Fix any link that misses its target.

## DATA

None (docs only).

## Checks, then commit

- `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not setup_integration and not textual_integration"])`
- `run_pylint_check`, `run_mypy_check`
- `run_format_code`, then `git_commit` with
  `paths=["docs/repository-setup/README.md"]`, plus any file the sweep fixed.
  Message: `docs: add non-Python repos section, fix repository-setup verify text (#1453)`.
