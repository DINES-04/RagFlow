"""
LLM Gateway: single interface over multiple providers so the rest of the app
never imports openai/anthropic/google SDKs directly. This is what makes model
switching and routing (see docs/ARCHITECTURE.md §7) a config change.
"""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.core.config import get_settings

settings = get_settings()


class Message(dict):
    """Simple {role, content} message. Kept as dict for easy LangChain interop."""


class LLMProvider(ABC):
    @abstractmethod
    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class OpenAIProvider(LLMProvider):
    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        # TODO: wire up `openai` async client / langchain_openai ChatOpenAI streaming
        raise NotImplementedError("Wire up OpenAI streaming here")
        yield ""  # pragma: no cover

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # TODO: wire up OpenAI embeddings endpoint
        raise NotImplementedError("Wire up OpenAI embeddings here")


class ClaudeProvider(LLMProvider):
    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        # TODO: wire up anthropic async client streaming
        raise NotImplementedError("Wire up Claude streaming here")
        yield ""  # pragma: no cover

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Claude has no embeddings endpoint; route to another provider")


class GeminiProvider(LLMProvider):
    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        raise NotImplementedError("Wire up Gemini streaming here")
        yield ""  # pragma: no cover

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Wire up Gemini embeddings here")


class OllamaProvider(LLMProvider):
    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        # TODO: call local Ollama server (http://ollama:11434/api/chat)
        raise NotImplementedError("Wire up Ollama streaming here")
        yield ""  # pragma: no cover

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Wire up Ollama embeddings here")


_PROVIDERS: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
}


def get_provider(name: str | None = None) -> LLMProvider:
    name = name or settings.DEFAULT_LLM_PROVIDER
    if name not in _PROVIDERS:
        raise ValueError(f"Unknown LLM provider '{name}'. Available: {list(_PROVIDERS)}")
    return _PROVIDERS[name]()


def route_model(estimated_complexity: str = "low", workspace_settings: dict | None = None) -> str:
    """
    Config-driven routing stub (docs/ARCHITECTURE.md §7).
    Replace with a rules engine reading workspace/org config once Phase 2 lands.
    """
    workspace_settings = workspace_settings or {}
    if workspace_settings.get("local_only"):
        return "ollama"
    if estimated_complexity == "high":
        return "claude"
    return settings.DEFAULT_LLM_PROVIDER
