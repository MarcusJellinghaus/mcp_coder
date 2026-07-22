# Step 4 — Prompt templates in `prompts.md`

> References `pr_info/steps/summary.md` §1 and §5. Author **3** fresh headed sections tuned for
> the headless two-session model (KISS: one shared supervisor section, two reviewer sections).
> The CI step reuses `implement`'s existing headers — do **not** author new CI sections.

## WHERE
- `src/mcp_coder/prompts/prompts.md` (modify — append a new top-level section)
- `tests/prompts/test_prompt_loader.py` (modify — assert the new headers load)

## WHAT — three new sections loadable via `get_prompt(str(PROMPTS_FILE_PATH), "<Header>")`
1. **`Review Implementation Reviewer`** — reviewer for code review. Substitution vars
   `{issue_number}`, `{base_branch}`. Instructs: read `.claude/knowledge_base/*.md`, the
   issue + linked issues (via MCP `github_issue_view`), and compute the diff against
   `{base_branch}` itself; return a **structured** report (findings as `file:line` + severity;
   no free prose). Says: implement fixes only when a follow-up task list is given, using
   `mcp-workspace` edit tools.
   - **Structured-report contract (explicit requirement):** the report is the **sole**
     reviewer→supervisor interface and **nothing machine-parses it downstream**, so the reviewer
     prompt MUST enforce the contract — every finding is emitted as `file:line` + an explicit
     severity, never as free prose (a finding lacking `file:line` + severity is invalid). Both
     reviewer sections carry this hard requirement.
2. **`Review Plan Reviewer`** — reviewer for plan review. No `{base_branch}`, no diff; reviews
   `pr_info/steps/*` + issue + knowledge base; same structured-report contract; edits plan
   files via MCP when tasked.
3. **`Review Supervisor`** — shared triage prompt (both workflows). Consumes the reviewer's
   report string; emits a **strict fenced JSON** verdict and nothing else:
   ````
   ```json
   {"decision": "dismiss" | "tasks" | "escalate",
    "tasks": ["...", "..."],            // present only when decision == "tasks"
    "escalate_reason": "..."}           // present only when decision == "escalate"
   ```
   ````
   Includes the triage rules from `/implementation_review_supervisor` (accept/skip/escalate,
   stay in scope, substantive-findings-only stop bar) condensed for the headless model.

## HOW
- Loaded with `get_prompt` (whole section, reviewer/supervisor) — same convention as
  `Initial Analysis` etc. The reviewer prompts use `get_prompt_with_substitutions` at the call
  site (Step 7/8) for `{issue_number}`/`{base_branch}`.
- Header nesting must match the existing parser used by `get_prompt` (see `Initial Analysis`,
  `CI Fix Prompt` for the exact `###`/`####` level convention); reuse that level.

## ALGORITHM
- None (prompt authoring).

## DATA
- Markdown only. The supervisor section's JSON contract is the interface Step 5 parses.

## TDD / checks
- Test first: extend `tests/prompts/test_prompt_loader.py` to assert
  `get_prompt(PROMPTS_FILE_PATH, "Review Implementation Reviewer")`,
  `"Review Plan Reviewer"`, and `"Review Supervisor"` each return non-empty text, and that the
  reviewer sections contain the `{issue_number}` placeholder.
- Run: `run_pytest_check(extra_args=["-n","auto","-k","prompt"])`, then pylint + mypy.

## LLM prompt for this step
> Implement Step 4 of `pr_info/steps/summary.md`. First add failing tests to
> `tests/prompts/test_prompt_loader.py` asserting three new headers load and the reviewer ones
> contain `{issue_number}`. Then append three sections to `src/mcp_coder/prompts/prompts.md`:
> `Review Implementation Reviewer` (vars `{issue_number}`/`{base_branch}`, computes diff, returns
> a structured `file:line`+severity report, edits via mcp-workspace when tasked),
> `Review Plan Reviewer` (no diff, reviews `pr_info/steps/*`, same report contract), and a shared
> `Review Supervisor` that emits ONLY a strict fenced-JSON verdict
> `{decision, tasks?, escalate_reason?}` using the triage rules from
> `.claude/skills/implementation_review_supervisor/SKILL.md`. Match the existing header level
> used by `Initial Analysis`/`CI Fix Prompt`. Do NOT add CI prompt sections. Run prompt tests,
> pylint, mypy.
