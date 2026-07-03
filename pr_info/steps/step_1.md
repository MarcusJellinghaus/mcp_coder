# Step 1 — `SessionSpec` type + spec read/write helpers

Read `pr_info/steps/summary.md` first. This step adds the typed launch-time/
run-time contract. Additive only — nothing else changes yet.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/types.py` (add to existing module)
- `tests/workflows/vscodeclaude/test_session_spec.py` (new)

## WHAT
```python
@dataclass(frozen=True)
class SessionSpec:
    issue_number: int
    title: str
    repo: str
    status: str
    issue_url: str
    emoji: str
    commands: list[str]
    timeout: int
    mcp_config: str                 # e.g. ".mcp.json" / ".mcp.linux.json"
    install_script_path: str        # resolved tools/install.py
    mcp_coder_install_path: str     # coordinator install dir (holds .venv)
    skip_github_install: bool
    is_intervention: bool

SESSION_SPEC_FILENAME: str = ".vscodeclaude_session.json"

def write_session_spec(folder: Path, spec: SessionSpec) -> Path: ...
def read_session_spec(folder: Path) -> SessionSpec: ...
```

## HOW
- Keep everything in `types.py` (no new module) — it already holds the feature's
  dataclasses/TypedDicts.
- `write_session_spec` / `read_session_spec` use `dataclasses.asdict` + `json`.
  No custom (de)serializers, no `version` field (spec is ephemeral, gitignored,
  regenerated every restart).
- Import `json` and `dataclasses.asdict`, `pathlib.Path` at top of module.

## ALGORITHM
```
write: path = folder / SESSION_SPEC_FILENAME
       path.write_text(json.dumps(asdict(spec), indent=2), encoding="utf-8")
       return path
read:  data = json.loads((folder / SESSION_SPEC_FILENAME).read_text("utf-8"))
       return SessionSpec(**data)   # commands stays a list
```

## DATA
- `write_session_spec` -> `Path` to the written JSON file.
- `read_session_spec` -> `SessionSpec` (frozen).

## TESTS (write first)
- Round-trip: build a `SessionSpec`, `write_session_spec(tmp_path, spec)`,
  `read_session_spec(tmp_path)` == original (including `commands` list and both
  bools).
- File is named `.vscodeclaude_session.json` and contains valid JSON.
- `commands=[]` and multi-element `commands` both round-trip.

## LLM PROMPT
> Implement Step 1 from `pr_info/steps/step_1.md` (context in
> `pr_info/steps/summary.md`). Add a frozen `SessionSpec` dataclass and
> `write_session_spec` / `read_session_spec` helpers (asdict + json, no custom
> serializers, no version field) to
> `src/mcp_coder/workflows/vscodeclaude/types.py`, plus
> `SESSION_SPEC_FILENAME`. Write `tests/workflows/vscodeclaude/
> test_session_spec.py` first (round-trip incl. empty/multi commands and the
> filename). Use MCP workspace tools for all file ops. After each edit run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check`
> (`extra_args=["-n","auto","-m","not git_integration and not
> claude_cli_integration and not claude_api_integration and not
> formatter_integration and not github_integration and not
> langchain_integration"]`), and `mcp__tools-py__run_mypy_check`; fix all
> issues. One commit: tests + implementation + green checks.
