# Decisions

Decisions from the plan-update discussion for issue #988 (diagnostics/UX only).

## F1 — Correct the pass/fail rationale (summary.md, step_2.md)

The plan wrongly claimed the `--check-models` /models probe was the only check
that can fail `verify` on a bad endpoint ("hard pass/fail belongs to
`--check-models`"). This is false in the current code:

- `--check-models` output is stored under `available_models` and is **excluded**
  from `overall_ok` and `_compute_exit_code`; it only displays a "models" row.
- `overall_ok` is built only from backend, `backend_package.ok`,
  `mcp_adapters.ok`, `langgraph.ok` (+ ollama daemon/tools).
- What actually fails `verify` on a bad endpoint is the separate unified
  "Reply with OK" test prompt in `execute_verify` (`test_prompt_ok=False` →
  exit 1).

Decision: reword summary.md and step_2.md to state this accurately. Step 2 stays
a **pure reword** of the /models probe 404 message (auth vs connection vs
endpoint) and does **not** change pass/fail behavior. The existing (correct)
statement that the shape heuristic never affects `overall_ok` is kept.

## F2 — Remove remaining 404 duplication (step_3.md)

The plan factored the 404 hint *message* into `_format_404_hint` but left the
404 *detection* predicate copy-pasted inline in both `_ask_text` and
`_ask_text_stream`. Decision: also extract detection into a single
`_is_404_error(exc) -> bool` helper called from both sites, so both predicate
and message live in one place each ("so the two copies don't drift"). Step 3
description and test notes updated accordingly.

## F3 — Add a docs note (step_1.md)

Decision: add a minimal documentation update to `docs/configuration/config.md`
in Step 1 — near the `endpoint` description (~line 287) and OpenAI example
(~lines 290-299): a one-line warning that `endpoint` must be the BASE URL only
(e.g. `https://your-host/v1`) with NO `/chat/completions` (mcp-coder appends
it), plus a short OpenAI-compatible-relay example block. Kept minimal. Added to
Step 1's file list and description. Directly addresses the config mistake behind
the reported 404.

## Not changing

- Steps 1 and 2 stay separate (do not merge).
- F5 patch-target nit not acted on — existing tests already handle it.
