# chore(permissions): move allows to committed settings.json, untrack settings.local.json

Move this repo's permission allows from the tracked `.claude/settings.local.json` into the committed `.claude/settings.json`, and make `settings.local.json` a gitignored personal file — without breaking Copilot, existing clones or the docs.

## Dependencies / references

- **Depends on:** issue 1 (committed `settings.json` with deny exists)
- **Read first:** `docs/repository-setup/claude-permissions/implementation.md` §2.1 (settings layout), §3.1 T1, F8; §3.2 FU3, FU5, FU6
- Findings from the issue 1 analysis (consumers of `settings.local.json`), below

## Known consumers and risks

| Consumer | Risk when `settings.local.json` is gone |
|---|---|
| `llm/providers/copilot/copilot_cli.py::_read_settings_allow` (also `copilot_cli_streaming.py`) | Reads local only → returns `None` → `build_copilot_command` drops `--available-tools`, keeps `--allow-all-tools`: Copilot sees every tool (FU3) |
| `cli/utils.py::resolve_claude_settings_path` | Falls back to `settings.json` (tested). Unknown: do `settings.json` allows apply in `-p` when a personal local file is passed via `--settings` |
| vscodeclaude session folders, reused Jenkins workspaces | `git pull` fails when Claude has modified the tracked `settings.local.json` ("would be overwritten") |
| `tools/mlflow/_source_transcripts.py::load_allowlist` | Reads both; exact names only |
| `.gitattributes` | `settings.local.json text eol=lf`; nothing for `settings.json` |
| `cli/shared_args.py::_SETTINGS_HELP` (+ `tests/cli/test_shared_args.py`) | Names `settings.local.json`; "overrides cwd discovery" is wrong (F11) |
| Docs | `repository-setup/README.md`, `cli-reference.md`, `configuration/config.md`, `configuration/toolkits.md`, `architecture/toolkit-interface.md`, `environments/environments.md`, `iCoder.md`, `agent-permissions.md`, `.claude/skills/rebase/rebase_design.md`, `claude-code.md`, docstrings |

## Tasks

- [ ] Copilot: read and merge allows from `settings.json` too (FU3); tests
- [ ] Verify in `-p`: `settings.json` allows apply when a personal `settings.local.json` is passed via `--settings`
- [ ] Verify in a fresh clone: `enableAllProjectMcpServers` / `enabledMcpjsonServers` from a committed file don't add an MCP approval prompt
- [ ] Move allows and MCP enablement keys to `settings.json` (exact tool names; drop `Skill(...)` entries of `disable-model-invocation` skills)
- [ ] `settings.local.json`: untrack, gitignore; migration note for existing clones / session folders / Jenkins workspaces
- [ ] `.gitattributes`: add `settings.json`
- [ ] `--settings` help text and its test
- [ ] `mcp-coder init`: deploy a `settings.json` template; gitignore `settings.local.json` (FU5)
- [ ] Docs in the table above (FU6)
- [ ] `implementation.md`: T1, F8, FU3, FU5, FU6

## Acceptance

- [ ] Fresh clone, no local file: interactive and headless runs work without new prompts
- [ ] Copilot sees only the allowed tools
- [ ] A session folder with a modified old `settings.local.json` updates cleanly (per migration note)
- [ ] pylint, pytest, mypy pass
