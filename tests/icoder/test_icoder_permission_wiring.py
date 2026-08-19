"""Permission-gateway startup wiring + bypass guards (Step 5 of I2.3, TDD).

Three concerns are covered here:

* **Wiring** — ``execute_icoder`` loads the permission config once, constructs
  the gateway, injects its interceptor into ``MCPManager``, and hands the *same*
  gateway to ``RealLLMService`` (only on the ``langchain`` + ``mcp_config``
  path). Outside that path no config is loaded and ``gateway`` stays ``None``.
* **Ordering** — the adapter capability check fires *before* ``MCPManager``
  builds tools, so a ``<0.3.0`` adapter yields the clear ``ImportError`` rather
  than the raw ``TypeError`` at the first ``convert_...(tool_interceptors=...)``
  call.
* **Bypass guard (Decision D1)** — iCoder can never reach the un-instrumented
  ``convert_...`` site: site 3 (the ``run_agent_stream`` inline loader) is
  skipped whenever tools are supplied. The former site 2 (the non-stream
  ``run_agent``'s own loader) no longer exists — ``run_agent`` is now a thin
  drainer of ``run_agent_stream`` — so that half of the guard is structurally
  trivial, but the test is kept: it still pins the stream-only iCoder path.

The ``langchain_integration``-marked tests drive a real
``convert_mcp_tool_to_langchain_tool`` + interceptor path end to end, including a
graph-level deny test: a denied call leaves the message history paired, so
``create_react_agent`` does not raise ``INVALID_CHAT_HISTORY`` and the agent
continues past the deny.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.icoder.permissions import PermissionConfig
from tests.icoder.conftest import make_icoder_args, patch_icoder_deps

# ======================================================================
# Helpers
# ======================================================================


def _install_fake_manager(
    monkeypatch: pytest.MonkeyPatch, captured: list[dict[str, Any]]
) -> None:
    """Patch ``MCPManager`` so no real thread/loop starts; capture ctor args."""

    def fake_init(
        self: object, server_config: object, tool_interceptors: object = None
    ) -> None:
        captured.append(
            {"server_config": server_config, "tool_interceptors": tool_interceptors}
        )
        object.__setattr__(self, "_server_names", [])
        object.__setattr__(self, "_server_config", server_config)
        object.__setattr__(self, "_cached_tools", None)
        object.__setattr__(self, "_client", None)
        object.__setattr__(self, "_tool_counts", {})
        object.__setattr__(self, "_loop", None)
        object.__setattr__(self, "_thread", None)

    monkeypatch.setattr("mcp_coder.cli.commands.icoder.MCPManager.__init__", fake_init)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.MCPManager.close", lambda self: None
    )


def _capture_llm_kwargs(
    monkeypatch: pytest.MonkeyPatch, captured: list[dict[str, Any]]
) -> None:
    """Patch ``RealLLMService.__init__`` to record its keyword arguments."""

    def fake_init(self: object, **kwargs: Any) -> None:
        captured.append(kwargs)

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.RealLLMService.__init__", fake_init
    )


class _FakeMCPManager:
    """Minimal MCP manager stand-in: tools are their own canonical names."""

    def __init__(self, tool_names: list[str]) -> None:
        self._tools = list(tool_names)

    def tools(self) -> list[str]:
        return self._tools

    def canonical_name(self, tool: str) -> str | None:
        return tool


# ======================================================================
# Wiring
# ======================================================================


def test_icoder_loads_permission_config_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``load_permission_config`` is called exactly once with ``project_dir``."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    patch_icoder_deps(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder._load_mcp_server_config",
        lambda *_a, **_kw: {"srv": {"transport": "stdio"}},
    )
    _install_fake_manager(monkeypatch, [])

    calls: list[Path] = []

    def fake_load(project_dir: Path) -> PermissionConfig:
        calls.append(project_dir)
        return PermissionConfig()

    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.load_permission_config", fake_load
    )

    result = execute_icoder(make_icoder_args(tmp_path))

    assert result == 0
    assert calls == [Path(str(tmp_path)).resolve()]


def test_icoder_injects_interceptor_into_manager(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Manager gets ``[gateway.interceptor]``; the same gateway reaches the service."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    patch_icoder_deps(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder._load_mcp_server_config",
        lambda *_a, **_kw: {"srv": {"transport": "stdio"}},
    )

    created: list[Any] = []

    class _FakeGateway:
        def __init__(self, config: Any) -> None:
            self.config = config
            self.interceptor = object()  # stable sentinel identity
            created.append(self)

    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.LangchainEnforcementGateway", _FakeGateway
    )

    manager_calls: list[dict[str, Any]] = []
    _install_fake_manager(monkeypatch, manager_calls)
    llm_calls: list[dict[str, Any]] = []
    _capture_llm_kwargs(monkeypatch, llm_calls)

    result = execute_icoder(make_icoder_args(tmp_path))

    assert result == 0
    assert len(created) == 1
    gateway = created[0]
    assert len(manager_calls) == 1
    assert manager_calls[0]["tool_interceptors"] == [gateway.interceptor]
    assert len(llm_calls) == 1
    assert llm_calls[0]["gateway"] is gateway


def test_icoder_no_gateway_without_langchain(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Non-langchain provider -> gateway is None; config is never loaded."""
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    patch_icoder_deps(monkeypatch, tmp_path)
    # Force the claude provider with no MCP config: the langchain branch is skipped.
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_llm_method",
        lambda _: ("claude", None),
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.parse_llm_method_from_args",
        lambda _: "claude",
    )
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.resolve_mcp_config_path",
        lambda *a, **_kw: None,
    )

    load_calls: list[Path] = []

    def fake_load(project_dir: Path) -> PermissionConfig:
        load_calls.append(project_dir)
        return PermissionConfig()

    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder.load_permission_config", fake_load
    )
    manager_calls: list[dict[str, Any]] = []
    _install_fake_manager(monkeypatch, manager_calls)
    llm_calls: list[dict[str, Any]] = []
    _capture_llm_kwargs(monkeypatch, llm_calls)

    result = execute_icoder(make_icoder_args(tmp_path))

    assert result == 0
    assert load_calls == []
    assert manager_calls == []
    assert len(llm_calls) == 1
    assert llm_calls[0]["gateway"] is None
    assert llm_calls[0]["mcp_manager"] is None


