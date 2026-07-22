# Summary — Resolve LangChainPendingDeprecationWarning via langgraph/langchain-core floor bump

**Issue:** #1078

## Goal

Silence a cosmetic `LangChainPendingDeprecationWarning` emitted on the langchain
provider path by **adopting the upstream fix** (not suppressing the warning).
The warning originates entirely inside langgraph's internal serializer; we never
call `Reviver` / `load` / `loads` ourselves.

## Root cause (recap)

The warning needs **old `langgraph-checkpoint` + new `langchain-core` at the same
time**. `langgraph-checkpoint 4.1.0` already fixed it by constructing
`Reviver(allowed_objects="core")` explicitly. Requiring a `langgraph` version that
transitively pulls `langgraph-checkpoint>=4.1.0` eliminates both conditions.

## Architectural / design changes

**None.** This is a **packaging-metadata-only** change — no source module, package,
class, function, or import is added, removed, or modified. There is no reachable
code path to change (verified: zero references to `Reviver`, `langchain_core.load`,
`langgraph.checkpoint`, or `allowed_objects` anywhere in the repo). The only edit is
raising two dependency floors in one `pyproject.toml` extra, plus a one-line
explanatory comment.

The sole (optional, KISS-aligned) additive change is a **regression-guard unit test**
in the existing `tests/test_pyproject_config.py` that pins the intended floors so a
future careless edit cannot silently reintroduce the stale dead values. This is a
metadata assertion, not new production behavior.

## What changes

In the `langchain-base` extra of `pyproject.toml`:

| Line | Before | After |
|------|--------|-------|
| langchain-core | `langchain-core>=0.3.0` | `langchain-core>=1.4.7` |
| langgraph | `langgraph>=0.2.0` | `langgraph>=1.2.9` (with `#1078` comment above) |

Both current floors are stale dead values (they resolve far higher transitively).
`langchain-mcp-adapters>=0.1.0` and `httpx>=0.27.0` are **left untouched** —
unrelated to the warning, out of scope.

## Folders / modules / files created or modified

| Path | Action | Reason |
|------|--------|--------|
| `pyproject.toml` | **Modified** | Bump the two floors in `[langchain-base]`; add `#1078` comment |
| `tests/test_pyproject_config.py` | **Modified** | Add regression-guard test asserting the two floors |
| `pr_info/steps/summary.md` | Created | This document |
| `pr_info/steps/step_1.md` | Created | The single implementation step |

No new folders. No `src/` changes. No new dependencies added — only floors raised.

## Scope, constraints & non-goals

- **Scope:** langchain provider path only (agent mode / iCoder / `--llm-method
  langchain`). Claude-CLI users never trigger the warning.
- **Purely cosmetic:** no `filterwarnings` entry in the pytest config, so the warning
  cannot fail CI. No functional behavior changes.
- **Declined (per issue):** pinning `langgraph-checkpoint` directly; bumping
  `langchain-mcp-adapters`. Both kept out to preserve a minimal diff.
- **Post-merge gotcha (not part of this change):** the pin bump does **not** upgrade
  already-installed environments. The stale tool env that produced the warning must
  be **reinstalled** to actually pull `langgraph-checkpoint>=4.1.0` and clear it.

## Verification

1. `tests/test_pyproject_config.py` passes (asserts the new floors).
2. Full mandatory quality gate green (pylint / pytest / mypy).
3. Manual, post-merge: reinstall the `langchain` extra and confirm the warning no
   longer appears on the langchain provider path.
