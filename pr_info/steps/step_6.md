# Step 6 — `RebaseOutcome` and merge-tree classification

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 6** exactly as described in
> `pr_info/steps/step_6.md`. Tests first, then implementation. The review
> hand-off comment is NOT changed in this step (step 8 does that) — only make the
> callers compile against the new return type. Run pylint, pytest (fast unit set,
> `-n auto`) and mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/workflow_steps/rebase.py`
- Callers: `src/mcp_coder/workflows/implement/core.py:104` (result ignored — no change needed beyond confirming), `src/mcp_coder/workflows/fix_conflict/core.py:60`, `src/mcp_coder/workflows/review/steps.py:107` (`_after_steps`), `src/mcp_coder/workflows/review/core.py` (two `_after_steps` call sites)
- Docstring mention of `_has_uncommitted_tracked_changes` in `src/mcp_coder/workflows/review/handoff.py` (`_unstage_path`) → `_uncommitted_tracked_files`
- Tests: `tests/workflow_steps/test_rebase.py`, `tests/workflows/fix_conflict/test_core.py`, `tests/workflows/review/conftest.py:143`, `tests/workflows/review/test_core_after_steps.py` (`:105`, `:252`, `:298`)

## WHAT

```python
RebaseReason = Literal[
    "ok", "dirty_tree", "no_base", "base_missing",
    "conflict", "rebase_failed", "push_failed",
]

@dataclass(frozen=True)
class RebaseOutcome:
    reason: RebaseReason
    base_branch: str | None = None
    base_sha: str | None = None          # 7 chars
    files: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.reason == "ok"

def _uncommitted_tracked_files(project_dir: Path) -> list[str]:   # replaces _has_uncommitted_tracked_changes
def _base_sha(project_dir: Path, base: str) -> str | None:
def _classify_failed_rebase(project_dir: Path, base: str) -> tuple[RebaseReason, tuple[str, ...]]:
def _attempt_rebase_and_push(project_dir: Path) -> RebaseOutcome:

# review/steps.py
def _after_steps(...) -> tuple[str | None, RebaseOutcome | None]:
```

## HOW

- `rebase.py` imports `execute_command` from `mcp_coder.utils.subprocess_runner`
  (shim — never `mcp_coder_utils`) and `SHORT_SHA_LENGTH` from
  `mcp_coder.workflow_utils.failure_handling`.
- `_uncommitted_tracked_files` = `sorted(set(status["staged"] + status["modified"]))`
  from `get_full_status` (untracked still ignored; same comments as today).
- Dirty-tree `logger.warning` names the files (`", ".join(files)`).
- `_base_sha`: `execute_command(["git", "rev-parse", "--verify", "--quiet", f"origin/{base}"], cwd=str(project_dir))`; return `stdout.strip()[:SHORT_SHA_LENGTH]` on exit 0 with non-empty stdout, else `None`; `try/except Exception` → `None`.
- `_classify_failed_rebase`: `execute_command(["git", "merge-tree", "--write-tree", "--name-only", "--no-messages", f"origin/{base}", "HEAD"], cwd=…)`; `try/except Exception` → `("rebase_failed", ())`.
- `_after_steps`: `run_after_steps=False` → `(None, None)`. After the rebase:
  `if not outcome.ok: return "rebase", outcome`; every later return carries
  `outcome` (`(None, outcome)`, `("ci", outcome)`, `(llm_failure_reason(exc) or "general", outcome)`).
  Leave the INFO log and the `#1066` comment as-is (step 8 changes them).
- `review/core.py`: unpack `reason, _ = _after_steps(...)` at both sites (step 8
  names the outcome).
- `fix_conflict/core.py`: `outcome = _attempt_rebase_and_push(project_dir)`;
  `logger.info("Rebase attempt result: %s", outcome.reason)`.
- Update the `_attempt_rebase_and_push` and `_after_steps` docstrings.

## ALGORITHM (`_attempt_rebase_and_push`)

```
dirty = _uncommitted_tracked_files(project_dir)
if dirty: warn(files); return RebaseOutcome("dirty_tree", files=tuple(dirty))
target = _get_rebase_target_branch(project_dir);  if not target: return RebaseOutcome("no_base")
if check_base_branch_on_origin(project_dir, target): warn; return RebaseOutcome("base_missing", target)
rebased = rebase_onto_branch(project_dir, target);  sha = _base_sha(project_dir, target)
if not rebased: reason, files = _classify_failed_rebase(project_dir, target); return RebaseOutcome(reason, target, sha, files)
if not push_changes(project_dir, force_with_lease=True): warn; return RebaseOutcome("push_failed", target, sha)
return RebaseOutcome("ok", target, sha)
```

`_classify_failed_rebase`:

```
r = execute_command([... merge-tree ...])
lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
if r.return_code == 1 and not r.execution_error and lines and _TREE_OID.fullmatch(lines[0]):
    return "conflict", tuple(lines[1:])
return "rebase_failed", ()          # exit 0, timeout, missing git, git < 2.38, ...
```

`_TREE_OID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")`.

## DATA

`RebaseOutcome` is always truthy — no caller may use `if outcome:`; use `.ok`.

## Tests

`tests/workflow_steps/test_rebase.py` (patch `get_full_status`,
`detect_base_branch`, `check_base_branch_on_origin`, `rebase_onto_branch`,
`push_changes`, `execute_command` in `mcp_coder.workflow_steps.rebase`):
- one test per reason: `ok`, `dirty_tree` (files = staged + modified, untracked excluded, warning names files), `no_base`, `base_missing` (base set, sha `None`), `conflict`, `rebase_failed`, `push_failed`
- `base_sha` truncated to 7 chars; `None` when rev-parse fails
- `_classify_failed_rebase`: exit 1 + OID + files → `conflict` with files; exit 1 + empty stdout + `execution_error` → `rebase_failed`; exit 1 with non-OID first line → `rebase_failed`; exit 0 → `rebase_failed`; `execute_command` raising → `rebase_failed`
- `.ok` only for `"ok"`
- Existing dirty-tree / missing-on-origin tests updated to assert `outcome.reason` instead of `False`.

Mocks elsewhere return `RebaseOutcome`:
- `tests/workflows/review/conftest.py:143` → `RebaseOutcome("ok", "main", "abc1234")`
- `test_core_after_steps.py:105,252,298` → `RebaseOutcome("conflict", "main", "abc1234", ("a.py",))`
- `tests/workflows/fix_conflict/test_core.py:30` → `RebaseOutcome("ok", "main", "abc1234")`; `:111` sets a `RebaseOutcome` return value.
- implement tests patching `_attempt_rebase_and_push` need no change (result ignored).
