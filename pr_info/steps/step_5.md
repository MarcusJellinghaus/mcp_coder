# Step 5 — Documentation

**Context:** [summary.md](./summary.md).

#1113 already rewrote every `--execution-dir` mention into a deprecation notice, so this step
**deletes** rather than corrects. Docs-only: no source change, no test change.

## WHERE

| File | Occurrences |
|---|---|
| `docs/cli-reference.md` | 10, last at `:693` |
| `docs/architecture/architecture.md` | `:124`, `:126-137`, `:158-163`, `:374-376` |
| `docs/configuration/claude-code.md` | `:127` |
| `docs/environments/environments.md` | `:124` (and the anchor link at `:150` — see below) |
| `docs/repository-setup/claude-code.md` | `:200`, `:245` |
| `.claude/CLAUDE.md` | the `## Execution directory` section (`:130-135`, 2 refs at `:132`, `:135`) |

## WHAT — passages that change without containing the literal string

- **`architecture.md:124`** — the "Context Separation Pattern" bullet becomes factually wrong
  once the two directories are one. Delete it. **Leave `:118` ("Execution Context Anchoring")
  alone** — it carries no deprecation clause and already states the surviving truth verbatim, so
  it needs no edit at all.
- **`architecture.md:126` `### Execution Context Management`** — **keep the heading verbatim.**
  `environments.md:150` links to `#execution-context-management`; keeping the name is
  anchor-compatible by definition and leaves no dangling link to chase.
- Under that heading: delete the two-directory framing (`:130-137`, incl. the `--execution-dir`
  override bullets) and the "**Deprecated override**" block (`:158-163`). **Keep** the
  "Why the default is `project_dir`" explanation (`:139-156`) and the "**Reporting**" paragraph
  (`:165-173`) — both remain true as written.
- **`architecture.md:374-376`** — delete the "Deprecated variant" blockquote in Scenario 1.
- **`environments.md:124`** — "`--execution-dir` still overrides this, but is deprecated" →
  drop the clause; the sentence keeps its first half.
- **`repository-setup/claude-code.md:243-246`** — "its `_read_settings_allow`
  (`llm/providers/copilot/copilot_cli.py:230-241`) reads
  `<execution_dir>/.claude/settings.local.json`". Step 2 renamed that parameter to `cwd`, so the
  passage is already false; it contains no `--execution-dir`, only `<execution_dir>`. Rewrite it
  as `<cwd>/.claude/settings.local.json` — the point it makes (the anchoring shift applies to
  copilot too) stays true.
- **`.claude/CLAUDE.md:130-135`** — delete the whole `## Execution directory` section: the
  heading, the two-bullet `execution_dir` / `project_dir` list and the "Never conflate the two"
  paragraph. Nothing replaces it: `--project-dir` is documented elsewhere.

## HOW

Search-driven, not memory-driven:

```
mcp__workspace__search_files(pattern="(?i)execution.dir", glob="docs/**/*.md")
mcp__workspace__search_files(pattern="(?i)execution.dir", glob=".claude/*.md")
```

**The `(?i)` matters.** A case-sensitive pattern misses `architecture.md:124`'s "Execution
directory" (capital E, lowercase d) and any other sentence-case prose; `execution.dir` with an
inline any-character then covers `--execution-dir`, `execution_dir`, `<execution_dir>` and
"Execution Directory" in one pass.

Then re-run both searches after editing; the only surviving hits should be none.

## ALGORITHM / DATA

None — prose only.

## Verification

- Zero hits for the **broad, case-insensitive** pattern `(?i)execution.dir` across `docs/` and
  `.claude/` — not just the literal flag. Grepping only `--execution-dir` misses prose like
  `<execution_dir>/.claude/settings.local.json` (`repository-setup/claude-code.md:245`), and a
  case-sensitive grep misses sentence-case prose like `architecture.md:124`.
- `docs/environments/environments.md:150`'s `#execution-context-management` anchor still
  resolves to a heading in `docs/architecture/architecture.md`.
