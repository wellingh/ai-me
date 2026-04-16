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

    def to_pydantic_ai_model(self) -> Any:
        """Build the model argument for pydantic-ai Agent.

        For Ollama, constructs an OpenAIChatModel with an explicit OllamaProvider
        so that the base_url from config is passed through.
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

        return f"{self.provider}:{self.model_name}"

    @classmethod
    def from_string(cls, model_string: str, ollama_base_url: str | None = None) -> ModelConfig:
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
        )
