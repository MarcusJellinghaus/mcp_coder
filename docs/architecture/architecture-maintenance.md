# Keeping the Architecture Document Current

[architecture.md](architecture.md) is an overview, not an inventory. It holds what stays true while the code changes. Keep it that way; a document that lists files goes stale and stops being read.

## What belongs there

Purpose, structure, rules, and the reasons behind them. For each paragraph ask: *would it still be true in six months, and would a newcomer decide wrongly without it?* If not, cut it.

Do not copy facts that have a home elsewhere:

| Fact | Lives in |
|------|----------|
| Dependency versions, pytest markers, tool settings | `pyproject.toml` |
| Layers and allowed imports | `.importlinter`, `tach.toml` |
| Why a boundary is enforced | [enforcement.md](enforcement.md) |
| Label names and flow | [Development Process](../processes-prompts/development-process.md), `src/mcp_coder/config/labels.json` |
| What a module does | its docstring |
| Root cause of one defect, rationale for one change | the issue or PR |

## When to review it

Review the document when a change does one of these:

- adds or removes a top-level module, or moves a layer boundary
- changes a dependency rule or adds an isolation contract for a new external library
- adds an external system (a new forge, LLM provider, CI service) or changes how a run is deployed
- adds a workflow or a label family
- reverses or adds a decision that shapes the whole system (like anchoring the LLM subprocess to `project_dir`)

Most changes do none of these, so most changes need no edit. "No update needed" is a valid result; do not add content to show activity.

## Checking it

A reader should be able to answer these from the document alone, without opening code:

1. Which layers exist, and which may `llm` import?
2. Where does workflow state live, and who moves it?
3. How does a run get from a GitHub label to a Claude session on a Jenkins agent?
4. Which external systems and packages does mcp-coder depend on, and through which module?
5. What does a repository need to provide to be worked on by mcp-coder?

If one of them needs a code search, the document is missing something. If a paragraph answers none of them, consider cutting it.

Skim links as part of the review: a moved or renamed doc is the most common way this page goes stale.
