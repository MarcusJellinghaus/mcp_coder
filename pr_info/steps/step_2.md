# Step 2 — `ApprovalModal` widget

## Goal

A self-contained `ModalScreen` that shows one pending tool call and returns the user's typed
`ApprovalDecision`, or `None` when the user cancels the turn. No wiring yet — step 3 pushes it.

## WHERE

| File | Change |
|---|---|
| `src/mcp_coder/icoder/ui/widgets/approval_modal.py` | **new** |
| `tests/icoder/test_app_pilot.py` | new tests in the approval section (from `:1591`) |

## WHAT

```python
DISCLAIMER_TEMPLATE: str

def build_prompt_text(
    tool_name: str, source: str, persist_target: Path
) -> str: ...

def format_args_full(args: dict[str, object]) -> str: ...

class ApprovalModal(ModalScreen[Optional[ApprovalDecision]]):
    DEFAULT_CSS: str
    BINDINGS: list[Binding]

    def __init__(
        self,
        *,
        tool_name: str,
        args: dict[str, object],
        source: str,
        persist_target: Path,
    ) -> None: ...

    def compose(self) -> ComposeResult: ...
    def action_allow_once(self) -> None: ...
    def action_allow_session(self) -> None: ...
    def action_allow_persist(self) -> None: ...
    def action_deny_once(self) -> None: ...
    def action_cancel_turn(self) -> None: ...
    def action_copy_selection(self) -> None: ...
```

`Optional[ApprovalDecision]`, not `ApprovalDecision | None`: a base-class subscript is evaluated
at runtime, and this matches the cited template `SessionPickerScreen(ModalScreen[Optional[Path]])`.
Typing it `[ApprovalDecision]` would be a `mypy --strict` failure on line one, because `5` must
dismiss with `None` — `ApprovalDecision.outcome` is `Literal["allow", "deny"]` and there is no
cancel outcome.

## HOW — integration points

```python
from mcp_coder.icoder.permissions.approval import ApprovalDecision
```

**`detail_modal._format_args` is deliberately NOT reused.** It renders each value through
`stream_renderer._render_value_full`, which truncates a single-line string longer than 120
characters to `value[:117] + "..."`. That is right for a read-after-the-fact inspection modal and
wrong here: the user makes a security decision on what the modal shows, and a long one-line
command, URL or JSON blob is exactly the case where the tail matters. Truncated text is not
"reachable by scrolling" — the characters are gone before the widget sees them.

`format_args_full` is therefore authored in this module: the same block shape as `_format_args`
(`"Args:"` header, `  key: value`, multi-line values indented under their key), but values are
rendered **verbatim** — no length test, no ellipsis. Long lines wrap/scroll inside the `TextArea`,
which is what makes the full text reachable.

This is what #1046's full-args acceptance criterion asks for: *the args widget's text contains
every argument value verbatim, with no truncation or ellipsis.* It is a containment property, not
an equality one — the widget also carries the `"Args:"` header and the key prefixes.

```
if not args: return "Args: (none)"
lines = ["Args:"]
for key, value in args.items():
    text = value if isinstance(value, str) else json.dumps(value, indent=2, default=repr)
    rendered = text.splitlines() or [""]
    if len(rendered) == 1:  lines.append(f"  {key}: {rendered[0]}")
    else:                   lines += [f"  {key}:"] + [f"    {sub}" for sub in rendered]
return "\n".join(lines)
```

`detail_modal.py` stays untouched: its truncation is correct for its own screen, so this is a new
sibling formatter, not a change to a shared one.

Bindings — the digit bindings carry `priority=True` so a focused `TextArea` cannot swallow them,
and `ctrl+c` carries `priority=True` to shadow `ICoderApp`'s `ctrl+c → action_noop` (precedent:
`detail_modal.py:143`). `escape` needs no priority: screen bindings are checked before app
bindings, which is exactly why choice `5` exists — `Esc` shadows `ICoderApp`'s
`escape → action_cancel_stream`, so the modal must not take away the user's only way to abandon
a turn.

```python
BINDINGS = [
    Binding("1", "allow_once", "Allow once", priority=True),
    Binding("2", "allow_session", "Session", priority=True),
    Binding("3", "allow_persist", "Persist", priority=True),
    Binding("4", "deny_once", "Deny", priority=True),
    Binding("5", "cancel_turn", "Cancel turn", priority=True),
    Binding("escape", "deny_once", "Deny", show=False),
    Binding("ctrl+c", "copy_selection", "Copy", priority=True),
]
```

`compose` yields one `Container` holding exactly two widgets:

```python
yield Container(
    Static(build_prompt_text(...), id="approval-prompt"),
    TextArea(format_args_full(self._args), read_only=True, id="approval-args"),
    classes="approval-modal-container",
)
```

`Static` cannot scroll or be selected; `TextArea` gives both, which is what makes the full args
reachable and copyable. That is the only reason there are two widgets rather than one.

`action_copy_selection` is the five-line body from `detail_modal.py`: query the `TextArea`
(returning early on `NoMatches`), and `self.app.copy_to_clipboard(selected or text_area.text)`.
`DEFAULT_CSS` follows `DetailModal`'s (`align: center middle`, 80%/80% container, `#262626`).

## ALGORITHM — `build_prompt_text`

