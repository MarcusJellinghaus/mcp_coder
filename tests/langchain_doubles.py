from __future__ import annotations

from collections.abc import Callable
from typing import Any, Self


def make_scripted_chat_model(next_message: Callable[[int], Any], llm_type: str) -> Any:
    """Build a BaseChatModel test double driven by *next_message*.

    *next_message* receives the 1-based invoke count and returns the
    AIMessage for that invoke. Callers decide via its logic when (or
    whether) to stop returning tool calls.

    The caller must already have confirmed langchain_core is importable
    (e.g. via `pytest.importorskip`) before calling this.
    """
    from langchain_core.callbacks import (
        AsyncCallbackManagerForLLMRun,
        CallbackManagerForLLMRun,
    )
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import BaseMessage
    from langchain_core.outputs import ChatGeneration, ChatResult

    class _ScriptedChatModel(BaseChatModel):  # type: ignore[misc]
        invoke_count: int = 0

        def bind_tools(self, tools: Any, **kw: Any) -> Self:
            return self

        def _generate(
            self,
            messages: list[BaseMessage],
            stop: list[str] | None = None,
            run_manager: CallbackManagerForLLMRun | None = None,
            **kwargs: Any,
        ) -> ChatResult:
            raise NotImplementedError("scripted model implements _agenerate")

        async def _agenerate(
            self,
            messages: list[BaseMessage],
            stop: list[str] | None = None,
            run_manager: AsyncCallbackManagerForLLMRun | None = None,
            **kwargs: Any,
        ) -> ChatResult:
            self.invoke_count += 1
            message = next_message(self.invoke_count)
            return ChatResult(generations=[ChatGeneration(message=message)])

        @property
        def _llm_type(self) -> str:
            return llm_type

    return _ScriptedChatModel()
