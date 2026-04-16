# Step 4 — Documentation: optional-dependencies page + pointers from README and existing docs

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_4.md`).
> Implement ONLY step 4: create
> `docs/configuration/optional-dependencies.md`, add a short "Optional
> features" subsection to `README.md`, and add a one-line pointer to the
> new page at each of the three existing install-hint sites
> (`docs/configuration/config.md`, `docs/configuration/mlflow-integration.md`,
> `docs/architecture/architecture.md`). Do NOT modify code or config.
> After the edit, run pylint, pytest (fast), mypy, `lint-imports` — all
> must still pass (unrelated; mandated by CLAUDE.md).
> Commit: `docs(config): add optional-dependencies page and cross-link from README + existing docs`.

## WHERE

**Created:** `docs/configuration/optional-dependencies.md`

**Modified:**
- `README.md` — add a new `#### Optional features` subsection directly
  after the `pip install -e ".[dev]"` fenced block under `### Installation`
  and before the `## 📚 Documentation` heading.
- `docs/configuration/config.md` — add a one-line pointer near the existing
  `pip install 'mcp-coder[langchain]'` example (currently line 215, inside
  the `### [llm.langchain]` section). Re-check line numbers before editing —
  they may have shifted.
- `docs/configuration/mlflow-integration.md` — add a one-line pointer near
  the existing install block (currently around lines 11–18, inside the
  `## Installation` section). Re-check before editing.
- `docs/architecture/architecture.md` — add a one-line pointer near the
  existing `pip install 'mcp-coder[langchain]'` mention (currently line 193,
  in the `langchain/` bullet). Re-check before editing.

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

Insert a new subsection directly after the `pip install -e ".[dev]"` fenced
block under `### Installation` and before the `## 📚 Documentation` heading.
Use an `####` heading so it nests under `### Installation`:

```markdown
#### Optional features

mcp-coder publishes several pip extras for optional integrations
(LangChain providers, MLflow logging, Textual dev tooling, …). See
[Optional Dependencies](docs/configuration/optional-dependencies.md) for
the full list and when to install each.
```

### Cross-link pointers in existing docs

At each of the three existing install-hint sites, add one short sentence
(wording is the implementer's call — the requirement is that each page
acquires a visible pointer to the new reference). Suggested form:

> See [`docs/configuration/optional-dependencies.md`](./optional-dependencies.md)
> for per-provider extras (smaller footprints if you only need one backend).

Per-file targets (confirm line numbers with `mcp__workspace__read_file`
before editing — the three line numbers below are from plan-writing time):

- **`docs/configuration/config.md`** (around line 215): add the pointer
  just after the `pip install 'mcp-coder[langchain]'` fenced block, before
  the `| Field | Type | ...` table.
- **`docs/configuration/mlflow-integration.md`** (around line 17): add the
  pointer just after the install fenced block (lines 9–19), before the
  `## Configuration` heading. Use the neutral wording ("per-provider
  extras … smaller footprints") since this page is about `[mlflow]`, not
  `[langchain]` — the pointer is generic.
- **`docs/architecture/architecture.md`** (around line 193): add the
  pointer as a sibling bullet immediately after the
  `**Optional install**: `pip install 'mcp-coder[langchain]'`` bullet,
  inside the same `langchain/` sub-list.

## HOW

1. Use `mcp__workspace__save_file` to create the new doc page.
2. Use `mcp__workspace__edit_file` on `README.md` with one edit inserting
   the `#### Optional features` subsection directly after the
   `pip install -e ".[dev]"` fenced block under `### Installation`.
3. Use `mcp__workspace__edit_file` on each of the three existing docs
   (`config.md`, `mlflow-integration.md`, `architecture.md`) to insert the
   one-line pointer next to the existing install hint. Re-read each file
   first to confirm current line positions.

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
  confirms the four new links (from README and each of the three existing
  docs) to `docs/configuration/optional-dependencies.md` resolve.

### Acceptance criteria (step-level)

- [ ] `docs/configuration/optional-dependencies.md` exists and lists every
      extra published by `pyproject.toml` after step 2.
- [ ] `README.md` has a `#### Optional features` subsection under
      `### Installation`, linking to the new page.
- [ ] `docs/configuration/config.md` has a visible pointer to the new page
      near the `[langchain]` install hint.
- [ ] `docs/configuration/mlflow-integration.md` has a visible pointer to
      the new page near its install hint.
- [ ] `docs/architecture/architecture.md` has a visible pointer to the new
      page near the `langchain/` optional-install bullet.

## Commit

```
docs(config): add optional-dependencies page and cross-link from README + existing docs

New docs/configuration/optional-dependencies.md enumerates every pip extra
the project publishes (what it enables, when to install, per-provider
trade-offs, extra-name vs PyPI-name mismatches). README gains a short
"Optional features" subsection under Installation. The three existing docs
that currently mention an install hint (config.md, mlflow-integration.md,
architecture.md) each gain a one-line pointer to the new reference page.

Closes #829
```
