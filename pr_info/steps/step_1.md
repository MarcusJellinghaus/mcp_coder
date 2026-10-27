# Step 1 — Move the six approval helpers into `tests/icoder/_app_pilot_approval_helpers.py`

Read `pr_info/steps/summary.md` first. This step is one commit.

## LLM prompt
> Implement step 1 of `pr_info/steps/step_1.md`, using the context in `pr_info/steps/summary.md` (issue #1331). This is a pure move: use `mcp__mcp-tools-py__move_symbol` (dry run first) and change nothing inside any moved body. Use MCP tools only. If any check below fails, write one line describing it to `pr_info/.blocked.txt` and stop. Do not hand-edit code beyond the import edits allowed in part D. Run all checks in part F, then format and commit.

## WHERE
- Source: `tests/icoder/test_app_pilot.py` (lines 444–510)
- Destination (new): `tests/icoder/_app_pilot_approval_helpers.py`
- Importers: `tests/icoder/test_app_pilot_approval.py`, `tests/icoder/test_app_pilot_approval_persist.py`

## WHAT (moved verbatim, signatures unchanged)
```python
_APPROVAL_TOOL = "mcp__srv__do_it"
def _approval_event(approval_id: str = "a1", tool_name: str = _APPROVAL_TOOL) -> StreamEvent: ...
class _RecordingEngine(ApprovalEngine):
    def __init__(self) -> None: ...
    def resolve_pending(self, approval_id: str, decision: ApprovalDecision) -> None: ...
    def cancel_all(self) -> None: ...
def _isolate_user_layer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None: ...
def _author_project_ask(tmp_path: Path) -> None: ...
async def _open_modal_and_press(app: ICoderApp, pilot: Pilot[Any], key: str, tool_name: str = _APPROVAL_TOOL) -> None: ...
```

## HOW (integration points)
- The new module gets whatever imports `move_symbol` writes for the moved code. Expected: `json`, `Path`, `Any`, `pytest`, `Pilot`, `ApprovalDecision`/`ApprovalEngine`, `ICoderApp`, `ApprovalModal`, `StreamEvent`, each from the same module as in the original file.
- Each approval file gets one `from tests.icoder._app_pilot_approval_helpers import (...)` with the same names as before. No `tests.icoder.test_app_pilot` import remains in either file.
- No `pytestmark`, no module docstring and no `conftest.py` change.

## ALGORITHM
```
A. baseline   = collect(-qq tests/icoder/)  + run the 3 pilot files        # must all pass
B. preview    = move_symbol(6 symbols, dry_run=True); if not accept(preview): go to C
   else run move_symbol(6 symbols) for real; go to D
C. fallback:  3a [_RecordingEngine,_isolate_user_layer,_author_project_ask,_open_modal_and_press]
              3b [_approval_event]   3c [_APPROVAL_TOOL]   (each dry-run + accept first)
D. fix imports: delete stale self-import (fallback only); run_ruff_fix(select=[F401,F811])
E. run_format_code
F. verify: counts == baseline, 3 files pass, checks green, compact diff clean → commit
```

### A. Baseline (no marker filter)
1. `run_pytest_check(extra_args=["--collect-only", "-qq", "tests/icoder/"])`. Record the total (expected 1062) and the per-file counts: `test_app_pilot.py` 19, `test_app_pilot_approval.py` 22, `test_app_pilot_approval_persist.py` 11. If the output has no per-file lines, run `--collect-only -q` on each of the three files instead.
2. `run_pytest_check(extra_args=["-q", "-n", "auto", "tests/icoder/test_app_pilot.py", "tests/icoder/test_app_pilot_approval.py", "tests/icoder/test_app_pilot_approval_persist.py"], timeout_seconds=600)` → all must pass. Otherwise write to `pr_info/.blocked.txt` and stop.
3. Precondition: `tests/icoder/_app_pilot_approval_helpers.py` does not exist. If it exists, write to `pr_info/.blocked.txt` and stop.

### B. Single call (preferred)
```python
move_symbol(
    source_file="tests/icoder/test_app_pilot.py",
    symbol_names=["_APPROVAL_TOOL", "_approval_event", "_RecordingEngine",
                  "_isolate_user_layer", "_author_project_ask", "_open_modal_and_press"],
    dest_file="tests/icoder/_app_pilot_approval_helpers.py",
    dry_run=True,
)
```
**accept(preview)** requires all of:
- only the four files in WHERE are touched;
- `_APPROVAL_TOOL` sits above `_approval_event` and `_open_modal_and_press`;
- no body contains a `test_app_pilot.` or `_app_pilot_approval_helpers.` prefixed reference.

If all hold, run the same call with `dry_run=False`. If the real call touches another file or times out, write to `pr_info/.blocked.txt` and stop.

### C. Fallback (only if B's preview fails a check)
Same `source_file` / `dest_file`. Dry-run each call and apply accept() before its real call:
- 3a `["_RecordingEngine", "_isolate_user_layer", "_author_project_ask", "_open_modal_and_press"]`
- 3b `["_approval_event"]`
- 3c `["_APPROVAL_TOOL"]`, alone and last. It leaves a stale `from tests.icoder.test_app_pilot import _APPROVAL_TOOL` in the new module, which is deleted in D. Run no tests between 3c and D.

If any fallback preview fails accept(), or the final order still puts `_APPROVAL_TOOL` below a user, write to `pr_info/.blocked.txt` and stop. Never reorder by hand.

### D. Imports (import-only edits)
1. Read the import blocks of the four files.
2. Delete any import of a name that the same file defines (fallback only: `_APPROVAL_TOOL` in the new module).
3. If an approval file still imports any helper from `tests.icoder.test_app_pilot`, change that import's module path to `tests.icoder._app_pilot_approval_helpers` (same names).
4. `run_ruff_fix(select=["F401", "F811"], target_directories=["tests/icoder"])`. Expected removals in `test_app_pilot.py`: `ApprovalDecision` and `ApprovalEngine` (the whole `permissions.approval` line), `ApprovalModal`, `StreamEvent`. `json`, `Callable`, `Path`, `Any`, `Pilot`, `Static` and `pytest` stay.
5. If a moved name is imported from a different module than in the original file, change it back to the original module.

### E. Format
`run_format_code`.

### F. Verification (all MCP)
- [ ] `run_pylint_check`, `run_mypy_check`, `run_ruff_check` are green.
- [ ] The step A.1 collect call gives the same total and the same three per-file counts. A difference → `pr_info/.blocked.txt`, stop.
- [ ] The step A.2 command passes. A `NameError` / `ImportError` → `pr_info/.blocked.txt`, stop.
- [ ] `run_pytest_check(extra_args=["-q", "-m", "not textual_integration", "tests/icoder/test_app_pilot_approval.py", "tests/icoder/test_app_pilot_approval_persist.py"])` → "No Tests Found".
- [ ] Fast unit tests with the CLAUDE.md marker exclusion and `-n auto` are green.
- [ ] `run_vulture_check`, `run_lint_imports_check`, `run_tach_check` and `check_file_size` are green.
- [ ] `search_files(pattern="(test_app_pilot\\w*|_app_pilot_approval_helpers|conftest)\\.(?!py\\b)\\w", glob="tests/icoder/**/*.py")` → 0 matches.
- [ ] `search_files(pattern="from tests\\.icoder\\.test_app_pilot import", glob="tests/icoder/test_app_pilot_approval*.py")` → 0 matches.
- [ ] Compact diff (`git diff`, `compact=true`) contains only moved blocks, import changes in the four files, the new file header and blank-line hunks. Any body hunk → `pr_info/.blocked.txt`, stop.

## DATA
- No runtime data or return values change. All six signatures, defaults and bodies are identical.
- End state:
  - `test_app_pilot.py` is about 440 lines with 19 tests;
  - the new module has 6 symbols and 0 tests;
  - the collect counts equal the baseline.

## Commit
After F is green: `run_format_code`, then commit:
`test(icoder): move shared approval pilot helpers into _app_pilot_approval_helpers.py (#1331)`
