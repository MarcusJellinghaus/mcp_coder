# Step 2: src/ W0612 — unused variables (5 occurrences)

## Goal
Fix unused variables in `src/`. Replace with `_` or remove `as e` where unused.

## WHERE — Files Modified

- `src/mcp_coder/prompt_manager.py` line 565 — change `except Exception as e:` to `except Exception:` (variable `e` unused)
- `src/mcp_coder/checks/branch_status.py` line 192 — remove local `logger = ...` reassignment (shadows module logger)
- `src/mcp_coder/cli/commands/check_branch_status.py` line 347 — change `ci_status = ...` to `_ = ...` or call without assigning
- `src/mcp_coder/llm/providers/claude/claude_cli_verification.py` line 45 — change `claude_path, ...` unpack to `_, ...`
- `src/mcp_coder/utils/git_operations/readers.py` line 117 — change `index_status = ...` to `_ = ...`

## WHAT

- `except Exception as e:` to `except Exception:` (when `e` is unused)
- `varname = expr` to `_ = expr` (when result is discarded)

## ALGORITHM

```
For each W0612 location:
    If `except Exception as e:` with unused `e` -> remove `as e`
    If `varname = result` where result unused -> `_ = result`
```

## DATA

Pylint count reduced by: **5 warnings**.

## TDD Note

Run existing tests after changes to confirm nothing broken.

---

## LLM Prompt

```
Please implement Step 2: fix W0612 (unused variables) in src/.
See pr_info/steps/step_2.md for exact locations.
Rules: replace unused vars with _, remove unused `as e`. No logic changes.
Run pylint, pytest (fast unit tests), and mypy to verify.
```
