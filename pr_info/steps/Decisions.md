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