- Read `architecture.md`'s "Execution Context Management" section end-to-end: it must describe
  one directory, with the #1113 rationale and the reporting behaviour intact.
- Quality gate still run (docs-only, but the project requires all three checks).

## Commit

```
Remove --execution-dir from documentation

The flag is gone; #1113's deprecation notices are deleted rather than
corrected. Closes #1132.
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`, then implement step 5 only.
>
> Delete every `--execution-dir` reference from `docs/cli-reference.md`,
> `docs/architecture/architecture.md`, `docs/configuration/claude-code.md`,
> `docs/environments/environments.md`, `docs/repository-setup/claude-code.md` and the
> `## Execution directory` section of `.claude/CLAUDE.md` (`:130-135`). Also fix the passages that are now
> wrong without containing the literal string: the "Context Separation Pattern" bullet
> (`architecture.md:124`), the two-directory framing and deprecated-override block under
> "Execution Context Management", the "Deprecated variant" blockquote in Scenario 1, and
> `repository-setup/claude-code.md:243-246`, where `<execution_dir>/.claude/settings.local.json`
> must become `<cwd>/.claude/settings.local.json` after step 2's rename.
>
> **Keep the `### Execution Context Management` heading exactly as it is** —
> `docs/environments/environments.md:150` links to its anchor. Keep the "Why the default is
> `project_dir`" explanation and the "Reporting" paragraph; both are still true.
>
> Use `mcp__workspace__search_files` to find the occurrences and again afterwards to prove none
> remain — search the broad, **case-insensitive** pattern `(?i)execution.dir`, not just
> `--execution-dir`, or references written as `<execution_dir>` or "Execution directory" survive.
> Docs-only: no source or test changes. Use MCP tools exclusively, run the three
> quality checks, and make one commit for this step.

---

## Implementation note (2026-08-29)

Docs-only, as planned — no source or test change. Deleted: 10 identical `--execution-dir` bullets
in `docs/cli-reference.md`; the "Context Separation Pattern" bullet, the two-directory framing +
`**Implementation**` bullets, the "Deprecated override" example and the Scenario 1 "Deprecated
variant" blockquote in `docs/architecture/architecture.md`; the `## Execution directory` section
of `.claude/CLAUDE.md`. Reworded: the deprecation clauses in `docs/configuration/claude-code.md`,
`docs/environments/environments.md` and `docs/repository-setup/claude-code.md` (whose
"discovery picks the wrong file" symptom paragraph described a case that can no longer occur),
plus `<execution_dir>/.claude/settings.local.json` → `<cwd>/.claude/settings.local.json` after
step 2's rename. Kept verbatim: the `### Execution Context Management` heading (anchor target of
`environments.md:149`), the "Why the default is `project_dir`" explanation and the "Reporting"
paragraph.

**Verified:** `(?i)execution.dir` returns **0 matches** across `docs/**/*.md` and `.claude/*.md`;
`environments.md:149`'s `#execution-context-management` link still resolves to
`architecture.md:125`.

**pytest could not be run — the same pre-existing environment blocker recorded in
[step_2.md](./step_2.md), [step_3.md](./step_3.md), [step_4a.md](./step_4a.md) and
[step_4b.md](./step_4b.md).** The installed `mcp-workspace` package lacks
`mcp_workspace.checks.branch_status_rendering`, which `src/mcp_coder/checks/branch_status.py:17`
imports via `mcp_coder/__init__.py:37`, so every test module fails at collection. Fix by
reinstalling `mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git`.

`black` / `isort` pass. Pylint and mypy report **exactly** the step-4b baseline (the `E0401` /
`import-not-found`, `fail_on_reviews` / `pr_feedback_undeterminable` and `E1125` entries from the
same stale package plus the optional langchain extras) — unchanged, as a docs-only edit cannot
affect them.

`run_format_code` also reformatted one unrelated pre-existing file,
`tests/workflows/vscodeclaude/test_assessment_issue_facts.py` (isort collapsed a wrapped
`from ... import assess_issue_state`). It is not part of this step; commit or drop it separately.
