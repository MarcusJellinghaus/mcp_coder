# Step 6 — Documentation updates

This step lands the documentation changes required by issue #727.
No code changes — only `docs/configuration/config.md` and
`docs/configuration/optional-dependencies.md`.

## WHERE

**Modify:**
- `docs/configuration/config.md`
- `docs/configuration/optional-dependencies.md`

## WHAT (changes only)

### `docs/configuration/config.md`

**(a) Replace** the existing **Local Ollama** example (which
currently uses `backend = "openai"` + `/v1` endpoint as a workaround)
with a native Ollama example:

```toml
# Example — Local Ollama (native backend)
[llm]
provider = "langchain"

[llm.langchain]
backend  = "ollama"
model    = "llama3:latest"
# endpoint = "127.0.0.1:11434"  # optional — defaults to localhost:11434
# api_key  = "..."              # optional — only for proxy-auth setups
```

Append a note:

> **First-call slowness.** Ollama lazy-loads model weights from disk
> on the first request (seconds to minutes for multi-GB models);
> subsequent calls within `keep_alive` are fast. To work around this
> use any of:
>
> - `--timeout N` on the CLI to extend the request timeout
> - `OLLAMA_KEEP_ALIVE=-1` on the daemon to keep loaded models in
>   memory indefinitely
> - `ollama run <model>` ahead of time to pre-load the model
>
> The mcp-coder default timeout (30s) is unchanged.
>
> **`OLLAMA_HOST` env var.** Ollama's own convention uses bare
> `host:port` (e.g. `127.0.0.1:11434`) rather than a URL. mcp-coder
> normalizes this automatically — set either `endpoint` in
> config.toml (URL or `host:port`) or `OLLAMA_HOST` env var.

**(b) Update** the `backend` field's description in the
`[llm.langchain]` table to include `"ollama"`:

| `backend` | string | LangChain backend: `"openai"`, `"gemini"`, `"anthropic"`, or `"ollama"` | Yes |

**(c) Update** the Environment Variable Overrides table:

| `OLLAMA_API_KEY` | `[llm.langchain] api_key` | `ollama` |
| `OLLAMA_HOST` | `[llm.langchain] endpoint` | `ollama` |

### `docs/configuration/optional-dependencies.md`

In the extras-overview table, change:

> `langchain-ollama` | `[langchain-base]` + Ollama wrapper | Using
> Ollama via LangChain (backend integration in progress)

to:

> `langchain-ollama` | `[langchain-base]` + Ollama wrapper | Using
> Ollama via LangChain

(drop the "(backend integration in progress)" qualifier).

## HOW

Use `mcp__workspace__edit_file` for precise edits. Locate the
existing **Example — Local Ollama** section in `config.md` (currently
showing `backend = "openai"` + `endpoint =
"http://localhost:11434/v1"`) and replace the body. Add the
post-example notes immediately below. Update the two tables
described above.

For `optional-dependencies.md` the change is a single one-line
substitution.

## ALGORITHM

None — this is plain documentation editing.

## DATA

None — text-only changes.

## Tests

No automated tests for documentation. Manual checks:
- Render the Markdown locally (or just visually inspect) to confirm
  the table rows align.
- Search the file for any other references to the old "Local Ollama
  via OpenAI-compatible" wording and remove them if found.

## Definition of done

- The `config.md` Ollama example is native (no `backend = "openai"`
  workaround).
- The post-example notes about timeout / KEEP_ALIVE / pre-loading /
  `OLLAMA_HOST` are present.
- The env-var override table lists both `OLLAMA_API_KEY` and
  `OLLAMA_HOST`.
- The `optional-dependencies.md` row no longer says "backend
  integration in progress".
- `mcp__mcp-workspace__check_file_size` does not flag the docs
  (sanity check via the canonical MCP tool; docs are usually fine).
- All three MCP code-quality checks pass on the source tree (the
  doc edits should not affect them, but run them anyway).

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_6.md.

Implement Step 6 only — documentation changes only. No source code
or test changes.

Make the four edits described in the step:

1. config.md — replace the existing "Local Ollama via OpenAI-
   compatible" example with the native backend = "ollama" example.

2. config.md — add the post-example notes (first-call slowness +
   OLLAMA_HOST convention).

3. config.md — update the [llm.langchain] backend-field description
   and the Environment Variable Overrides table to include
   OLLAMA_API_KEY and OLLAMA_HOST.

4. optional-dependencies.md — drop the "(backend integration in
   progress)" qualifier from the langchain-ollama row.

Use mcp__workspace__edit_file with precise old_string anchors so
multiple matches are not ambiguous.

After the edits, run all three MCP code-quality checks (they should
not be affected, but verify zero new issues).
```
