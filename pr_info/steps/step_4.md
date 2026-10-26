# Step 4 — Move push tests from `test_commit.py` to `test_commit_push.py`

## LLM prompt

> Read `pr_info/steps/summary.md` (hard rules, standard checks) and implement
> `pr_info/steps/step_4.md` exactly. Pure refactoring: move code with `move_symbol` only,
> edit only imports, `.large-files-allowlist` and the `vulture_whitelist.py:136` comment.
> Produce exactly one commit.

## WHERE

- Source: `tests/cli/commands/test_commit.py`
- Destination (new): `tests/cli/commands/test_commit_push.py`
- `.large-files-allowlist`
- `vulture_whitelist.py` (line 136, comment only)

## WHAT

| Symbol | Kind | Tests |
|---|---|---:|
| `MODULE` | constant `"mcp_coder.cli.commands.commit"` (patch-target prefix, used only by the two classes below) | — |
| `TestPushAfterCommit` | class (tests `_push_after_commit`) | 8 |
| `TestCommitAutoPush` | class (`execute_commit_auto` with `push=True/False`) | 4 |

## HOW

- **Two calls, in this order** (`MODULE` must be defined above the classes, whose
  `@patch(f"{MODULE}...")` decorators evaluate at class definition):
  1. `move_symbol(source_file="tests/cli/commands/test_commit.py", symbol_names=["MODULE"], dest_file="tests/cli/commands/test_commit_push.py")` — dry run, then apply.
  2. `move_symbol(source_file="tests/cli/commands/test_commit.py", symbol_names=["TestPushAfterCommit", "TestCommitAutoPush"], dest_file="tests/cli/commands/test_commit_push.py")` — dry run, then apply.
- Check that `MODULE = ...` comes before `class TestPushAfterCommit` in `test_commit_push.py`,
  and that the file does not import from `test_commit`. Otherwise write one line to
  `pr_info/.blocked.txt` and stop. Do not reorder by hand.
- Expected imports afterwards:
  - `test_commit.py`: `argparse`, `logging`, `Path`, `Mock`, `patch`, `pytest`,
    `from mcp_coder.cli.commands.commit import execute_commit_auto, validate_git_repository`
    (`_push_after_commit` dropped), `create_parser`.
  - `test_commit_push.py`: `argparse`, `logging`, `Path`, `Mock`, `patch`, `pytest`,
    `from mcp_coder.cli.commands.commit import _push_after_commit, execute_commit_auto`.
    Keep only what is actually used, removing stale ones with `run_ruff_fix(select=["F401"])`.
- `.large-files-allowlist`: delete the line `tests/cli/commands/test_commit.py`.
- `vulture_whitelist.py:136`:
  `# test_commit.py - @patch decorator parameters for push tests` →
  `# test_commit_push.py - @patch decorator parameters for push tests`.

## ALGORITHM

```
before = collect-only counts: test_commit.py, tests/cli/commands/
move MODULE (dry run, apply); move both push classes (dry run, apply)
verify MODULE precedes classes and no import from test_commit; else write one line to pr_info/.blocked.txt and stop
fix imports (ruff_fix F401 / add missing); edit allowlist + vulture comment
run standard checks; compare counts to DATA; check_file_size reports no stale entries
```

## DATA — expected counts (collect-only, no marker filter)

| Path | Before | After |
|---|---:|---:|
| `tests/cli/commands/test_commit.py` | 30 | 18 |
| `tests/cli/commands/test_commit_push.py` | — | 12 |
| `tests/cli/commands/` | C (record) | C |

End state across the whole PR (verify once here): `test_commit.py` 18,
`test_commit_push.py` 12, `test_commit_operations.py` 19, `test_commit_operations_parsing.py` 25,
`test_commit_operations_default_args.py` 10 (total 84). All five files are under 750 lines,
and neither original is in `.large-files-allowlist`. Any mismatch → write one line to
`pr_info/.blocked.txt` and stop.

## Commit

`test(commit): move push tests to test_commit_push.py`
