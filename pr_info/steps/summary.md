# Summary: Create-plan workflow failure handling (#336)

## Goal
Add failure handling to the create-plan workflow, mirroring the implement workflow's pattern. When create-plan fails, set an appropriate failure label and post a GitHub comment with failure details.

## Architecture & Design Changes

### New Exception Type
- `LLMTimeoutError(TimeoutError)` in `src/mcp_coder/llm/interface.py` — normalizes `TimeoutExpired` (claude) and `asyncio.TimeoutError` (langchain) into a single catchable type. Subclasses stdlib `TimeoutError` for backward compatibility. This also **fixes a latent bug** in implement where langchain timeouts were misclassified as `GENERAL` instead of `LLM_TIMEOUT`.

### Package Refactor
- `src/mcp_coder/workflows/create_plan.py` (single file) → `src/mcp_coder/workflows/create_plan/` (package)
- Mirrors implement's structure: `__init__.py`, `core.py`, `constants.py`, `prerequisites.py`
- `__init__.py` re-exports all 9 public symbols so import statements don't change
- Test mock.patch paths update from `mcp_coder.workflows.create_plan.*` → `...core.*` / `...prerequisites.*`

### Failure Handling Pattern
- Local `FailureCategory` enum + `WorkflowFailure` dataclass in `constants.py` (mirrors implement)
- Local `_handle_workflow_failure()` wrapper in `core.py` converts local enum → shared string-based `WorkflowFailure` and delegates to `workflow_utils.failure_handling.handle_workflow_failure()`
- Local `_format_failure_comment()` in `core.py` builds GitHub comment body
- `run_planning_prompts()` return type changes: `bool` → `tuple[bool, Optional[WorkflowFailure]]`

### Behavioral Changes
- Commit/push failures promoted from warnings (return 0) to hard errors (return 1) with failure handling
- `post_issue_comments` parameter (already plumbed from CLI) wired to failure comment posting
- Always uses `from_label_id="planning"` for label transitions (relies on graceful handling in `update_workflow_label`)

### New Labels (`labels.json`)
| Internal ID | Label Name | Color |
|---|---|---|
| `planning_llm_timeout` | `status-03f-timeout:planning-llm-timeout` | `e99695` |
| `planning_prereq_failed` | `status-03f-prereq:planning-prereq-failed` | `b60205` |

### Failure Category Mapping
| Failure Point | Category |
|---|---|
| Dirty git / issue not found / branch creation / pr_info setup | `PREREQ_FAILED` |
| Prompt 1/2/3 timeout (`LLMTimeoutError`) | `LLM_TIMEOUT` |
| Prompt 1/2/3 empty response / missing session_id / other error | `GENERAL` |
| Output validation / commit / push | `GENERAL` |

## Files Created
| File | Purpose |
|---|---|
| `src/mcp_coder/workflows/create_plan/__init__.py` | Package init, re-exports 9 public symbols |
| `src/mcp_coder/workflows/create_plan/core.py` | Orchestration, prompts, failure handling |
| `src/mcp_coder/workflows/create_plan/constants.py` | FailureCategory enum, WorkflowFailure dataclass |
| `src/mcp_coder/workflows/create_plan/prerequisites.py` | Prerequisite checks, branch management |

## Files Modified
| File | Change |
|---|---|
| `src/mcp_coder/llm/interface.py` | Add `LLMTimeoutError`, normalize timeouts in `prompt_llm()` |
| `src/mcp_coder/workflows/implement/task_processing.py` | Catch `LLMTimeoutError` instead of `TimeoutExpired` |
| `src/mcp_coder/config/labels.json` | Add 2 new failure labels |
| `src/mcp_coder/workflows/__init__.py` | Update import for package |
| `src/mcp_coder/cli/parsers.py` | CLI help text one-liner about failure handling |

## Files Deleted
| File | Reason |
|---|---|
| `src/mcp_coder/workflows/create_plan.py` | Replaced by package |

## Test Files Modified
| File | Change |
|---|---|
| `tests/llm/test_interface.py` | Add `LLMTimeoutError` normalization tests |
| `tests/workflows/implement/test_task_processing.py` | Add langchain timeout → `LLM_TIMEOUT` test |
| `tests/workflows/create_plan/test_main.py` | Update patch paths, update commit/push behavior tests, add failure handling tests |
| `tests/workflows/create_plan/test_prerequisites.py` | Update patch paths to `...prerequisites.*` |
| `tests/workflows/create_plan/test_branch_management.py` | Update patch paths to `...prerequisites.*` |
| `tests/workflows/create_plan/test_prompt_execution.py` | Update patch paths to `...core.*` |
| `tests/workflows/create_plan/test_argument_parsing.py` | Update patch paths to `...prerequisites.*` |

## Implementation Steps Overview
1. **LLMTimeoutError + implement fix** — standalone, no dependencies on other steps
2. **Labels + package refactor** — mechanical restructuring, no logic changes
3. **Failure handling constants + helpers** — `constants.py`, `_format_failure_comment`, `_handle_workflow_failure`
4. **Wire failure handling into orchestration** — modify `run_create_plan_workflow` and `run_planning_prompts`
5. **Failure handling tests + CLI help** — test coverage for all failure paths, minor CLI update
