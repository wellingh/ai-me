# 🤖 ai-me

`ai-me` is a multi-agent Command Line Interface (CLI) designed to streamline your software development workflow. By bundling specialized AI tools and skills, it automates repetitive daily tasks—like writing commit messages, opening pull requests, and creating Jira tickets.

Let the AI do the heavy lifting, so you only have to review, tweak, and ship.

## ✨ Why ai-me?

- Frictionless Experience: While you can achieve similar results with other AI coding tools (like the Claude CLI), ai-me provides a faster, more direct interface. There is no need to initialize a session first—just call it directly from your terminal and get to work.

- Opinionated yet Extensible: ai-me is built with sensible, opinionated defaults to handle internal tasks efficiently right out of the box. However, if you need custom workflows, it can be easily extended via custom skills.

- Model Agnostic: Work with the AI models you prefer. ai-me supports remote models (like Anthropic or OpenAI) as well as secure, self-hosted local models via Ollama.

## 🚀 Core Features

**ai commit**
Automatically generate clean, accurate commit messages following the Conventional Commits standard.

```bash
ai commit -a
```

**How it works**: This acts similarly to `git commit -am "message"`, but instead of typing a message yourself, ai-me analyzes your git diffs and intelligently generates a context-aware commit message based on your actual code changes.

**ai pr**
Instantly draft comprehensive pull requests.

```bash
ai pr
```

**How it works**: ai-me analyzes your recent branch changes to generate a detailed PR title and description. If a pull request already exists for your branch, it will smartly update the existing title and description instead of creating a duplicate.

## 🛡️ Human in the Loop

You are always in control. ai-me is designed to assist, not replace. For every feature and automated task, you will always have the opportunity to review, edit, or converse with the AI agents to refine the descriptions and messages before finalizing any actions.
