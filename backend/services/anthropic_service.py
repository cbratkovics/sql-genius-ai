"""Small, explicit wrapper around the optional Anthropic integration."""

from dataclasses import dataclass
from typing import Optional

from anthropic import AsyncAnthropic

from backend.core.config import settings


class ProviderNotConfiguredError(RuntimeError):
    """Raised when live generation was requested without credentials."""


class ProviderResponseError(RuntimeError):
    """Raised when the provider response has no usable text."""


@dataclass(frozen=True)
class CompletionResult:
    text: str
    provider: str
    model: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]


class AnthropicService:
    """Interact with Anthropic without silently substituting fixture SQL."""

    def __init__(self, client=None):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.client = client or (
            AsyncAnthropic(api_key=self.api_key, timeout=settings.ANTHROPIC_TIMEOUT_SECONDS)
            if self.api_key
            else None
        )

    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.2,
        model: Optional[str] = None,
    ) -> CompletionResult:
        if not self.client:
            raise ProviderNotConfiguredError(
                "Live generation is not configured. Set ANTHROPIC_API_KEY on the backend, "
                "or choose a curated example in the playground."
            )

        requested_model = model or settings.ANTHROPIC_MODEL
        response = await self.client.messages.create(
            model=requested_model,
            max_tokens=min(max_tokens, settings.ANTHROPIC_MAX_OUTPUT_TOKENS),
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        text_blocks = [
            block.text for block in response.content
            if getattr(block, "type", None) == "text" and getattr(block, "text", "").strip()
        ]
        if not text_blocks:
            raise ProviderResponseError("The provider returned no usable text.")

        usage = getattr(response, "usage", None)
        return CompletionResult(
            text="\n".join(text_blocks),
            provider="anthropic",
            model=getattr(response, "model", requested_model),
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
        )
