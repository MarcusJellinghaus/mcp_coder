# Step 19 — Documentation

`docs/configuration/config.md` currently encodes the confusion this issue
exists to prevent: the `[llm.langchain]` table (lines 326-332) documents
`endpoint` while *describing* it as "base URL", and the OpenAI-compatible-relay
example (lines 350-358) never warns against setting `api_version`.

## WHERE

- `docs/configuration/config.md` — the `[llm.langchain]` section and a new
  Troubleshooting section
- `docs/architecture/architecture.md` — the langchain module list under
  *Building Block View*

No test file. Verification is a careful read plus a grep.

## WHAT

Four edits to `config.md`:

1. **Field table** — `endpoint` → `base_url`, described as "Base URL of the
   server (`azure_endpoint` in Azure mode)". Add a line stating plainly that
   `endpoint` was renamed and no longer works, with the one-line migration
   (`endpoint = ...` → `base_url = ...`, and
   `MCP_CODER_LLM_LANGCHAIN_ENDPOINT` → `MCP_CODER_LLM_LANGCHAIN_BASE_URL`).
2. **Scenario → values table**, replacing the prose:

   | Setup | `base_url` | `api_version` | `model` | `api_key` |
   |---|---|---|---|---|
   | Plain OpenAI | omit | omit | model name | required (key / env) |
   | OpenAI-compatible relay (LiteLLM, vLLM) | `https://host/v1` | **omit** | relay alias | required (key / env) |
   | Azure OpenAI | `https://res.openai.azure.com/` | required | deployment | key / env |
   | Gemini / Anthropic | ignored | ignored | model name | key / env |
   | Ollama | optional (host) | ignored | model name | optional |

3. **Relay example warning** — *"Do not set `api_version` for a non-Azure server
   — it switches to Azure mode and requires `base_url`."* Update all four
   examples to use `base_url`.
4. **Config-overriding env vars** — a short list of the variables that change
   behaviour invisibly: `OPENAI_BASE_URL`, `OPENAI_API_BASE`,
   `AZURE_OPENAI_ENDPOINT`, `OLLAMA_HOST`, `OPENAI_API_KEY`,
   `MCP_CODER_LLM_PROVIDER`. Note that `mcp-coder verify` reports each of them.

Plus a new **Troubleshooting** section, symptom → cause:

| Symptom | Likely cause |
|---|---|
| `system messages must be at the beginning` | single-system provider + two system messages (#1116) |
| "connection error" to `api.openai.com` | `base_url` not set → public-OpenAI fallback (check for a stale `endpoint` key) |
| `unknown key: endpoint` | renamed to `base_url` |
| requests hit a host that is in no config file | `OPENAI_BASE_URL` / `OPENAI_API_BASE` / `OLLAMA_HOST` set in the environment |
| `404 - {"detail":"Not Found"}` | wrong `base_url` path (include the relay's prefix, e.g. `/v1`) |
| `Must provide one of base_url or azure_endpoint` | stray `api_version` → Azure mode without `base_url` (and no `AZURE_OPENAI_ENDPOINT`) |
| `Ensure Authorization has Bearer prefix` | curl only (add `Bearer `); the client adds it — don't put it in `api_key` |
| `no api_key ... and no OPENAI_API_KEY` on a relay | the OpenAI client cannot be built without credentials even for an unauthenticated relay — set any non-empty `api_key` |
| `Invalid model name passed in` | `model` not an alias the relay/proxy exposes |
| `verify` reports one provider but behaves like another | `MCP_CODER_LLM_PROVIDER` set in the environment, overriding `--llm-method` (fixed in 0.1.21) |
| `verify` passes but the real command fails | `verify` before 0.1.21 sent no system/project prompt, so it did not exercise the real message shape |

## HOW

- `architecture.md`: add one bullet to the `langchain/` list —
  `_config_diagnostics.py - per-backend config contract, resolved-target probe,
  effective-config echo`.
- Keep the existing `⚠️ base URL only — no /chat/completions` warning; it is
  still correct and now agrees with the key name.

## DATA

Documentation only.

## Verification

- `grep -rn "endpoint" docs/configuration/config.md` returns only the rename /
  migration note and the `azure_endpoint` mention.
- Every TOML example in the section uses `base_url`.
- The scenario table and the step-5 `_CONTRACT` table agree cell for cell — read
  them side by side; a divergence here is a documentation bug.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_19.md`.
> Implement step 19: update `docs/configuration/config.md` — document `base_url`
> with the `endpoint` rename and its one-line migration (config key **and** env
> var), replace the prose with the scenario→values table, add the "no
> `api_version` on non-Azure servers" warning to the relay example, list the env
> vars that override config invisibly, and add the symptom→cause Troubleshooting
> section. Update all TOML examples to `base_url`. Also add
> `_config_diagnostics.py` to the langchain module list in
> `docs/architecture/architecture.md`. Cross-check the scenario table against the
> `_CONTRACT` table from step 5 — they must agree cell for cell.
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