def test_icoder_asserts_adapter_capability_before_manager(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The capability check precedes ``MCPManager`` construction (ordering fix).

    With ``_assert_tool_interceptors_supported`` patched to raise ``ImportError``,
    the manager (patched) is **never** constructed — proving the check runs before
    the first ``convert_...(tool_interceptors=...)`` the manager would trigger.
    """
    from mcp_coder.cli.commands.icoder import execute_icoder

    (tmp_path / "logs").mkdir()
    patch_icoder_deps(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder._load_mcp_server_config",
        lambda *_a, **_kw: {"srv": {"transport": "stdio"}},
    )
    manager_calls: list[dict[str, Any]] = []
    _install_fake_manager(monkeypatch, manager_calls)

    def _boom() -> None:
        raise ImportError("requires langchain-mcp-adapters>=0.3.0")

    monkeypatch.setattr(
        "mcp_coder.cli.commands.icoder._assert_tool_interceptors_supported", _boom
    )

    result = execute_icoder(make_icoder_args(tmp_path))

    assert result == 1  # ImportError caught by the top-level CLI boundary
    assert manager_calls == []  # manager never reached


# ======================================================================
# Bypass guard (Decision D1)
# ======================================================================


def test_icoder_stream_always_provides_manager_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """iCoder always hands ``prompt_llm_stream`` non-None tools (never site 3).

    The ``run_agent_stream`` inline loader (site 3) only runs when ``tools is
    None``; because ``RealLLMService`` always supplies the manager's tools, the
    inline loader is structurally unreachable from iCoder.
    """
    from mcp_coder.icoder.services.llm_service import RealLLMService

    captured: dict[str, Any] = {}

    def mock_stream(question: str, **kwargs: Any) -> Any:
        captured.update(kwargs)
        yield {"type": "done"}

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream", mock_stream
    )
    service = RealLLMService(
        provider="langchain",
        mcp_manager=_FakeMCPManager(["mcp__srv__a", "mcp__srv__b"]),  # type: ignore[arg-type]
    )

    list(service.stream("hi"))

    assert captured["tools"] is not None
    assert captured["tools"] == ["mcp__srv__a", "mcp__srv__b"]


def test_icoder_path_is_stream_only_never_run_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Driving ``RealLLMService.stream`` never invokes the non-stream ``run_agent``.

    ``run_agent`` is reachable only via the non-stream ``prompt_llm`` path.
    iCoder streams, so its turn routes ``RealLLMService.stream`` ->
    ``prompt_llm_stream`` -> ``ask_langchain_stream`` and can never reach
    ``run_agent``. Now that ``run_agent`` is a thin drainer of
    ``run_agent_stream`` it has no ``convert_...`` loader of its own, so this
    guard is structurally trivial — it is kept as a regression pin on the
    stream-only path.
    """
    from mcp_coder.icoder.services.llm_service import RealLLMService

    # Avoid an ambient provider override leaking from the environment.
    monkeypatch.delenv("MCP_CODER_LLM_PROVIDER", raising=False)

    reached: list[bool] = []

    async def _boom_run_agent(*_a: Any, **_k: Any) -> Any:
        reached.append(True)
        raise AssertionError("run_agent must be unreachable from iCoder")

    monkeypatch.setattr(
        "mcp_coder.llm.providers.langchain.agent.run_agent", _boom_run_agent
    )

    def fake_stream(question: str, **_kwargs: Any) -> Any:
        # Mirrors the real langchain stream entry, which uses run_agent_stream.
        yield {"type": "done", "session_id": "sess-1"}

    monkeypatch.setattr(
        "mcp_coder.llm.providers.langchain.ask_langchain_stream", fake_stream
    )

    service = RealLLMService(
        provider="langchain",
        mcp_config="/fake/.mcp.json",
        mcp_manager=_FakeMCPManager(["mcp__srv__a"]),  # type: ignore[arg-type]
    )

    events = list(service.stream("hi"))

    assert any(e["type"] == "done" for e in events)
    assert reached == []


# ======================================================================
# Integration (real convert_... + interceptor path)
# ======================================================================


@pytest.mark.langchain_integration
@pytest.mark.asyncio
async def test_gateway_denies_never_call_through_real_convert() -> None:
    """End-to-end: a ``never`` tool denies through the real converter path.

    Builds a langchain tool from a fake in-process MCP tool via the real
    ``convert_mcp_tool_to_langchain_tool`` with the gateway interceptor attached,
    then invokes it:

    * a config denying the tool -> invoking yields ``ToolMessage(status="error")``
      and does **not** raise;
    * an ``always`` tool returns the same result as with no gateway;
    * the turn-level canonical stamp (``MCPManager.canonical_name``) equals the
      interceptor-reconstructed ``f"mcp__{server}__{request.name}"`` — pinning the
      turn-vs-call identity assumption to a fact through the real path.
    """
    from types import SimpleNamespace
    from typing import cast

    # Real adapter + MCP SDK required: skip (not error) when they are absent so
    # explicitly selecting the marker on a base install is a clean skip.
    pytest.importorskip("langchain_mcp_adapters")
    pytest.importorskip("mcp")

    from langchain_mcp_adapters.tools import (  # pylint: disable=import-error
        convert_mcp_tool_to_langchain_tool,
    )
    from mcp.types import CallToolResult  # pylint: disable=import-error
    from mcp.types import Tool as MCPTool  # pylint: disable=import-error

    from mcp_coder.icoder.permissions import (
        Matcher,
        PermissionConfig,
        Policy,
        Rule,
    )
    from mcp_coder.icoder.permissions.gateway import LangchainEnforcementGateway
    from mcp_coder.llm.providers.langchain.mcp_manager import MCPManager

    server = "srv"
    # Build via model_validate (alias-aware) so the on-disk MCP field names
    # (``inputSchema``, ``isError``) parse cleanly regardless of the model's
    # Python attribute aliases.
    fake_tool = MCPTool.model_validate(
        {
            "name": "do_it",
            "description": "",
            "inputSchema": {"type": "object", "properties": {}},
        }
    )
    tool_call = {"name": fake_tool.name, "args": {}, "id": "c1", "type": "tool_call"}

    def _rule(policy: Policy) -> Rule:
        return Rule(
            matcher=Matcher(server=server, tool=fake_tool.name),
            policy=policy,
            layer="user",
        )

    class _FakeSession:
        """Fake MCP session whose ``call_tool`` returns a fixed result."""

        async def call_tool(
            self, name: str, args: dict[str, Any], progress_callback: Any = None
        ) -> CallToolResult:
            return CallToolResult.model_validate(
                {
                    "content": [{"type": "text", "text": "ran-ok"}],
                    "isError": False,
                }
            )

    # --- never: denied at call level, no raise, canonical identity captured ---
    deny_gateway = LangchainEnforcementGateway(
        PermissionConfig(rules=(_rule(Policy.NEVER),))
    )
    captured: dict[str, Any] = {}

    async def _capturing_interceptor(request: Any, handler: Any) -> Any:
        captured["request"] = request
        return await deny_gateway.interceptor(request, handler)

    deny_tool = convert_mcp_tool_to_langchain_tool(
        None,
        fake_tool,
        connection={"transport": "stdio"},
        server_name=server,
        tool_interceptors=[_capturing_interceptor],
    )
    deny_msg = await deny_tool.ainvoke(tool_call)
    assert deny_msg.status == "error"

    request = captured["request"]
    reconstructed = f"mcp__{request.server_name}__{request.name}"
    stamped = {
        **(deny_tool.metadata or {}),
        "mcp_canonical_name": f"mcp__{server}__{fake_tool.name}",
    }
    turn_stamp = MCPManager.canonical_name(
        cast(Any, None), SimpleNamespace(metadata=stamped)
    )
    assert turn_stamp == reconstructed

    # --- always: passes through unchanged (same result as with no gateway) ---
    allow_gateway = LangchainEnforcementGateway(
        PermissionConfig(rules=(_rule(Policy.ALWAYS),))
    )
    with_gate = convert_mcp_tool_to_langchain_tool(
        _FakeSession(),
        fake_tool,
        server_name=server,
        tool_interceptors=[allow_gateway.interceptor],
    )
    without_gate = convert_mcp_tool_to_langchain_tool(
        _FakeSession(),
        fake_tool,
        server_name=server,
        tool_interceptors=None,
    )
    with_msg = await with_gate.ainvoke(tool_call)
    without_msg = await without_gate.ainvoke(tool_call)

    assert with_msg.status != "error"
    assert with_msg.content == without_msg.content


@pytest.mark.langchain_integration
@pytest.mark.asyncio
async def test_denied_call_keeps_history_paired_and_agent_continues() -> None:
    """Graph level: a denied call stays paired, so the agent continues past it.

    Drives a scripted ``BaseChatModel`` through a real ``create_react_agent`` /
    ``ToolNode`` over a tool built by the real
    ``convert_mcp_tool_to_langchain_tool`` with the real gateway interceptor. The
    deny ``ToolMessage`` must carry the emitted ``tool_call_id`` — otherwise the
    model's tool_call is unpaired and ``create_react_agent`` raises
    ``INVALID_CHAT_HISTORY`` on the next turn, wedging the agent.

    Assertions read the **graph state** returned by ``ainvoke``, never the
    stream: ``run_agent_stream`` masks the empty id in its ``tool_result`` event
    via ``run_id``, so a stream-only assertion passes even with the bug present.
    The deny-text and captured-request assertions are load-bearing —
    ``ToolNode``'s own error message is also a ``ToolMessage(status="error")``
    with the correct id, so without them the test would pass green even if the
    interceptor was never reached.
    """
    # Real adapter + langgraph + MCP SDK required: skip (not error) when absent
    # so explicitly selecting the marker on a base install is a clean skip.
    pytest.importorskip("langchain_mcp_adapters")
    pytest.importorskip("langgraph")
    pytest.importorskip("mcp")

    from langchain_core.language_models.chat_models import (  # pylint: disable=import-error
        BaseChatModel,
    )
    from langchain_core.messages import (  # pylint: disable=import-error
        AIMessage,
        HumanMessage,
        ToolMessage,
    )
    from langchain_core.outputs import (  # pylint: disable=import-error
        ChatGeneration,
        ChatResult,
    )
    from langchain_mcp_adapters.tools import (  # pylint: disable=import-error
        convert_mcp_tool_to_langchain_tool,
    )
    from langgraph.prebuilt import create_react_agent  # pylint: disable=import-error
    from mcp.types import Tool as MCPTool  # pylint: disable=import-error

    from mcp_coder.icoder.permissions import (
        Matcher,
        PermissionConfig,
        Policy,
        Rule,
    )
    from mcp_coder.icoder.permissions.gateway import (
        _DENY_NEVER,
        LangchainEnforcementGateway,
    )

    class _ScriptedModel(BaseChatModel):  # type: ignore[misc]
        """Deterministic 2-step model: tool_call first, then plain text.

        ``bind_tools`` must be overridden (``BaseChatModel.bind_tools`` raises
        and ``create_react_agent`` calls it). Only the ASYNC ``_agenerate`` is
        implemented: the agent path is async and the default ``_agenerate``
        would hand ``_generate`` to a thread pool. ``invoke_count`` doubles as
        the script index.
        """

        invoke_count: int = 0

        def bind_tools(self, tools: Any, **kw: Any) -> "_ScriptedModel":
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kw):  # type: ignore[no-untyped-def]
            raise NotImplementedError("scripted model implements _agenerate")

        async def _agenerate(self, messages, stop=None, run_manager=None, **kw):  # type: ignore[no-untyped-def]
            self.invoke_count += 1
            if self.invoke_count == 1:
                message = AIMessage(
                    content="",
                    tool_calls=[{"name": "do_it", "args": {}, "id": "call_1"}],
                )
            else:
                message = AIMessage(content="done")
            return ChatResult(generations=[ChatGeneration(message=message)])

        @property
        def _llm_type(self) -> str:
            return "scripted"

    # Empty-object schema so ``args={}`` passes ToolNode's schema validation,
    # which runs BEFORE the tool coroutine and therefore before the interceptor.
    fake_tool = MCPTool.model_validate(
        {
            "name": "do_it",
            "description": "",
            "inputSchema": {"type": "object", "properties": {}},
        }
    )
    gateway = LangchainEnforcementGateway(
        PermissionConfig(
            rules=(
                Rule(
                    matcher=Matcher(server="srv", tool="do_it"),
                    policy=Policy.NEVER,
                    layer="user",
                ),
            )
        )
    )
    captured: dict[str, Any] = {}

    async def _capturing_interceptor(request: Any, handler: Any) -> Any:
        captured["request"] = request
        return await gateway.interceptor(request, handler)

    tool = convert_mcp_tool_to_langchain_tool(
        None,  # no session needed: the deny never calls the handler
        fake_tool,
        connection={"transport": "stdio"},
        server_name="srv",
        tool_interceptors=[_capturing_interceptor],
    )

    model = _ScriptedModel()
    agent = create_react_agent(model, [tool])

    result = await agent.ainvoke({"messages": [HumanMessage("go")]})

    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_msgs) == 1
    assert tool_msgs[0].content == _DENY_NEVER  # the GATEWAY denied it, not ToolNode
    assert captured["request"].name == "do_it"  # the interceptor really ran
    assert tool_msgs[0].status == "error"
    assert tool_msgs[0].tool_call_id == "call_1"  # THE fix, at graph-state level
    assert model.invoke_count == 2  # agent continued past the deny
    assert result["messages"][-1].content == "done"
