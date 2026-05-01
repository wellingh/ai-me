"""LLM model configuration for pydantic-ai integration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ModelConfig(BaseModel):
    """Resolved model configuration ready for pydantic-ai Agent creation."""

    model_config = ConfigDict(frozen=True)

    provider: str
    model_name: str
    ollama_base_url: str | None = None
    anthropic_base_url: str | None = None
    anthropic_auth_token: str | None = None

    def to_pydantic_ai_model(self) -> Any:
        """Build the model argument for pydantic-ai Agent.

        For Ollama, constructs an OpenAIChatModel with an explicit OllamaProvider
        so that the base_url from config is passed through.
        For Anthropic with a custom base_url or auth_token (e.g. LiteLLM proxy),
        constructs an AnthropicModel with a custom AsyncAnthropic client.
        For other providers, returns the standard 'provider:model' string.
        """
        if self.provider == "ollama":
            from pydantic_ai.models.openai import OpenAIChatModel
            from pydantic_ai.providers.ollama import OllamaProvider

            raw_url = self.ollama_base_url or "http://localhost:11434"
            base_url = raw_url.rstrip("/")
            if not base_url.endswith("/v1"):
                base_url = f"{base_url}/v1"
            return OpenAIChatModel(
                self.model_name,
                provider=OllamaProvider(base_url=base_url),
            )

        if self.provider == "anthropic" and (self.anthropic_base_url or self.anthropic_auth_token):
            from anthropic import AsyncAnthropic
            from pydantic_ai.models.anthropic import AnthropicModel
            from pydantic_ai.providers.anthropic import AnthropicProvider

            client_kwargs: dict[str, Any] = {}
            if self.anthropic_base_url:
                client_kwargs["base_url"] = self.anthropic_base_url
            if self.anthropic_auth_token:
                client_kwargs["auth_token"] = self.anthropic_auth_token

            return AnthropicModel(
                self.model_name,
                provider=AnthropicProvider(anthropic_client=AsyncAnthropic(**client_kwargs)),
            )

        return f"{self.provider}:{self.model_name}"

    @classmethod
    def from_string(
        cls,
        model_string: str,
        ollama_base_url: str | None = None,
        anthropic_base_url: str | None = None,
        anthropic_auth_token: str | None = None,
    ) -> ModelConfig:
        """Parse a 'provider:model_name' string into a ModelConfig."""
        provider, _, model_name = model_string.partition(":")
        if not model_name:
            raise ValueError(
                f"Invalid model string '{model_string}'. "
                "Expected format: 'provider:model_name' (e.g. 'anthropic:claude-sonnet-4-20250514')"
            )
        return cls(
            provider=provider,
            model_name=model_name,
            ollama_base_url=ollama_base_url if provider == "ollama" else None,
            anthropic_base_url=anthropic_base_url if provider == "anthropic" else None,
            anthropic_auth_token=anthropic_auth_token if provider == "anthropic" else None,
        )
