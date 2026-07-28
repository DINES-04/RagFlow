import httpx
import json
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
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set in environment settings")

        system_instruction_parts = []
        contents = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role == "system":
                system_instruction_parts.append({"text": content})
            else:
                gemini_role = "model" if role == "assistant" else "user"
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })

        payload = {
            "contents": contents
        }
        if system_instruction_parts:
            payload["systemInstruction"] = {"parts": system_instruction_parts}

        model = "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={api_key}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise RuntimeError(f"Gemini API error ({response.status_code}): {error_text.decode()}")

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    while True:
                        buffer = buffer.lstrip().lstrip("[").lstrip(",").lstrip()
                        if not buffer:
                            break
                        brace_count = 0
                        in_string = False
                        escape = False
                        end_index = -1
                        for idx, char in enumerate(buffer):
                            if char == '"' and not escape:
                                in_string = not in_string
                            elif char == '\\' and in_string:
                                escape = not escape
                                continue
                            elif not in_string:
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end_index = idx + 1
                                        break
                            escape = False

                        if end_index != -1:
                            obj_str = buffer[:end_index]
                            buffer = buffer[end_index:]
                            try:
                                obj = json.loads(obj_str)
                                text = obj["candidates"][0]["content"]["parts"][0]["text"]
                                if text:
                                    yield text
                            except (json.JSONDecodeError, KeyError, IndexError):
                                pass
                        else:
                            break

    async def embed(self, texts: list[str]) -> list[list[float]]:
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set in environment settings")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={api_key}"
        requests = [
            {
                "model": "models/gemini-embedding-001",
                "content": {"parts": [{"text": t}]},
                "outputDimensionality": settings.EMBEDDING_DIM
            }
            for t in texts
        ]
        payload = {"requests": requests}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Gemini embedding API error ({response.status_code}): {response.text}")
            
            data = response.json()
            embeddings = [emb["values"] for emb in data.get("embeddings", [])]
            if len(embeddings) != len(texts):
                raise RuntimeError(f"Expected {len(texts)} embeddings, got {len(embeddings)}")
            return embeddings


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
