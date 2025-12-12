
"""
LLM client wrapper for OpenRouter (Qwen, etc.).

Other modules should use LLMClient instead of calling openai / OpenRouter
directly, so we keep config + error handling in one place.
"""

from typing import List, Dict
from openai import OpenAI

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """
    Lazily-initialized OpenAI client configured to talk to OpenRouter.
    """
    global _client
    if _client is None:
        if not OPENROUTER_API_KEY:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. "
                "Export it in your environment before running the app."
            )
        _client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=OPENROUTER_API_KEY,
        )
    return _client


class LLMClient:
    """
    Simple chat-completion wrapper.

    Example:
        llm = LLMClient(model_name="qwen2.5-vl-32b-instruct")
        text = llm.chat([
            {"role": "system", "content": "You are a helpful tutor."},
            {"role": "user", "content": "Explain photosynthesis simply."},
        ])
    """

    def __init__(self, model_name: str):
        self.model_name = model_name

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> str:
        client = _get_client()
        resp = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # OpenAI v1-style client; choices[0].message.content is a string
        return resp.choices[0].message.content or ""