```
lines  = ["Approve tool call?", "", f"Tool:   {tool_name}", f"Source: {source}", ""]
lines += [DISCLAIMER_TEMPLATE.format(tool=tool_name), ""]
lines += ["  1  allow once",
          "  2  allow + remember (session)",
          "  3  allow + remember (persist)",
          f'       will add \"allow\": \"{tool_name}\" to {persist_target}',
          "  4  deny once",
          "  5  cancel this turn        (Esc = deny once · Ctrl+C = copy)"]
return "\n".join(lines)
```

The persist confirmation is this always-visible line, not a second screen: the issue settles that
"the modal choice *is* the explicit apply", so the confirmation is text to display before the user
commits, not a keystroke to collect. It shows both the resolved target file and a one-line summary
of the pending write.

```python
DISCLAIMER_TEMPLATE = (
    "⚠ Remembering allows every future call to {tool} — "
    "with any arguments, not just these."
)
```

## DATA

| Action | Dismiss value |
|---|---|
| `action_allow_once` | `ApprovalDecision("allow", "once")` |
| `action_allow_session` | `ApprovalDecision("allow", "session")` |
| `action_allow_persist` | `ApprovalDecision("allow", "persist")` |
| `action_deny_once` | `ApprovalDecision("deny", "once")` — `reason` left at its `None` default |
| `action_cancel_turn` | `None` |

`reason` must stay `None` for a real user deny: it exists only to override the gateway's deny
wording for the two producers that deny *without* asking anybody.

## TDD — tests first

Add to the approval section of `tests/icoder/test_app_pilot.py`, under the file's existing
module-level `pytestmark`. Wiring does not exist yet, so each test pushes the modal directly:

```python
app = ICoderApp(AppCore(llm_service=fake_llm, event_log=event_log))
async with app.run_test() as pilot:
    got: list[ApprovalDecision | None] = []
    app.push_screen(
        ApprovalModal(
            tool_name="mcp__srv__do_it",
            args={"path": "a.txt", "cmd": "x" * 300},
            source="project",
            persist_target=tmp_path / ".icoder" / "settings.local.json",
        ),
        got.append,
    )
    await pilot.pause()
```

| Test | Asserts |
|---|---|
| `test_approval_modal_states_the_over_grant` | `"with any arguments"` **and** `"mcp__srv__do_it"` are both in the `#approval-prompt` text. Substrings only, so copy-editing does not break it. |
| `test_approval_modal_args_widget_holds_full_args` | build `args = {"path": "a.txt", "cmd": "x" * 300}` (a single-line value well over 120 chars); assert the **raw value** `"x" * 300` is a substring of `query_one("#approval-args", TextArea).text`, that the key `"cmd"` is present, and that `"..."` does not appear in the widget text. Assert against the raw input, never against the formatter's own output — comparing with `format_args_full(args)` would pass identically if the formatter truncated, which is the bug this test exists to catch. |
| `test_approval_modal_shows_persist_target_and_summary` | the prompt text contains `str(persist_target)`, `"allow"` and the tool name |
| `test_approval_modal_choice_dismisses_with_decision` | **parametrised** over `("1", "allow", "once")`, `("2", "allow", "session")`, `("3", "allow", "persist")`, `("4", "deny", "once")`, `("escape", "deny", "once")` — one `pilot.press(key)`, then the captured decision's `outcome`/`scope`, and `reason is None` |
| `test_approval_modal_cancel_dismisses_with_none` | `pilot.press("5")` captures exactly `None` |
| `test_approval_modal_ctrl_c_copies_and_does_not_dismiss` | monkeypatch `app.copy_to_clipboard` to record; after `pilot.press("ctrl+c")` the recorder is non-empty **and** nothing was captured (the screen is still open) |

## Acceptance

- All six tests pass under `markers=["textual_integration"]`.
- pylint / mypy(strict) / ruff-docstrings / lint-imports clean.
- `approval_modal.py` well under the 750-line CI gate (expect ~120 lines).

## Commit

`feat(icoder): add the reactive approval modal (#1046)`

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`.
>
> Implement step 2 only: create `src/mcp_coder/icoder/ui/widgets/approval_modal.py` with
> `DISCLAIMER_TEMPLATE`, `build_prompt_text`, `format_args_full` and `ApprovalModal`, exactly as
> specified under WHAT, HOW, ALGORITHM and DATA. Do not wire it into `ui/stream_view.py` — that is
> step 3. Do not modify `ui/widgets/detail_modal.py`, and do **not** import its `_format_args`:
> it truncates long single-line values through `_render_value_full`, which would defeat #1046's
> full-args acceptance criterion — "the args widget's text contains every argument value verbatim,
> with no truncation or ellipsis". Author `format_args_full` here and render values verbatim.
>
> Work TDD: first add the six tests from the table to the approval section of
> `tests/icoder/test_app_pilot.py` (they push the modal directly with `app.push_screen`), watch
> them fail, then write the module.
>
> One detail to verify rather than assume: that `pilot.press("1")` reaches the screen binding
> rather than the focused read-only `TextArea`. `priority=True` on the digit bindings should make
> this correct, but confirm it with the parametrised test; if it fails, do not restructure the
> widgets — check the binding declaration first.
>
> Run `run_format_code`, then pylint, mypy(strict), ruff, lint-imports and the
> `textual_integration` test selection. Make exactly one commit when everything passes.
