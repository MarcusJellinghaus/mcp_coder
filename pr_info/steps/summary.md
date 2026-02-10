# Issue #425: Fix .vscodeclaude_status Extension Regression

## Summary

PR #409 correctly changed `.vscodeclaude_status.md` to `.vscodeclaude_status.txt`, but PR #420 accidentally reverted this change because the branch was based on a pre-#409 commit.

This fix restores the `.txt` extension by performing a global find-and-replace across the affected files.

## Architectural / Design Changes

**None.** This is a pure string replacement fix with no architectural or design changes. The file extension was already intended to be `.txt` (as documented in `docs/coordinator-vscodeclaude.md`).

## Change Summary

| Change Type | Description |
|-------------|-------------|
| String replacement | `.vscodeclaude_status.md` → `.vscodeclaude_status.txt` |
| Files affected | 5 files (2 source, 3 test) |
| Logic changes | None |
| New features | None |

## Files to Modify

### Source Files
| File | Changes |
|------|---------|
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | 2 occurrences |
| `src/mcp_coder/workflows/vscodeclaude/templates.py` | 2 occurrences |

### Test Files
| File | Changes |
|------|---------|
| `tests/workflows/vscodeclaude/test_workspace.py` | Multiple assertions |
| `tests/workflows/vscodeclaude/test_orchestrator_regenerate.py` | Status file path assertions |
| `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` | Template content assertions |

## Out of Scope

Per issue requirements:
- Smarter gitignore handling - separate issue
- Backward compatibility for `.md` entries - not needed
- The `uv sync --extra dev` change in PR #420 - intentional, should remain

## Verification

Run affected tests:
```bash
pytest tests/workflows/vscodeclaude/test_workspace.py tests/workflows/vscodeclaude/test_orchestrator_regenerate.py tests/cli/commands/coordinator/test_vscodeclaude_cli.py -v
```
