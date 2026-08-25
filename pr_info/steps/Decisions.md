# Plan decisions

Resolutions applied after the round-5 review escalation
(`pr_info/plan_review_log_1.md`). Numbered independently of the issue's own
"Decision N" list.

## A. `_API_KEY_ENV` lists every credential variable the SDK accepts (step 5)

Directed fix. `azure` gains `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_AD_TOKEN`,
`gemini` gains `GOOGLE_API_KEY`. Verified in the project venv: both Azure
variables construct a client through `create_openai_model(api_key=None)`, and
`GOOGLE_API_KEY` alone constructs a `ChatGoogleGenerativeAI`. A narrower table
would raise a false required-error on setups that work today.

## B. Gemini's keyless case is an explicit carve-out, tested by presence (step 5)

Mine to choose ("simplest rule that cannot break a working setup").

Measured: `credentials` has no env default and `create_gemini_model` never
passes it, so ADC / `GOOGLE_APPLICATION_CREDENTIALS` / `GOOGLE_CLOUD_PROJECT`
cannot rescue a keyless construction — all still raise. The **only** keyless
path that works is `GOOGLE_GENAI_USE_VERTEXAI`. So a required-error stays
correct everywhere else, and `_KEYLESS_ENV` carves out just that variable.

Presence (any non-empty value), not truthiness: `=0`/`=false` do not enable
Vertex mode, but mirroring the SDK's parsing would risk the very false
required-error being fixed here, while over-permissiveness costs only a contract
message the user still gets from the SDK in already-actionable form.

## C. `describe_effective_config` receives the masked key, its source and `overridden` (step 7)

Directed fix. The builder stays pure formatting and never reads
`config["api_key"]`: the winning key is often the env var's while config.toml
holds a losing one, so masking the config value under an env-var label would
fabricate provenance. Masking stays in `verification.py`, which also avoids an
import back into `_config_diagnostics`.

## D. Contract findings win both `ok` and `value` (step 9)

Directed fix, resolving the HOW/ALGORITHM contradiction in favour of the
ALGORITHM. When a finding exists for `api_key`, the row renders the finding's
message; only the no-finding branch renders the masked key. The acceptance
criterion is "exit 1, naming the contract violation", which a `not set` value
cannot do. The contradicting HOW sentence is deleted, not reworded.

---

Resolutions applied after the run-2 review (`pr_info/plan_review_log_2.md`).

## E. `_resolve_api_key` is keyed by *mode*, matching the contract (steps 7, 9)

Directed fix. `_BACKEND_ENV_VARS` holds one variable per *backend*, while step
5's contract accepts a tuple per *mode* (`AZURE_OPENAI_API_KEY`,
`AZURE_OPENAI_AD_TOKEN`, `GOOGLE_API_KEY`, `GOOGLE_GENAI_USE_VERTEXAI`).
Verified against `verification.py:24-29,56-77`: an Azure setup keyed off
`AZURE_OPENAI_API_KEY` produces no contract finding *and* no resolved key, so
the echo would print `api_key   (not set)` and step 9's `scoped` default
`API key [OK] not set (optional)` — false provenance in the block whose purpose
is provenance, and "optional" contradicts the `required` contract row.

Mechanism chosen (the reviewer's preferred option, not the fallback): delete
`_BACKEND_ENV_VARS`, pass `mode_of(config)`, scan `_API_KEY_ENV[mode]` in order,
and name the variable that actually supplied the key. Gemini's keyless Vertex
carve-out has no readable key, so `_resolve_api_key` returns a source with a
`None` key and the rows render `satisfied via GOOGLE_GENAI_USE_VERTEXAI env var`
rather than `not set (optional)`. `not set (optional)` survives only for a
genuinely optional-and-unset `api_key` (ollama). Both steps state the same
mechanism.

## F. ollama's unset target resolves to the real default, not `(unknown)` (step 6)

Directed fix, first raised in run 1 round 4 and never applied. Measured:
`_resolve_ollama_host(None)` returns `None`, `create_ollama_model` omits the
kwarg (`ollama_backend.py:40-42`), and `ChatOllama(model=...).base_url` is
`None` (confirmed in the project venv) — so the most common ollama setup would
echo `base_url (unknown)` for a value `_models._check_ollama_daemon` already
assumes. The fallback becomes
`_resolve_ollama_host(config["base_url"]) or _OLLAMA_DEFAULT_URL`;
`_source_for` labels it with no special case. `(unknown)` survives only for a
constructed non-ollama client that exposes no URL.

## G. Step 8's DATA example matches its own algorithm (step 8)

Directed fix. `"https://api.openai.com/v1/".rstrip("/")` ends in `/v1`, so the
current code (`verification.py:165-170`) takes the healthy branch and returns
`ok=True` — the `[WARN] … most relays use .../v1` example was unreachable and
invited flipping the heuristic's severity. Replaced with the `[OK]` row plus a
genuinely-warning example, a note that a `/v1` URL can only be `[OK]`, and a TDD
case pinning it. The `(source: …)` suffix is now spelled out in all four
ALGORITHM branches, as HOW already required.

## H. The redirect-row guard reuses `_targets_match` (steps 6, 7)

Directed fix. Step 7 called an undeclared `_matches_config_base_url`. The
condition is expressed as `cfg_base and _targets_match(cfg_base, target.url)`,
and `_targets_match` is promoted into step 6's declared module surface — the
same predicate `_source_for` uses, so the two cannot drift.
