# Step 10 — Launchers, reinstall hints, `llm/env.py` docstring (Scope 2)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_10.md`).
> Implement Step 10 only: the five repo-root launchers warn and continue when
> mcp-tools-py is missing and guard its `--version` line; the reinstall hints
> and the `llm/env.py` docstring name `mcp-coder[python]`. No Python logic
> changes. Run format, pylint, mypy and the fast pytest set (a test may pin
> launcher text). One commit.

## WHERE

- `claude.bat` (Step 4 / 4b), `claude_local.bat`, `icoder_local.bat` (Step 5 / 5b)
- `claude.sh` (Step 4 / 4b), `claude_local.sh` (Step 5 / 5b)
- `tools/reinstall_local.bat` (line ~18), `tools/reinstall_local.sh` (line ~34)
- `src/mcp_coder/llm/env.py` (docstring, line ~23)

## WHAT

`.bat` check block (replace the `ERROR` + `exit /b 1` block):

```bat
if not exist "!MCP_CODER_VENV_PATH!\mcp-tools-py.exe" (
    echo WARNING: mcp-tools-py.exe not found in !MCP_CODER_VENV_PATH! - only Python projects need it
    echo To install: pip install "mcp-coder[python]"
)
```

- `claude.bat` hint: `pip install "mcp-coder[python]"`.
- `claude_local.bat` / `icoder_local.bat` hint stays `Please run: tools\reinstall_local.bat`.

`.bat` version line:

```bat
if exist "!MCP_CODER_VENV_PATH!\mcp-tools-py.exe" "!MCP_CODER_VENV_PATH!\mcp-tools-py.exe" --version
```

`.sh` check block:

```sh
if [ ! -x "$MCP_CODER_VENV_PATH/mcp-tools-py" ]; then
    echo "WARNING: mcp-tools-py not found in $MCP_CODER_VENV_PATH - only Python projects need it"
    echo 'To install: pip install "mcp-coder[python]"'
fi
if [ -x "$MCP_CODER_VENV_PATH/mcp-tools-py" ]; then "$MCP_CODER_VENV_PATH/mcp-tools-py" --version; fi
```

`claude_local.sh` keeps `Please run: tools/reinstall_local.sh` as its hint.
Hints for a missing mcp-coder or mcp-workspace are unchanged.

Reinstall hints: `(pip install mcp-coder^)` → `(pip install "mcp-coder[python]"^)` in
the `.bat` (keep the `^` escapes); `(pip install mcp-coder)` →
`(pip install "mcp-coder[python]")` in the `.sh`.

`llm/env.py`: "co-installed with mcp-coder" → mcp-tools-py comes with the
`mcp-coder[python]` extra (keep the rest of the sentence's reasoning).

## HOW

Edit with `edit_file`. Preserve each file's line endings (the tool keeps them).
In `.bat` blocks, `"mcp-coder[python]"` needs no escaping; parentheses inside
an `if ( ... )` block do.

## DATA / ALGORITHM

None.

## Tests

If a test pins launcher text (`search_files(pattern="mcp-tools-py", glob="tests/**/*.py")`),
update it. Otherwise no new tests: these are shell scripts.
