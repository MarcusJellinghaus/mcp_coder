# review-plan review log 1

## Round 1 — 2026-11-08
**Findings**:
Reviewing plan step files against the issue; now checking the real `PythonToolkit` and the callers the plan rewires.Cross-checking existing verify/commit tests that the plan claims stay unchanged.`pr_info/steps/step_3.md:70` — medium — The autouse `_resolvable_formatter` fixture only stubs `verify_toolkit`. From step 3 on, every unit test that reaches `check_formatter_config` or `run_formatters` (implement, rebase, review, fix_ci, check_branch_status, commit) goes through the real `load_toolkit`: an entry-point lookup under `mcp_coder.toolkits`, then building `PythonToolkit` and calling `describe()`. The whole fast suite then depends on installed entry-point metadata, which the issue's Constraints say tests must not assume. Also stub the registry in the fixture, by patching `toolkit_runner._toolkit_class` to return `PythonToolkit` or a fake, and let the step-2 tests override it.

`pr_info/steps/step_4.md:63` — low — The "Default (no toolkit table) → `Toolkit` row `[OK]` with `mcp-tools-py`" test, and the autouse fixture at line 55 that patches only `verify_toolkit`, need `mcp-tools-py` to be registered as an entry point. Patch `_toolkit_class` or `load_toolkit` here as well, so the verify tests don't rely on installed metadata.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_3.md (around line 70), extend the autouse `_resolvable_formatter` fixture so it also stubs the toolkit registry: patch `toolkit_runner._toolkit_class` to return `PythonToolkit` (or a fake toolkit), in addition to `verify_toolkit`. That way fast unit tests that reach `check_formatter_config` / `run_formatters` (implement, rebase, review, fix_ci, check_branch_status, commit) don't depend on installed `mcp_coder.toolkits` entry-point metadata. State that the step-2 registry tests override or bypass this patch.", "In pr_info/steps/step_4.md (around lines 55-63), have the verify-test autouse fixture also patch `_toolkit_class` (or `load_toolkit`). The 'Default (no toolkit table) → Toolkit row [OK] with mcp-tools-py' test must not depend on `mcp-tools-py` being registered as an installed entry point."], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-08
**Findings**:
Reviewing plan steps against the contract and the real `PythonToolkit` next.pr_info/steps/step_5.md:82 — medium — `get_binding` is called without error handling in `process_single_task` and in the final check block in `core.py`. The plan assumes the entry pre-flight already validated the config. But implement's LLM sessions can edit `pyproject.toml` / `mcp-coder.toml` mid-run, and step 1 of this very plan does. Strict loading then raises an uncaught `ValueError` and crashes the workflow. Today a failed check logs and continues. Catch `ValueError` at both call sites, log it and skip, or treat it as a failed check.
pr_info/steps/step_2.md:107 — medium — The "params accepted by an open schema" test can't be built: `ToolkitInfo.__post_init__` in mcp-coder-utils rejects any `params_schema` that isn't `"type": "object"` with `"additionalProperties": false`. The fake toolkit's `describe()` would raise. Use a closed schema that declares the test's params as properties.
pr_info/steps/step_6.md:107 — low — The real-toolkit test puts `test_fail.py` at the tmp project root. `PythonToolkit` takes the test folder from `testpaths` and defaults to `tests`, so nothing is collected: the result is `skipped` and `_run_all_checks` returns an empty set. Put the file under `tests/` (expected key `test: tests/test_fail.py::test_fail`), or set `testpaths`. The real-toolkit test at `pr_info/steps/step_2.md:118` has the same problem.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_5.md (around line 82), wrap both `get_binding` call sites in `core.py` (in `process_single_task` and in the final check block) with `except ValueError`. Log the error and treat it as a failed check rather than crashing. A config edited mid-run can fail strict loading, and the current behaviour is to log and continue. Add a unit test where `get_binding` raises `ValueError` and check that the workflow logs it and continues.', 'In pr_info/steps/step_2.md (around line 107), rewrite the \'params accepted by an open schema\' test. `ToolkitInfo.__post_init__` rejects any `params_schema` that isn\'t `"type": "object"` with `"additionalProperties": false`. Give the fake toolkit a closed schema that declares the test\'s params as properties, and update the test name and description to match.', 'In pr_info/steps/step_6.md (around line 107) and pr_info/steps/step_2.md (around line 118), put the real-toolkit test file `test_fail.py` under `tests/` in the tmp project (or set `testpaths` explicitly) so `PythonToolkit` collects it. In step 6, expect the key `test: tests/test_fail.py::test_fail`.'], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-11-08
**Findings**:
Checking the plan against the real `PythonToolkit` and the current `commit.py` / `rebase.py`; the report follows.`pr_info/steps/step_3.md:78` — medium — Step 3's autouse conftest patch makes `toolkit_runner._toolkit_class` return `PythonToolkit`. Step 2's test "unregistered name → `ValueError` (patch `entry_points` to return nothing)" (`pr_info/steps/step_2.md:106`) calls `load_toolkit`, not `_toolkit_class`, so the patch bypasses `entry_points` and the test fails from step 3 on. Line 78–81 only covers tests that call `_toolkit_class` directly. Fix: have the `load_toolkit`-level registry tests also monkeypatch `_toolkit_class` back to `_REAL_TOOLKIT_CLASS`.
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
