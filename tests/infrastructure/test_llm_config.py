"""Tests for LLM ModelConfig."""

import pytest

from ai_me.infrastructure.llm.config import ModelConfig


class TestModelConfig:
    def test_from_string_anthropic(self):
        config = ModelConfig.from_string("anthropic:claude-sonnet-4-20250514")
        assert config.provider == "anthropic"
        assert config.model_name == "claude-sonnet-4-20250514"
        assert config.ollama_base_url is None

    def test_from_string_openai(self):
        config = ModelConfig.from_string("openai:gpt-4o")
        assert config.provider == "openai"
        assert config.model_name == "gpt-4o"

    def test_from_string_ollama(self):
        config = ModelConfig.from_string("ollama:llama3", ollama_base_url="http://localhost:11434")
        assert config.provider == "ollama"
        assert config.model_name == "llama3"
        assert config.ollama_base_url == "http://localhost:11434"

    def test_from_string_ollama_ignores_url_for_other_providers(self):
        config = ModelConfig.from_string("openai:gpt-4o", ollama_base_url="http://localhost:11434")
        assert config.ollama_base_url is None

    def test_from_string_invalid(self):
        with pytest.raises(ValueError, match="Invalid model string"):
            ModelConfig.from_string("invalid-no-colon")

    def test_to_pydantic_ai_model_returns_string_for_anthropic(self):
        config = ModelConfig(provider="anthropic", model_name="claude-sonnet-4-20250514")
        assert config.to_pydantic_ai_model() == "anthropic:claude-sonnet-4-20250514"

    def test_to_pydantic_ai_model_returns_string_for_openai(self):
        config = ModelConfig(provider="openai", model_name="gpt-4o")
        assert config.to_pydantic_ai_model() == "openai:gpt-4o"

    def test_to_pydantic_ai_model_returns_model_object_for_ollama(self):
        config = ModelConfig(
            provider="ollama",
            model_name="llama3",
            ollama_base_url="http://localhost:11434",
        )
        model = config.to_pydantic_ai_model()
        assert not isinstance(model, str)
        assert model.model_name == "llama3"

    def test_to_pydantic_ai_model_returns_model_object_for_anthropic_with_base_url(self):
        config = ModelConfig(
            provider="anthropic",
            model_name="claude-sonnet-4-20250514",
            anthropic_base_url="http://localhost:36253",
            anthropic_auth_token="cloudflare",
        )
        model = config.to_pydantic_ai_model()
        assert not isinstance(model, str)
        assert model.model_name == "claude-sonnet-4-20250514"

    def test_from_string_anthropic_with_base_url_and_token(self):
        config = ModelConfig.from_string(
            "anthropic:claude-sonnet-4-20250514",
            anthropic_base_url="http://localhost:36253",
            anthropic_auth_token="cloudflare",
        )
        assert config.anthropic_base_url == "http://localhost:36253"
        assert config.anthropic_auth_token == "cloudflare"

    def test_from_string_anthropic_overrides_ignored_for_other_providers(self):
        config = ModelConfig.from_string(
            "openai:gpt-4o",
            anthropic_base_url="http://localhost:36253",
            anthropic_auth_token="cloudflare",
        )
        assert config.anthropic_base_url is None
        assert config.anthropic_auth_token is None


class TestModelConfigImmutable:
    def test_frozen(self):
        config = ModelConfig(provider="openai", model_name="gpt-4o")
        with pytest.raises(Exception):
            config.provider = "anthropic"
