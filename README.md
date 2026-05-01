# ai-me

`ai-me` is a multi-agent Command Line Interface (CLI) designed to streamline your software development workflow. By bundling specialized AI tools and skills, it automates repetitive daily tasks—like writing commit messages, opening pull requests, and creating Jira tickets.

Let the AI do the heavy lifting, so you only have to review, tweak, and ship.

## Why ai-me?

- **Frictionless Experience**: While you can achieve similar results with other AI coding tools (like the Claude CLI), ai-me provides a faster, more direct interface. There is no need to initialize a session first—just call it directly from your terminal and get to work.

- **Opinionated yet Extensible**: ai-me is built with sensible, opinionated defaults to handle internal tasks efficiently right out of the box. However, if you need custom workflows, it can be easily extended via custom skills.

- **Model Agnostic**: Work with the AI models you prefer. ai-me supports remote models (like Anthropic, OpenAI, or Gemini) as well as secure, self-hosted local models via Ollama.

## Core Features

### ai commit

Automatically generate clean, accurate commit messages following the Conventional Commits standard.

```bash
ai commit -a
```

**How it works**: This acts similarly to `git commit -am "message"`, but instead of typing a message yourself, ai-me analyzes your git diffs and intelligently generates a context-aware commit message based on your actual code changes.

| Option | Description |
|--------|-------------|
| `-a`, `--all` | Stage all changes before committing |
| `--model` | Override the LLM model for this command |

### ai pr

Instantly draft comprehensive pull requests.

```bash
ai pr
```

**How it works**: ai-me analyzes your recent branch changes to generate a detailed PR title and description. If a pull request already exists for your branch, it will smartly update the existing title and description instead of creating a duplicate.

| Option | Description |
|--------|-------------|
| `--base` | Base branch for the PR (defaults to the repo's default branch) |
| `--draft` | Create the PR as a draft |
| `--model` | Override the LLM model for this command |

## Human in the Loop

You are always in control. After ai-me generates content, you are presented with an interactive review loop:

| Action | Description |
|--------|-------------|
| **Submit** | Accept the generated content as-is and proceed |
| **Edit** | Open the content in your `$EDITOR` for manual changes |
| **Refine** | Provide feedback to the AI to improve the output (e.g. "make the title shorter") |
| **Cancel** | Abort the operation |

## Configuration

ai-me uses a TOML configuration file located at `~/.ai-me/config.toml`. Settings can be overridden per-command via CLI flags or environment variables.

### Resolution priority

When determining which model to use, ai-me checks in this order (first match wins):

1. `--model` CLI flag
2. Per-command `model` in config file (e.g. `[commit].model`)
3. Global `[model].default` in config file
4. `AI_ME_MODEL` environment variable
5. Built-in default (`anthropic:claude-sonnet-4-20250514`)

### Config file reference

```toml
# ~/.ai-me/config.toml

# Global model default — used when no per-command override is set.
# Format: "provider:model_name"
# Providers: anthropic, openai, gemini, ollama
[model]
default = "ollama:gemma4:latest"

# Ollama-specific settings.
# Only relevant when using an ollama model.
[ollama]
base_url = "http://localhost:11434"    # Ollama server URL (default shown)

# Anthropic-specific settings.
# Only relevant when using an anthropic model.
# Use these to point at an Anthropic-compatible proxy (e.g. LiteLLM).
# If unset, the standard ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN /
# ANTHROPIC_API_KEY environment variables are honored.
[anthropic]
# base_url   = "http://localhost:36253"
# auth_token = "cloudflare"

# Per-command model overrides.
# If set, these take priority over [model].default for the specific command.

[commit]
model = "ollama:gemma4:latest"         # Model used by `ai commit`

[pr]
model = "ollama:gemma4:latest"         # Model used by `ai pr`
```

### Sections

#### `[model]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `default` | string | `anthropic:claude-sonnet-4-20250514` | The fallback model for all commands when no per-command override is set |

#### `[ollama]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `base_url` | string | `http://localhost:11434` | The URL of your Ollama server. Only used when the selected model's provider is `ollama` |

#### `[anthropic]`

Only used when the selected model's provider is `anthropic`. Useful for routing through an Anthropic-compatible proxy such as LiteLLM. When a value is unset in the config file, the corresponding environment variable is used as a fallback.

| Key | Type | Default | Env fallback | Description |
|-----|------|---------|--------------|-------------|
| `base_url` | string | *none* | `ANTHROPIC_BASE_URL` | Override the Anthropic API base URL (e.g. a local LiteLLM proxy) |
| `auth_token` | string | *none* | `ANTHROPIC_AUTH_TOKEN` | Bearer token sent in the `Authorization` header (matches the Claude Code convention) |

#### `[commit]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `model` | string | *none* | Model override for `ai commit`. When set, takes priority over `[model].default` |

#### `[pr]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `model` | string | *none* | Model override for `ai pr`. When set, takes priority over `[model].default` |

### API keys

API keys are read from standard environment variables — they are never stored in the config file.

| Provider | Environment Variable |
|----------|---------------------|
| Anthropic | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Gemini | `GEMINI_API_KEY` |
| Ollama | *none required* (runs locally) |

### Model string format

Models are specified as `provider:model_name`:

```
anthropic:claude-sonnet-4-20250514
openai:gpt-4o
gemini:gemini-2.5-flash
ollama:gemma4:latest
```

## Installation

```bash
pip install ai-me
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install ai-me
```
