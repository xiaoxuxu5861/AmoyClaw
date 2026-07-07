from __future__ import annotations

from typing import Any

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


class ModelUnavailableError(RuntimeError):
    pass


class OpenAICompatibleClient:
    """Thin optional wrapper kept for the real Function Calling version."""

    def __init__(
        self,
        api_key: str = OPENAI_API_KEY,
        base_url: str = OPENAI_BASE_URL,
        model: str = OPENAI_MODEL,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        if not self.api_key:
            raise ModelUnavailableError("未配置 OPENAI_API_KEY，当前使用离线 demo controller")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - optional path
            raise ModelUnavailableError("未安装 openai 包") from exc
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return client.chat.completions.create(model=self.model, messages=messages, tools=tools)
