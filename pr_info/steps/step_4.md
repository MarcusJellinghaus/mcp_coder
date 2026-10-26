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

- **One call, all three symbols in source order** (`MODULE` must be defined above the classes,
  whose `@patch(f"{MODULE}...")` decorators evaluate at class definition; `move_symbol` moves
  the list in reverse and inserts each at the top, so one call keeps source order, while two
  separate calls put `MODULE` last):
  `move_symbol(source_file="tests/cli/commands/test_commit.py", symbol_names=["MODULE", "TestPushAfterCommit", "TestCommitAutoPush"], dest_file="tests/cli/commands/test_commit_push.py")` — dry run, then apply.
- The call leaves a stale `from tests.cli.commands.test_commit import MODULE` (or similar) in
  `test_commit_push.py`, shadowed by the moved `MODULE` (ruff F811, not auto-fixable). Delete
  that import line by hand — it is an import edit.
- Check that `MODULE = ...` comes before `class TestPushAfterCommit` in `test_commit_push.py`.
  If it does not, move the `MODULE = ...` assignment (that one statement only) by hand to
  directly below the imports — the only hand reordering allowed in this PR.
- Check that `test_commit_push.py` does not import from `test_commit`. Otherwise write one
  line to `pr_info/.blocked.txt` and stop.
- Expected imports afterwards:
  - `test_commit.py`: `argparse`, `logging`, `Path`, `Mock`, `patch`, `pytest`,
    `from mcp_coder.cli.commands.commit import execute_commit_auto, validate_git_repository`
    (`_push_after_commit` dropped), `create_parser`.
  - `test_commit_push.py`: `argparse`, `logging`, `Path`, `Mock`, `patch`, `pytest`,
    `from mcp_coder.cli.commands.commit import _push_after_commit, execute_commit_auto`.
    Keep only what is actually used, removing stale ones with
    `run_ruff_fix(select=["F401"], target_directories=["tests/cli/commands/test_commit.py", "tests/cli/commands/test_commit_push.py"])`.
- After all moves and the import fix, `test_commit.py` must not import from `test_commit_push`
  (no remaining test there uses `MODULE`). If it does → write one line to
  `pr_info/.blocked.txt` and stop.
- `.large-files-allowlist`: delete the line `tests/cli/commands/test_commit.py`.
- `vulture_whitelist.py:136`:
  `# test_commit.py - @patch decorator parameters for push tests` →
  `# test_commit_push.py - @patch decorator parameters for push tests`.

## ALGORITHM

```
before = collect-only counts: test_commit.py, tests/cli/commands/
move MODULE + both push classes in one call (dry run, apply)
delete stale `import MODULE` from test_commit in test_commit_push.py
if MODULE does not precede the classes: move that one assignment by hand to below the imports
verify no import from test_commit; else write one line to pr_info/.blocked.txt and stop
fix imports (ruff_fix F401 with target_directories=[test_commit.py, test_commit_push.py] / add missing)
verify test_commit.py has no import from test_commit_push; else write one line to pr_info/.blocked.txt and stop
edit allowlist + vulture comment
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
