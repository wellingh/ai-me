"""Application settings using pydantic-settings with TOML config file support."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource

from ai_me.infrastructure.llm.config import ModelConfig

DEFAULT_MODEL = "anthropic:claude-sonnet-4-20250514"
CONFIG_DIR = Path.home() / ".ai-me"
CONFIG_FILE = CONFIG_DIR / "config.toml"


class ModelSettings(BaseModel):
    """Global model defaults from [model] section."""

    default: str = DEFAULT_MODEL


class OllamaSettings(BaseModel):
    """Ollama-specific settings from [ollama] section."""

    base_url: str = "http://localhost:11434"


class AnthropicSettings(BaseModel):
    """Anthropic-specific settings from [anthropic] section.

    When set, these override the Anthropic SDK defaults — useful for pointing
    at an Anthropic-compatible proxy like LiteLLM. If left unset, the standard
    ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY env vars apply.
    """

    base_url: str | None = None
    auth_token: str | None = None


class CommandSettings(BaseModel):
    """Per-command settings (used for [commit] and [pr] sections)."""

    model: str | None = None


class AiMeSettings(BaseSettings):
    """Root settings loaded from ~/.ai-me/config.toml and environment variables."""

    model_config = SettingsConfigDict(
        toml_file=str(CONFIG_FILE),
        env_prefix="AI_ME_",
    )

    model: ModelSettings = ModelSettings()
    ollama: OllamaSettings = OllamaSettings()
    anthropic: AnthropicSettings = AnthropicSettings()
    commit: CommandSettings = CommandSettings()
    pr: CommandSettings = CommandSettings()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: object,
        env_settings: object,
        dotenv_settings: object,
        file_secret_settings: object,
    ) -> tuple:
        sources = [init_settings, env_settings]
        if CONFIG_FILE.exists():
            sources.append(TomlConfigSettingsSource(settings_cls))
        return tuple(sources)


def _get_settings() -> AiMeSettings:
    """Load settings, tolerating missing config file."""
    return AiMeSettings()


def resolve_model_config(
    command_name: str,
    cli_override: str | None = None,
) -> ModelConfig:
    """Resolve the model to use, applying the priority chain.

    Priority (highest wins):
        1. CLI --model flag
        2. Per-command model from [commit].model or [pr].model in config
        3. Default model from [model].default in config
        4. AI_ME_MODEL environment variable
        5. Hardcoded default
    """
    settings = _get_settings()

    if cli_override:
        model_string = cli_override
    else:
        command_settings = getattr(settings, command_name, None)
        command_model = command_settings.model if command_settings else None

        if command_model:
            model_string = command_model
        elif settings.model.default != DEFAULT_MODEL:
            model_string = settings.model.default
        else:
            model_string = os.environ.get("AI_ME_MODEL", DEFAULT_MODEL)

    ollama_base_url = (
        settings.ollama.base_url
        if model_string.startswith("ollama:")
        else None
    )

    anthropic_base_url: str | None = None
    anthropic_auth_token: str | None = None
    if model_string.startswith("anthropic:"):
        anthropic_base_url = settings.anthropic.base_url or os.environ.get("ANTHROPIC_BASE_URL")
        anthropic_auth_token = settings.anthropic.auth_token or os.environ.get("ANTHROPIC_AUTH_TOKEN")

    return ModelConfig.from_string(
        model_string,
        ollama_base_url=ollama_base_url,
        anthropic_base_url=anthropic_base_url,
        anthropic_auth_token=anthropic_auth_token,
    )
