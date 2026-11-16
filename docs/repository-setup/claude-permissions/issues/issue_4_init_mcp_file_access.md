# feat(init): create .mcp-file-access; gitignore .scratch/

`mcp-coder init` creates the `.mcp-file-access` rules file, and `.scratch/` becomes gitignored once `verify` respects that file.

## Dependencies / references

- **Read first:** `docs/repository-setup/claude-permissions/implementation.md` §3.2 FU10, FU11; `tool-inventory.md` (`.mcp-file-access` facts)
- This repo's `.mcp-file-access` (template for the rules)
- mcp-workspace docs: `docs/file-access.md` (reference project `mcp-workspace`)
- Part B needs a mcp-workspace version with `.mcp-file-access` support on Jenkins and in sibling repos

## Tasks

### A — init (FU10)
- [ ] `cli/commands/init.py`: create `.mcp-file-access` if missing, with the rules of this repo's file
- [ ] If it exists: append each missing rule; leave existing rules untouched (idempotent, like `update_gitignore`)
- [ ] Same for `vscodeclaude` session folders if `init` isn't run there (`workflows/vscodeclaude/workspace.py`)
- [ ] Tests: new file, existing file with/without the rules, second run = no change

### B — gitignore `.scratch/` (FU11)
- [ ] Precondition checked: mcp-workspace with `.mcp-file-access` on Jenkins and in the tool env
- [ ] `cli/commands/verify.py`: the MCP edit smoke test must not skip when `.scratch/` is gitignored but exposed by `.mcp-file-access`
- [ ] Add `.scratch/` to `.gitignore` (and to `init`'s `update_gitignore`)
- [ ] CLAUDE.md: update the `git_commit` note and "Scratch probes" (no longer "not gitignored")
- [ ] Keep CI `check_forbidden_folder .scratch` as a backstop
- [ ] Tests for the `verify` change

### Docs
- [ ] `implementation.md`: mark FU10, FU11 done

## Acceptance

- [ ] `mcp-coder init` twice → second run changes nothing
- [ ] `mcp-coder verify` runs the smoke test with `.scratch/` gitignored
- [ ] MCP `save_file` to `.scratch/x` works; `git status` doesn't show `.scratch/`
- [ ] pylint, pytest, mypy pass
