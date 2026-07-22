# Summary — Automated review workflows (`review-plan` / `review-implementation`)

Implements issue **#1072** (sub-issue 2 of 3 of epic #1063). Builds two **headless**
review workflows that run the plan / implementation review automatically and end in a
**3-way decision** (success / needs-human / error). This issue only **defines** the
supporting labels and config flags and **proves** the session mechanism; the wiring that
*consumes* them (pickup, `WORKFLOW_MAPPING`, success-transition gating) is deferred to
#1073.

Foundation #1071 (the `mcp_coder.workflow_steps` layer) is **merged** and already exposes
the round-loop-ready steps (`check_and_fix_ci`/`CIFixConfig` with
`analysis_prompt_header`/`fix_prompt_header`/`session_dir_name` overrides, `commit`,
`rebase`).

---

## Architectural / design changes

### 1. Two review LLM sessions emulated via session ids (replaces the interactive supervisor→subagent pattern)
Headless Claude cannot spawn subagents, so the interactive
`/implementation_review_supervisor` pattern is re-created in pure Python:
- **Reviewer** — a **fresh** session **per round** (`prompt_llm(session_id=None)`). Given
  only a *pointer* (issue number + base branch), it self-fetches the diff / plan + issue +
  knowledge base via MCP tools and returns a **structured** report (`file:line` + severity).
- **Supervisor** — a **persistent** session (captured on round 1, resumed each round) that
  triages the report and emits a machine-readable **verdict**
  `{decision: dismiss | tasks | escalate}`.

The two sessions **share no context**; the orchestrator is the only bridge and carries
plain text between them. `mcp_config` is threaded into **both** sessions (the reviewer edits
via `mcp-workspace` tools). CI's own ephemeral sessions (`check_and_fix_ci`) are out of scope
of this two-session invariant.

### 2. KISS decision — ONE shared review engine, not two workflows
`review-implementation` and `review-plan` differ in **only two behaviours** (base-branch
injection; after-steps = rebase + CI). Both are booleans over one identical loop
(reviewer → supervisor → verdict → apply tasks → whole-round diff backstop → 3-way routing →
per-round log → rounds cap). So instead of two near-duplicate packages we ship a single
`workflows/review/` package driven by a `ReviewConfig` dataclass with two instances. The
issue's mandated internal build order is preserved: the engine is built *as*
`review-implementation` (`run_after_steps=True`); `review-plan` is the same engine with both
flags off. This removes the drift risk the issue itself warns about.

### 3. KISS decision — failure labels as config data, not per-workflow enums
`handle_workflow_failure` already takes `category`/`from_label_id` as **plain label-id
strings**. Rather than mirror `implement`'s `FailureCategory` enum twice, each `ReviewConfig`
carries a small `failure_labels: dict[reason, label_id]`. Identical labels/behaviour; one
greppable mapping.
> **Divergence note (reversible):** the issue's letter says "a new `FailureCategory` enum per
> review workflow." Only the *representation* changes here, not the labels or routing. If the
> literal form is preferred, swap the dict for two tiny enums with no behavioural impact.

### 4. New behaviour with no interactive precedent — auto-path CI fix
On the auto path, CI is a **supervisor finding**, not a blind short-circuit.
`check_and_fix_ci` (reused from `implement`, overriding only `session_dir_name`) runs its own
retries as an after-step; a still-red result is fed back into the loop as a finding and
triaged within the rounds cap. Still red at the cap → terminal **`17f-ci`** (cause wins over
`17f-rounds`).

### 5. Structured verdict + strict parser
`prompt_llm` returns free text; the supervisor's verdict is a **fenced JSON block** parsed out
of `["text"]`. Parse failure gets **2 repair retries** (resume the supervisor asking for valid
JSON) before falling to `error`.

### 6. Task-application verification — no supervisor diff-read
Two cheap layers guard the silent-no-op mode: **(C)** a deterministic **whole-round** change
check (zero changes while `tasks` were issued = no-op, logged, loops); **(A)** the next
round's fresh reviewer re-surfaces the unmet finding. No extra LLM turn.

