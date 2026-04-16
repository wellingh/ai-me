---
name: create-pull-request
description: >
  Generate pull request descriptions that serve as meaningful historical records.
  Use this skill whenever the user asks to write, generate, draft, or create a PR
  description, pull request body, or commit message summary. Also trigger when the
  user says things like "write a PR for this", "describe these changes", "generate
  a PR description from this diff", or "help me write up this pull request". Covers
  all languages and change types (features, fixes, refactors, docs, chores, CI).
  Always use this skill when a PR description or changelog narrative is the goal —
  even if the user only provides a diff, branch name, or a vague description of
  what changed.
---

# PR Description Generator

You generate pull request descriptions that serve as meaningful historical records,
following the principles outlined by Linus Torvalds for Linux kernel pull requests.

---

## Step 1 — Gather the input

Determine what the user has provided:

- **A diff or patch**: use it directly.
- **A branch name or base ref**: run `git diff <base>...HEAD` to get the diff, then
  `git log <base>...HEAD --oneline` for the commit history.
- **A vague description only**: ask for the diff or a list of changed files before
  proceeding. A good PR description must be grounded in actual code changes.

If you have the diff, also run `git log --oneline` (or ask the user to paste it) so
you can use the commit history to tell the story.

---

## Step 2 — Write the title (Conventional Commits)

The **first line** of your output must be a Conventional Commits title:

```
<type>(<scope>): <description>
```

### Types

| Type | Use when |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `refactor` | Neither a fix nor a feature |
| `perf` | Performance improvement |
| `test` | Adding or correcting tests |
| `chore` | Build process, tooling |
| `ci` | CI configuration |
| `build` | Build system or external deps |

### Title rules
- Imperative mood: "add" not "added", "fix" not "fixed"
- Under 72 characters
- Scope is optional but recommended (e.g. `feat(auth):`, `fix(api):`)
- No trailing period

---

## Step 3 — Write the body

Leave a blank line after the title, then write the body using the principles below.

### 3a. Explain WHAT and WHY

The reader must understand what this set of changes does and why it matters. This is
not a changelog — it is a narrative that justifies the merge. The description must
make sense not just at review time, but as a historical record months or years later.

### 3b. Derive the WHY from the code itself

- Analyze the actual diff: look at comments, docstrings, variable names, and function
  signatures to understand the intent behind the changes.
- If the code adds comments explaining a decision, surface that reasoning in the PR
  description.
- Do not mechanically describe what changed — explain the motivation and reasoning
  that the code reveals.

### 3c. Call out anything unusual

- If the changes touch files outside the normal scope, explain WHY.
- If there are risky changes or edge cases, name them explicitly.
- If the timing is unusual (late changes, post-freeze fixes), explain what happened
  and why it could not wait.

### 3d. For refactoring changes, cite the applicable SOLID principle(s)

When the change is a refactoring, explain the motivation using the relevant principle:

| Principle | When it applies |
|---|---|
| **Single Responsibility** | A class/module had too many responsibilities and was split |
| **Open/Closed** | Code was restructured to be extensible without modification |
| **Liskov Substitution** | Subtype contracts were being violated and were corrected |
| **Interface Segregation** | A fat interface was broken into focused ones |
| **Dependency Inversion** | Concrete dependencies were replaced with abstractions |

Only reference the principles that actually apply. Do not force-fit irrelevant ones.

### 3e. Use the commit history

The commit log shows the evolution of the work. Use it to:
- Understand the sequence of decisions.
- Group related commits into coherent themes or sections.
- Reference significant individual commits when they add important context.

---

## Step 4 — Structure the body

Use clear sections as needed:

1. **High-level summary** — one paragraph explaining what this PR does and why it matters, written for someone who has never seen the code.
2. **Notable changes** — bullet list or indented list of new components, key modifications, or non-obvious decisions.
3. **Reasoning** — explain non-obvious design choices, trade-offs, or constraints.
4. **Testing / validation** — if tests are visible in the diff, note what was added or changed and what it covers.

Only include sections that have meaningful content. Do not pad with boilerplate.

## Step 5 - Create or Update the Pull Request

Preview the pull request title and description and ask for the user review. Upon confirmation, create a pull request pointing to the default branch.

In case a pull request for the specific branch already exists, ask if the user wants to update its title and description.

---

## Output format

```
<type>(<scope>): <description under 72 chars>

<high-level summary paragraph>

### Notable changes
- <change 1 with brief rationale>
- <change 2 with brief rationale>

### Reasoning
<non-obvious decisions, trade-offs, SOLID principles if applicable>

### Testing
<what tests were added/changed and what they cover>
```

Omit any section that has nothing meaningful to say.
