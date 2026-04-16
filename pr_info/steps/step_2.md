# Step 2 — Restructure `pyproject.toml` optional extras

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`).
> Implement ONLY step 2: restructure `[project.optional-dependencies]` in
> `pyproject.toml`. Do NOT touch `.importlinter` or docs — later steps.
> After the edit, verify the file parses (run any tool that loads it, e.g.
> pylint or pytest via MCP); mypy + pylint + pytest still green.
> Commit with message: `refactor(packaging): split langchain extra into per-provider layers`.

## WHERE

Single file: `pyproject.toml`, section `[project.optional-dependencies]`.

## WHAT

Replace the current `[mcp]`, `[truststore]`, `[langchain]`, `[dev]` blocks
with the following layout. All other extras (`types`, `test`, `mlflow`, `tui`)
are untouched.

```toml
# LangChain shared runtime (langchain-core, MCP adapters, graph, HTTP, SSL)
langchain-base = [
    "langchain-core>=0.3.0",
    "langchain-mcp-adapters>=0.1.0",
    "langgraph>=0.2.0",
    "httpx>=0.27.0",
    "truststore>=0.9.0",
]

# Per-provider extras — each pulls the shared base + its wrapper SDK
langchain-openai = [
    "mcp-coder[langchain-base]",
    "langchain-openai>=0.2.0",
]
langchain-gemini = [
    "mcp-coder[langchain-base]",
    "langchain-google-genai>=2.0.0",
]
langchain-anthropic = [
    "mcp-coder[langchain-base]",
    "langchain-anthropic>=0.3.0",
]
langchain-ollama = [
    "mcp-coder[langchain-base]",
    "langchain-ollama>=0.2.0",
]

# Meta — identical installed set to the current [langchain] extra
langchain = [
    "mcp-coder[langchain-openai]",
    "mcp-coder[langchain-gemini]",
    "mcp-coder[langchain-anthropic]",
    "mcp-coder[langchain-ollama]",
]

# ... (dev block, updated below; types/test/mlflow/tui unchanged)

dev = [
    "mcp-coder[types,test,langchain,mlflow,tui]",
    "import-linter>=2.0",
    "pycycle>=0.0.8",
    "pydeps>=3.0.0",
    "tach>=0.6.0",
    "vulture>=2.14",
    "ruff>=0.9.0",
]
```

**Deletions:**
- Remove `[mcp]` block (currently empty).
- Remove `[truststore]` block (folded into `[langchain-base]`).

## HOW

Use `mcp__workspace__edit_file` with a single edit replacing the whole
`mcp`/`mlflow`/`truststore`/`langchain`/`tui`/`dev` region — or multiple
scoped edits. Keep comment headers consistent with existing style
("# LangChain integration — alternative LLM providers (OpenAI, Gemini, …)").

No Python code touched. No tests need changing.

## ALGORITHM

```
1. Edit pyproject.toml: drop [mcp], drop [truststore], replace [langchain]
   with [langchain-base] + 4 per-provider extras + [langchain] meta.
2. Update [dev] to drop 'mcp' from the aggregated list.
3. Verify TOML parses: running any MCP tool that loads pyproject.toml
   (pylint, pytest) implicitly validates.
4. pytest (fast subset), pylint, mypy, lint-imports → all green.
```

## DATA

No runtime data structures. Only package-metadata strings. The installed
package set for `pip install mcp-coder[langchain]` must remain identical
to today's (verified manually in PR description, not automated here).

## Verification

- `mcp__tools-py__run_pytest_check` (fast subset) — confirms no test or
  tool chokes on the restructured TOML
- `mcp__tools-py__run_pylint_check` — pylint reads pyproject.toml
- `mcp__tools-py__run_mypy_check`
- `mcp__tools-py__run_lint_imports_check` — still green
  (no contract changes here)

**Manual (PR-description, not in-step):**
```
pip install -e .[langchain] && pip list       # before
# apply step 2
pip install -e .[langchain] && pip list       # after — diff should be empty
pip install -e .[langchain-anthropic]         # in clean venv
pip list | grep -iE 'openai|google|grpc|tiktoken'   # must be empty
```

## Commit

```
refactor(packaging): split langchain extra into per-provider layers

Introduces [langchain-base] shared runtime and per-provider extras for
openai/gemini/anthropic/ollama. [langchain] becomes a meta extra pulling
all four — installed package set unchanged for existing users. Drops the
standalone [truststore] extra (folded into [langchain-base]; only ever
exercised alongside the langchain HTTP/SSL plumbing) and the empty [mcp]
extra. [dev] meta updated accordingly.

Refs #829
```