### 7. Prototype proven first (mandatory first commit)
An integration-marked A-B-A regression test pins the persistent-supervisor / fresh-reviewer
interleave (≥3 supervisor turns; turn 3 recalls turn 2) and **decides the session-id chaining
discipline** (reuse-original-id vs re-capture-returned-id). The same experiment validates
`create_plan`'s reuse-original-id assumption; if it fails to preserve context, that is
recorded as a finding (fix out of scope).

---

## 3-way decision

| Outcome | When | Terminal label (via `update_workflow_label`) |
|---|---|---|
| **success** | supervisor `dismiss` + (impl only) rebased + CI green | `05:plan-ready` / `08:ready-pr` |
| **needs-human** | supervisor `escalate(reason)` (log-only handoff) | reuse `04:plan-review` / `07:code-review` |
| **error** | crash / unparseable verdict / timeout / MCP down / CI red at cap / rounds cap | `14f-*` / `17f-*` via `handle_workflow_failure` |

---

## Folders / modules / files

### Created
| Path | Purpose |
|---|---|
| `src/mcp_coder/workflows/review/__init__.py` | Package marker |
| `src/mcp_coder/workflows/review/verdict.py` | `Verdict` dataclass + `parse_verdict()` |
| `src/mcp_coder/workflows/review/config.py` | `ReviewConfig` + `REVIEW_IMPLEMENTATION` / `REVIEW_PLAN` |
| `src/mcp_coder/workflows/review/review_log.py` | `next_run_number()` + `write_round_log()` |
| `src/mcp_coder/workflows/review/core.py` | `run_review_workflow()` — the shared loop |
| `src/mcp_coder/cli/commands/review.py` | `execute_review_plan` / `execute_review_implementation` |
| `tests/workflows/review/__init__.py` | Test package marker |
| `tests/workflows/review/test_prototype_session_interleave.py` | Step 1 (integration) |
| `tests/workflows/review/test_verdict.py` | Step 5 |
| `tests/workflows/review/test_config.py` | Step 6 |
| `tests/workflows/review/test_review_log.py` | Step 6 |
| `tests/workflows/review/test_core.py` | Step 7 (mocked LLM) |
| `tests/workflows/review/test_core_after_steps.py` | Step 8 (mocked CI/rebase) |
| `tests/cli/commands/test_review.py` | Step 9 |

### Modified
| Path | Change |
|---|---|
| `src/mcp_coder/config/labels.json` | Append review labels (Step 2) |
| `src/mcp_coder/utils/user_config.py` | 2 bool `FieldDef`s under `coordinator.repos.*` (Step 3) |
| `src/mcp_coder/prompts/prompts.md` | 3 headed sections: 2 reviewers + 1 supervisor (Step 4) |
| `src/mcp_coder/cli/parsers.py` | `add_review_plan_parser` / `add_review_implementation_parser` (Step 9) |
| `src/mcp_coder/cli/main.py` | Route the two new commands (Step 9) |
| `src/mcp_coder/cli/command_catalog.py` | `COMMAND_DESCRIPTIONS` entries (Step 9) |
| `tests/config/test_label_config.py` | Assert new labels valid (Step 2) |
| `tests/utils/test_user_config*.py` | Assert new flags parse/verify (Step 3) |
| `tests/prompts/` (loader test) | Assert new headers load (Step 4) |

---

## Steps (one commit each, TDD)

1. **A-B-A session-interleave prototype** (integration test; mandatory first commit).
2. **Label definitions** appended to `labels.json`.
3. **Config flags** `auto_review_plan` / `auto_review_implementation` (define + verify).
4. **Prompt templates** (2 reviewers + 1 supervisor) in `prompts.md`.
5. **Verdict parser** (`verdict.py`, pure unit).
6. **`ReviewConfig` + failure-label map + review-log writer** (`config.py`, `review_log.py`).
7. **Review engine core loop** (`core.py`) — realizes `review-plan`; mocked-LLM tests.
8. **After-steps** (base-branch injection + rebase + CI-as-finding, `17f-ci`) — realizes
   `review-implementation`; mocked tests.
9. **CLI verbs** for both workflows (parser + command module + `main.py` + catalog).

**Constants:** `REVIEW_MAX_ROUNDS = 5`, `VERDICT_REPAIR_RETRIES = 2`.
