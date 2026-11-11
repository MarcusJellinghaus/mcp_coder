# Summary: Reference docs for the toolkit configuration and interface (#1200)

## Goal

The toolkit spec lives in epic #1192 and its amendment comments, which no longer
match the code. Replace it with two maintained repo pages that describe what
exists today, and point the existing docs at them. #1199's "no toolkit" error
will link to `docs/configuration/toolkits.md#configure-a-toolkit`.

**Docs only. No code, test or config change.**

## Ground rules (apply to every step)

- **The code is the source of truth.** Every symbol, default and number cited
  must exist in the named source file. Facts about Claude Code itself are linked
  to Claude Code's docs, not stated as numbers.
  - mcp-coder: read with `mcp__mcp-workspace__read_file` / `search_files`.
  - mcp-tools-py and mcp-coder-utils: read the **installed** version with
    `mcp__mcp-tools-py__get_library_source` / `search_library_files` (scope
    `mcp_tools_py` or `mcp_coder_utils`). Cite file names, never line numbers.
- **When this plan and the code disagree, document the code** and add one line
  per discrepancy to the commit message body (write it in
  `pr_info/.commit_message.txt`), so it can be carried into the PR description.
- **State each fact once.** `toolkits.md` owns the config, bindings, mcp-tools-py
  settings and the transitional section; other pages link to it. Do not
  duplicate existing homes: behaviour changes stay in
  `docs/migration/multi-language.md`, custom prompt slots in
  `docs/repository-setup/python.md`, the toolkit contract in the mcp-coder-utils
  README (except how mcp-coder uses the fragments, stated in
  `toolkit-interface.md`).
- **Wording in the two new pages:** no "proposed"; "planned" and "#1199" only in
  the transitional section of `toolkits.md`; no "will be", "until" or
  issue-number notes elsewhere. Only exception: the authoring guide's opening
  line pointing to #1194.
- **Cross-repo links** are absolute GitHub URLs on `main`.
- **mcp-tools-py is still required** (install, `MCP_SERVER_NAMES`, launch
  scripts, the unconfigured fallback). Pages call it one toolkit without
  contradicting that; the transitional section carries the facts.
- Match the repo's docs style: short clauses, tables over prose, no filler.
- Keep each file under the repo limit (`mcp__mcp-workspace__check_file_size`,
  750 lines).

## Architectural / design changes

None in code. The documentation architecture changes:

| Before | After |
|---|---|
| Toolkit spec only in epic #1192 (outdated) | `docs/configuration/toolkits.md`: user-facing configuration reference |
| `docs/configuration/command-toolkit.md` as a standalone page | Folded into `toolkits.md` under `## Command toolkit`; old page deleted |
| No description of mcp-coder's side of the toolkit interface | `docs/architecture/toolkit-interface.md`: what mcp-coder does with a toolkit, plus a first-party authoring guide; the contract itself stays linked in mcp-coder-utils |
| README, architecture and process docs describe Python / mcp-tools-py as the only path | Scoped to the Python toolkit; the `command` toolkit (`Bash(...)` grants) named; every setup path links `toolkits.md` |
| Facts that change with #1199 scattered | One transitional section in `toolkits.md` ("Today" vs "Planned (#1199)"); #1199 replaces it |

Stable anchors created for other issues: `toolkits.md#configure-a-toolkit`
(#1199's error message) and `toolkits.md#command-toolkit` (#1198's template).

## Files

| File | Change | Step |
|---|---|---|
| `docs/configuration/toolkits.md` | **create** | 1 |
| `docs/configuration/command-toolkit.md` | **delete** (content folded into `toolkits.md`) | 1 |
| `docs/README.md` | replace the Command Toolkit entry with `toolkits.md` (step 1); add `toolkit-interface.md` (step 2) | 1, 2 |
| `docs/architecture/toolkit-interface.md` | **create** | 2 |
| `README.md` | modify | 3 |
| `docs/architecture/architecture.md` | modify | 3 |
| `docs/repository-setup/python.md` | modify (one link) | 3 |
| `docs/configuration/config.md` | modify (one link, one scoped sentence) | 3 |
| `docs/repository-setup/README.md` | modify | 3 |
| `docs/processes-prompts/processes/05-implementation.md` | modify | 3 |
| `docs/migration/multi-language.md` | modify (one link) | 3 |

No change (checked): `docs/configuration/claude-code.md`,
`docs/getting-started/installation.md`, `docs/environments/environments.md`,
`docs/repository-setup/claude-code.md`. No folders or Python modules are
created or modified.

## Steps

1. `toolkits.md`: write it, fold in and delete `command-toolkit.md`, update the
   `docs/README.md` entry.
2. `toolkit-interface.md`: write it, add it to `docs/README.md`.
3. Existing docs: the Scope 3 edits, then the final "Done when" checks.

## Testing approach

TDD does not apply: there is no code to test. Each step replaces tests with
checkable verification (`search_files` for required headings, forbidden words
and dead links; `check_file_size`; every cited fact re-read from its source).
The standard checks (pylint, pytest, mypy) still run in each step to confirm
nothing else changed.

## Done when (whole issue)

- `docs/configuration/toolkits.md` and `docs/architecture/toolkit-interface.md`
  exist; every symbol, default and number they cite exists in the named source
  file.
- No "proposed" in either page; "planned" and "#1199" only in the transitional
  section of `toolkits.md`.
- `docs/configuration/command-toolkit.md` is deleted and no file outside
  `pr_info/` contains `command-toolkit.md`.
- `toolkits.md` has the headings `## Configure a toolkit` and `## Command toolkit`.
- The Scope 3 edits are made; `docs/README.md` lists both pages.
- `check_file_size` passes.
