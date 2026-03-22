# Step 4: Fix all `tests/` warnings — W0612, W0718, W1514, W1404, W0108, W0107, W0702, W0201, W0719

## Goal
Fix all fixable warnings in `tests/`. After step 5's config change, these warnings
will be surfaced by pylint — they must all be clean before that commit lands.

---

## WHERE — Files Modified

### W0612 — Unused variables (43 total)

**`tests/workflows/vscodeclaude/test_cleanup.py`** (~14 occurrences):
All are tuple unpacks like:
```python
session, git_status = stale_sessions[0]
# where only session OR git_status is used
```
Fix: use `_` for the unused side:
```python
session, _ = stale_sessions[0]   # or
_, git_status = stale_sessions[0]
```
Also: `session, git_status = get_stale_sessions(...)` where neither is used →
`_ = get_stale_sessions(...)` or check which side is used.

**Other files (one per test):**
- `tests/cli/commands/test_check_branch_status_ci_waiting.py` — `ci_status` unused (×2) → `_`
- `tests/cli/commands/test_commit.py` — `captured_out` unused → `_`
- `tests/cli/commands/test_define_labels.py` — `repo` unused (×3) → `_`
- `tests/cli/commands/test_gh_tool.py` — `result` unused → `_`
- `tests/cli/commands/test_verify_integration.py` — `call_args` unused → `_`
- `tests/formatters/test_integration.py` — `i` unused in for-loop → `_`
- `tests/llm/test_mlflow_logger.py` — `logger` (×2), `result` unused → `_`
- `tests/llm/providers/claude/test_claude_cli_stream_integration.py` — `result` unused → `_`
- `tests/llm/session/test_resolver.py` — `fake_path` unused → `_`
- `tests/utils/test_folder_deletion.py` — `mock_move` unused → `_`
- `tests/utils/git_operations/test_commits.py` — `repo` unused → `_`
- `tests/utils/git_operations/test_remotes.py` — `expected_sha` unused → `_`
- `tests/workflows/test_create_pr_integration.py` — `repo` (×3) unused → `_`
- `tests/workflows/vscodeclaude/test_closed_issues_integration.py` — `mock_launch`, `result` unused → `_`
- `tests/workflows/vscodeclaude/test_issues.py` — `issues_without_branch` unused → `_`
- `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` — `mock_execute` unused → `_`

### W0718 — Broad-exception-caught (31 total)

Add inline disable on each `except Exception` in test files:
```python
except Exception:  # pylint: disable=broad-exception-caught  # test helper — broad catch intentional
```
Key files: `tests/utils/github_operations/test_base_manager.py` and scattered others.
(Run pylint on tests/ to get exact list after steps 1–3 are committed.)

### W1514 — Unspecified encoding (23 total)

Every `open(path, "r")` or `open(path, "w")` call in test files needs `encoding="utf-8"`:
```python
# Before
with open(tmp_file, "r") as f:
# After
with open(tmp_file, "r", encoding="utf-8") as f:
```
Run `pylint tests/ --disable=... --enable=W1514` to get exact list of files/lines.
Expected files include test files under `tests/workflows/`, `tests/utils/`, `tests/formatters/`.

### W1404 — Implicit string concatenation (4 total)

Adjacent string literals on the same or consecutive lines without explicit `+`:
```python
# Before
msg = ("first part"
       "second part")
# After
msg = ("first part" " second part")  # or combine into one string
```
Fix: merge into a single string or add explicit `+`.

### W0108 — Unnecessary lambda (4 total)

```python
# Before
callback = lambda x: some_func(x)
# After
callback = some_func
```

### W0107 — Unnecessary pass (3 total)

Remove `pass` from blocks that have other statements:
```python
# Before
def test_something():
    assert True
    pass  # ← remove this
# After
def test_something():
    assert True
```

### W0702 — Bare except (2 total)

```python
# Before
except:
# After
except Exception:  # pylint: disable=broad-exception-caught  # test helper
```

### W0201 — Attribute defined outside init (2 total)

Move attribute assignments from test methods into `setUp` or `__init__`:
```python
# Before
class TestFoo:
    def test_a(self):
        self.bar = Mock()  # ← W0201

# After
class TestFoo:
    def setUp(self):
        self.bar = Mock()

    def test_a(self):
        ...
```

### W0719 — Broad exception raised (1 total)

```python
# Before
raise Exception("test error")
# After
raise RuntimeError("test error")
```

## WHAT

No new functions. All changes are:
- `varname = expr` → `_ = expr` (unused variables)
- `open(f)` → `open(f, encoding="utf-8")` (encoding)
- `lambda x: f(x)` → `f` (unnecessary lambda)
- Remove `pass` from non-empty blocks
- `except:` → `except Exception:  # pylint: disable=...`
- Attribute assignment moved to `setUp`
- `raise Exception` → `raise RuntimeError`
- `except Exception` with inline disable (W0718)

## HOW

No integration points change. Test logic is preserved exactly.
The `encoding="utf-8"` addition may require checking if any tests deliberately
test platform-default encoding — if so, keep as-is and add inline disable instead.

## ALGORITHM

```
W0612: for each unused variable, replace with _ or use _ in tuple unpack
W0718: append inline disable comment to each except Exception in tests/
W1514: add encoding="utf-8" to every open() call missing it in tests/
W1404: merge adjacent string literals into one
W0108: replace lambda x: f(x) with bare f reference
W0107: delete standalone `pass` from blocks that have other statements
W0702: replace bare `except:` with `except Exception:` + inline disable
W0201: move self.attr = ... from test methods into setUp / __init__
W0719: replace raise Exception with raise RuntimeError
```

## DATA

No return value changes. No test logic changes.
Pylint count in `tests/` reduced by: 43 + 31 + 23 + 4 + 4 + 3 + 2 + 2 + 1 = **113 warnings**.

## TDD Note

These are test files themselves — no additional tests needed.
Run pytest after changes to confirm all tests still pass.

---

## LLM Prompt

```
Please implement Step 4 of the pylint warning cleanup described in
`pr_info/steps/summary.md` and `pr_info/steps/step_4.md`.

This step fixes all fixable warnings in `tests/`:
W0612 (unused variables), W0718 (broad-exception-caught),
W1514 (unspecified-encoding), W1404 (implicit-str-concat),
W0108 (unnecessary-lambda), W0107 (unnecessary-pass),
W0702 (bare-except), W0201 (attribute-defined-outside-init),
W0719 (broad-exception-raised).

Rules:
- W0612: Replace unused variable names with `_`. For tuple unpacks, use `_` for
  the unused side only.
- W0718: Add `# pylint: disable=broad-exception-caught  # test helper` to each
  `except Exception` line in test files.
- W1514: Add `encoding="utf-8"` to every `open()` call in test files that
  lacks an encoding argument. If a test deliberately tests platform encoding,
  add an inline disable instead.
- W1404: Merge adjacent implicit string concatenations into a single string.
- W0108: Replace `lambda x: f(x)` with direct `f` reference.
- W0107: Delete `pass` from blocks that contain other statements.
- W0702: Replace bare `except:` with `except Exception:` plus inline disable.
- W0201: Move `self.attr = ...` assignments from test methods into `setUp`.
- W0719: Replace `raise Exception(...)` with `raise RuntimeError(...)`.
- Do NOT change any test assertions or test logic.

Run pylint on tests/ (with --disable=C,R,W1203,W0621,W0212,W0613,W0611,W0404,W0511
--enable=W) to verify zero remaining warnings.
Run pytest (fast unit tests) to confirm all tests still pass.
Run mypy to confirm type safety.
```
