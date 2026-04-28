# Summary — Issue #928: Globalise truststore + surface GITHUB_TOKEN source

## Goal

Two related changes that share a common motivation (corporate-network usability of
non-langchain HTTP):

1. **Globalise truststore activation.** Move `truststore` from the `[langchain-base]`
   extra into core dependencies, relocate `ensure_truststore()` from
   `mcp_coder.llm.providers.langchain._ssl` to `mcp_coder.utils.ssl_setup`, and call
   it once from `cli/main.py` before command dispatch. PyGithub, Jenkins, and any
   other in-process HTTP clients then benefit because
   `truststore.inject_into_ssl()` is a process-wide monkeypatch of
   `ssl.create_default_context`.

2. **Surface the GITHUB_TOKEN source** on `mcp-coder verify`'s GITHUB section.
   Upstream (`mcp-workspace#170`, merged) now emits `token_source: "env" | "config"`
   on the `token_configured` `CheckResult`. Render that on a second indented line
   below the existing `Token configured` row.

## Architectural / design changes

### Module relocation
- `ensure_truststore()` (and its `_injected` flag) move out of the langchain
  subpackage into `mcp_coder.utils.ssl_setup`. SSL bootstrap is no longer langchain
  business — it's a process-wide concern owned by `utils`.

### CLI as the boundary
- The single, canonical activation point becomes `mcp_coder.cli.main.main()`,
  inline between `setup_logging(...)` and the `try:` block. The 7 existing call
  sites inside the langchain subpackage are removed.
- **Why inline (not module-level):** keeps `--version` free of the SSL patch
  (argparse `_VersionAction` calls `sys.exit(0)` *during* `parse_args()`,
  before `main()`'s body runs), and ensures that *importing* `cli.main` does not
  trigger SSL injection (only running it does). `--help` still triggers the patch
  — accepted; the patch is fast and harmless.
- **Why `setup_logging` first:** `ensure_truststore()` emits a DEBUG log line on
  success.
- Library consumers (`from mcp_coder.* import ...`) are expected to self-activate
  by calling `ensure_truststore()` themselves.

### Dependency surface
- `truststore>=0.9.0` moves from `[project.optional-dependencies] langchain-base`
  to core `[project] dependencies`. It's now a hard requirement.

### Import-linter contract
- New dedicated `truststore_isolation` contract is added with `ignore_imports`
  permitting BOTH `mcp_coder.utils.ssl_setup -> truststore` (the global injector)
  AND `mcp_coder.llm.providers.langchain.** -> truststore` (the *non-injector*
  uses in `_http.py` for explicit `SSLContext()` per-client contexts and
  `_exceptions.py` for the `_truststore_available()` diagnostic probe — both
  stay in place).
- `truststore` is removed from `langchain_transitive_isolation`'s
  `forbidden_modules` list and its langchain ignore line.

### Verify-command rendering
- `_format_section()` in `cli/commands/verify.py` gains a 4-line special case
  keyed on `key == "token_configured"` to emit a second indented line at the
  value column when `entry["token_source"]` is present:
  - `"env"` → `from GITHUB_TOKEN env var`
  - `"config"` → `from ~/.mcp_coder/config.toml` (literal tilde)
- The upstream `value` (`configured (scopes: ...)`) stays on the main line.
- Out of scope (per Decision 11): conflict warning when token is set in both
  env *and* config. Requires upstream support; deferred.

### Documentation cleanup
- `_SSL_HINT` in `_exceptions.py` no longer references the non-existent
  `pip install mcp-coder[truststore]` extra; replaced with OS-trust-store +
  `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE` guidance.
- The doc comment in `gemini_backend.py:23-25` is updated to point at the new
  `mcp_coder.utils.ssl_setup` location.

### Out of scope
- Subprocess SSL (Claude CLI, formatter subprocesses) — `truststore` patches the
  in-process `ssl` module only.
- Refactoring `_http.py` / `_exceptions.py` to route their non-injector
  `truststore` usage through `ssl_setup` — the new import-linter contract
  accommodates them in place.
- `*.ghe.com` URL fix — tracked at `mcp-workspace#169`.
- Conflict-warning display when a token is set in both env *and* config —
  requires a new upstream field; tracked separately.

## Files created

- `src/mcp_coder/utils/ssl_setup.py`
- `tests/utils/test_ssl_setup.py` (relocated from
  `tests/llm/providers/langchain/test_langchain_ssl.py`)

## Files modified

- `pyproject.toml` — `truststore` moves from `[langchain-base]` to core deps.
- `.importlinter` — new `truststore_isolation` contract; trim
  `langchain_transitive_isolation`.
- `src/mcp_coder/cli/main.py` — inline `ensure_truststore()` call in `main()`.
- `src/mcp_coder/llm/providers/langchain/__init__.py` — drop `_ssl` import,
  remove 4 `ensure_truststore()` call sites.
- `src/mcp_coder/llm/providers/langchain/_models.py` — drop `_ssl` import,
  remove 3 `ensure_truststore()` call sites.
- `src/mcp_coder/llm/providers/langchain/_exceptions.py` — replace `_SSL_HINT`.
- `src/mcp_coder/llm/providers/langchain/gemini_backend.py` — refresh stale
  doc comment.
- `src/mcp_coder/cli/commands/verify.py` — render `token_source` second line
  in GITHUB section.
- `tests/cli/test_main.py` — test that `main()` calls `ensure_truststore()`.
- `tests/cli/commands/test_verify.py` — render tests for env / config sources.
- `tests/llm/providers/langchain/test_langchain_models.py` — delete
  `TestListModelsEnsureTruststore`; drop `patch(...ensure_truststore)` mocks.
- `tests/llm/providers/langchain/test_langchain_provider_system_messages.py` —
  delete `TestEnsureTruststoreCalled`; drop mocks.
- `tests/llm/providers/langchain/test_langchain_streaming.py` — drop mocks.
- `tests/llm/providers/langchain/test_langchain_streaming_timeout.py` — drop
  mocks.
- `tests/llm/providers/langchain/test_langchain_agent_timeout.py` — drop mocks.

## Files deleted

- `src/mcp_coder/llm/providers/langchain/_ssl.py`

## Steps overview

| # | Step | Scope |
|---|------|-------|
| 1 | Promote truststore to core dependencies | `pyproject.toml` |
| 2 | Create `ssl_setup` module + relocate tests + import-linter contract | new module, new contract, moved test file |
| 3 | Wire `ensure_truststore()` into `cli/main.main()` | CLI integration + test |
| 4 | Decommission langchain SSL plumbing | delete `_ssl.py`, remove 7 call sites, drop 5 test mocks, delete 2 obsolete test classes |
| 5 | Refresh SSL documentation | `_SSL_HINT` + gemini doc comment |
| 6 | Render GITHUB_TOKEN source in verify | `_format_section` special case + 2 tests |

Each step is one commit. Each passes `pylint`, `pytest` (fast unit pattern), `mypy`,
and `lint-imports` before being committed.
