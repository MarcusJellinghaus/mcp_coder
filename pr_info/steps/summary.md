# Summary — #1179: `verify` reports branch protection as `[ERR]` when the token lacks the scope

## Goal

When the GitHub token cannot read branch protection (HTTP 403), `mcp-coder verify`
must show `[WARN] not verifiable` instead of `[ERR] not configured`, must not
print stray PyGithub log lines, and must not change the exit code.

## Context

The verdict comes from `verify_github` in **mcp-workspace**
(`src/mcp_workspace/github_operations/verification.py`). It is re-exported by
`src/mcp_coder/mcp_workspace_github.py`. The upstream fix (mcp-workspace#301,
already merged) now returns a three-state verdict for all five branch-protection
rows:

| HTTP | `ok` | `value` |
|------|------|---------|
| 200 | `True` | e.g. `main protected` |
| 404 (not protected) | `False` | `not configured` |
| 403 | `None` | `not verifiable — token lacks Administration: Read` |

All five rows are `severity="warning"`, so `overall_ok` is unaffected. mcp-workspace is
an unpinned git dependency, so no version bump is needed. Unit tests here build the
result dicts directly and do not depend on the reinstall.

## Architectural / design changes

- **Renderer (`_format_section`):** child-row suppression widens from "parent failed"
  (`bp_ok is False`) to "parent not confirmed" (`bp_ok is not True`). That one
  condition is the only logic change. `ok=None` rows already render as `[WARN]`
  without the `(error)` suffix through the existing generic branch.
- **Exit code:** no change. A regression test locks in that `ok=None`
  branch-protection rows with `overall_ok=True` give exit code 0.
- **Logging policy:** the `setup_logging` shim also raises `github.GithubRetry` to
  WARNING, next to the other third-party loggers it already manages. This hides the
  `Request GET … failed with 403` INFO line. Accepted side effect: PyGithub's INFO
  rate-limit backoff lines are hidden too.
- **Docs:** the token guidance in `docs/repository-setup/github.md` describes both a
  fine-grained PAT (with an explicit permission list) and a classic PAT with `repo`
  scope.

Out of scope: the permissions for #1180's security-settings rows, and
`docs/configuration/config.md`.

## Files modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/commands/verify_formatting.py` | `bp_ok is False` becomes `bp_ok is not True` |
| `tests/cli/commands/test_verify_format_section_basic.py` | add a 403 test and tag the existing 200 and 404 tests |
| `tests/cli/commands/test_verify_exit_codes_github.py` | add one regression test |
| `src/mcp_coder/utils/log_utils.py` | add the `github.GithubRetry` WARNING line |
| `tests/utils/test_log_utils_shim.py` | add one test |
| `docs/repository-setup/github.md` | rewrite the token permissions section |

No files or modules are created (apart from these planning docs).

## Steps

1. [step_1.md](step_1.md) — renderer: suppress child rows when the parent is unverifiable.
2. [step_2.md](step_2.md) — exit-code regression test.
3. [step_3.md](step_3.md) — silence the `github.GithubRetry` logger.
4. [step_4.md](step_4.md) — token documentation.
