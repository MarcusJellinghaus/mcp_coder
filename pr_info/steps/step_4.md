# Step 4 — Documentation: optional-dependencies page + README pointer

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_4.md`).
> Implement ONLY step 4: create
> `docs/configuration/optional-dependencies.md` and add a short "Optional
> features" pointer section to `README.md`. Do NOT modify code or config.
> After the edit, run pylint, pytest (fast), mypy, `lint-imports` — all
> must still pass (unrelated; mandated by CLAUDE.md).
> Commit: `docs(config): add optional-dependencies page and README pointer`.

## WHERE

**Created:** `docs/configuration/optional-dependencies.md`
**Modified:** `README.md` — add one short section under / near the existing
"Installation" block, pointing to the new page.

## WHAT

### New page `docs/configuration/optional-dependencies.md`

Single-page reference with a table mapping each extra to what it enables
and when to install it. Structure:

```markdown
# Optional Dependencies

mcp-coder uses PyPI [extras](https://peps.python.org/pep-0508/) to gate
optional features behind opt-in installs. This page lists every extra the
project publishes.

> Note: The `[mcp]` section in `config.toml` (runtime `default_config_path`)
> is unrelated to pip extras and is not covered here — see
> `docs/configuration/config.md`.

## Extras overview

| Extra | What it enables | When to install |
|---|---|---|
| `types` | mypy type-stub packages | Local dev (PROJECT venv), for mypy type resolution |
| `test`  | pytest plugins (`pytest-asyncio`, `pytest-xdist`, textual-snapshot) | Local test runs |
| `mlflow` | MLflow conversation logging + analytics | Enabling MLflow integration |
| `tui`    | `textual-dev` dev tooling | Hacking on the iCoder TUI |
| `langchain-base` | langchain-core + MCP adapters + langgraph + httpx + truststore — **shared runtime** | Rarely installed directly; a building block for the per-provider extras |
| `langchain-openai` | `[langchain-base]` + OpenAI wrapper (`tiktoken` transitive) | Using OpenAI via LangChain |
| `langchain-gemini` | `[langchain-base]` + Google GenAI wrapper (`grpcio`, `protobuf` transitive — heavy native wheels) | Using Gemini via LangChain |
| `langchain-anthropic` | `[langchain-base]` + Anthropic wrapper (pure Python, small) | Using Anthropic via LangChain without OpenAI/Google dependencies |
| `langchain-ollama` | `[langchain-base]` + Ollama wrapper | Using Ollama via LangChain (backend integration in progress) |
| `langchain` | Meta: all four `[langchain-*]` providers | Full LangChain install (identical to historical `[langchain]`) |
| `dev` | All of the above (except per-provider langchain splits) + lint/type tooling | Full local development setup |

## Naming note — `[langchain-gemini]` wraps `langchain-google-genai`

Extra names follow **user-facing terminology** (provider keys in user config,
env vars, internal module names: `gemini_backend.py`), not PyPI package
names. So:

- `[langchain-gemini]` → installs PyPI `langchain-google-genai`
- `[langchain-anthropic]` → installs PyPI `langchain-anthropic` (same name)
- `[langchain-openai]` → installs PyPI `langchain-openai` (same name)
- `[langchain-ollama]` → installs PyPI `langchain-ollama` (same name)

## Why split by provider?

- `langchain-google-genai` pulls `grpcio` + `protobuf` — heavy native wheels,
  sometimes blocked in corporate Python environments.
- `langchain-openai` pulls `tiktoken` (C extension).
- `langchain-anthropic` and `langchain-ollama` are small, pure-Python.

Splitting lets Anthropic-only or Ollama-only users avoid the native-wheel
cost. Users who want everything still `pip install mcp-coder[langchain]` and
get the identical package set as before.
```

### README.md change

Add one short section (near the existing "Installation" or "Documentation"
block):

```markdown
### Optional features

mcp-coder publishes several pip extras for optional integrations
(LangChain providers, MLflow logging, Textual dev tooling, …). See
[Optional Dependencies](docs/configuration/optional-dependencies.md) for
the full list and when to install each.
```

## HOW

1. Use `mcp__workspace__save_file` to create the new doc page.
2. Use `mcp__workspace__edit_file` on `README.md` with one edit inserting
   the "Optional features" subsection in a logical location
   (after the existing `pip install -e ".[dev]"` block or under the
   "Documentation" section's Quick Links list).

## ALGORITHM

N/A — pure documentation. Ensure both files use trailing newline and existing
markdown style (headings depth, table spacing).

## DATA

N/A.

## Verification

- `mcp__tools-py__run_pylint_check` — must still pass
- `mcp__tools-py__run_pytest_check` (fast subset) — must still pass
- `mcp__tools-py__run_mypy_check` — must still pass
- `mcp__tools-py__run_lint_imports_check` — must still pass
- Optional: `tools/lychee_check.bat` if link-checking is wired up locally —
  confirms `docs/configuration/optional-dependencies.md` link from README
  resolves.

## Commit

```
docs(config): add optional-dependencies page and README pointer

New docs/configuration/optional-dependencies.md enumerates every pip extra
the project publishes (what it enables, when to install, per-provider
trade-offs, extra-name vs PyPI-name mismatches). README gains a short
"Optional features" section pointing to the new page.

Closes #829
```
