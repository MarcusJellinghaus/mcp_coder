# Step 2 — Migrate icoder to Textual clipboard, delete `clipboard.py`, drop `pyperclip`

**Goal:** Move icoder's Ctrl+C copy off `pyperclip` onto Textual's native
clipboard, then delete `utils/clipboard.py` wholesale and remove `pyperclip` +
`types-pyperclip` from the project. One commit.

**Depends on Step 1** (the clipboard commit helpers must already be gone, so
`clipboard.py` has no consumer except icoder's `set_clipboard_text`).

TDD: update the icoder copy test first to express the new Textual behaviour, then
make the source change; delete `test_clipboard.py` alongside `clipboard.py`.

## WHERE

- `src/mcp_coder/icoder/ui/widgets/detail_modal.py`
- `tests/icoder/ui/test_detail_modal.py`
- `src/mcp_coder/utils/clipboard.py`  *(delete)*
- `tests/utils/test_clipboard.py`  *(delete)*
- `src/mcp_coder/utils/__init__.py`
- `pyproject.toml`
- `.importlinter`
- `docs/architecture/architecture.md`

## WHAT

- `detail_modal.py`:
  - Remove `from mcp_coder.utils.clipboard import set_clipboard_text`.
  - In `DetailModal.action_copy_selection`, replace the final
    `set_clipboard_text(selected if selected else text_area.text)` with
    `self.app.copy_to_clipboard(selected if selected else text_area.text)`.
  - Signature unchanged: `def action_copy_selection(self) -> None`.
- `tests/icoder/ui/test_detail_modal.py`: rewrite
  `test_modal_ctrl_c_copy_selection_calls_clipboard` to assert against Textual
  instead of `set_clipboard_text`. Patch the app method and assert it received the
  TextArea text:
  ```python
  async def test_modal_ctrl_c_copy_selection_calls_clipboard() -> None:
      app = _ModalApp(_tool_unit())
      async with app.run_test() as pilot:
          await pilot.pause()
          text_area = app.screen.query_one(TextArea)
          text_area.select_all()
          await pilot.pause()
          with patch.object(app, "copy_to_clipboard") as mock_copy:
              await pilot.press("ctrl+c")
              await pilot.pause()
      mock_copy.assert_called_once_with(text_area.text)
  ```
  Drop the `monkeypatch`/`_fake_copy` scaffolding and the `detail_modal` import if
  it becomes unused.
- Delete `src/mcp_coder/utils/clipboard.py` and `tests/utils/test_clipboard.py`.
- `utils/__init__.py`: remove the Layer-1 clipboard import
  ```python
  from .clipboard import (
      get_clipboard_text,
      parse_commit_message,
      validate_commit_message,
  )
  ```
  and the three corresponding names from `__all__` (the `# Clipboard operations`
  group). Keep the `# isort: skip_file` directive and all other layers intact.
- `pyproject.toml`:
  - remove `"pyperclip>=1.8.2",` from `[project] dependencies`.
  - remove `"types-pyperclip",` from `[project.optional-dependencies] types`.
  - remove the mypy override block:
    ```toml
    [[tool.mypy.overrides]]
    module = ["pyperclip"]
    ignore_missing_imports = true
    ```
- `.importlinter`: remove the entire
  `[importlinter:contract:pyperclip_isolation]` contract block.
- `docs/architecture/architecture.md`: remove the line
  `- **Clipboard operations**: utils/clipboard.py - ... (tests: utils/test_clipboard.py)`.

## HOW (integration points)

- `textual.app.App.copy_to_clipboard(text: str) -> None` exists and emits an
  OSC 52 escape sequence. `DetailModal` is a `ModalScreen`; reach the app via
  `self.app`. No new import needed.
- The Textual library-isolation contract already permits
  `mcp_coder.icoder.ui.** -> textual`, so this introduces no new import-linter
  violation.

## ALGORITHM

```
action_copy_selection():
    text_area = query_one(TextArea)   # return on NoMatches
    text = selected_text or text_area.text
    self.app.copy_to_clipboard(text)
```

## DATA

No data-structure changes. `pyperclip` and `types-pyperclip` are no longer
installed; clipboard behaviour is now OSC 52 (terminal-dependent).

## VERIFY

Run formatter, then pylint / mypy / pytest (`-n auto` unit subset; the modal test
is `textual_integration` — also run `markers=["textual_integration"]` once to
confirm the rewritten test passes) / lint-imports / vulture. `git grep pyperclip`
and `git grep clipboard` return only unrelated hits (none in `src`/`pyproject`/
`.importlinter`).

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement Step 2
> only: migrate `detail_modal.py` to `self.app.copy_to_clipboard(...)`, rewrite the
> Ctrl+C copy test accordingly, delete `utils/clipboard.py` and
> `tests/utils/test_clipboard.py`, drop the clipboard re-exports from
> `utils/__init__.py`, and remove `pyperclip` + `types-pyperclip` (dependency,
> type stub, mypy override, and the `pyperclip_isolation` import-linter contract)
> plus the `clipboard.py` line in `architecture.md`. Use MCP workspace tools. Run
> isort+black then `run_pylint_check`, `run_mypy_check`, `run_pytest_check`
> (unit subset `-n auto`, plus once with `markers=["textual_integration"]`),
> `run_lint_imports_check`, `run_vulture_check`. Fix until all pass, then one commit.
