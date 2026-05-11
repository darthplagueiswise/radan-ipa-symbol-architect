# Codex Integration

Radan IPA Symbol Architect supports OpenAI Codex / ChatGPT Codex and Claude Code.

This document explains the Codex-facing layout so future edits do not accidentally make the project Claude-only.

## Confirmed Codex surfaces

### 1. `AGENTS.md`

Codex uses `AGENTS.md` as project-level agent guidance.

In this repository, `AGENTS.md` tells Codex how to work on the repo itself: which scripts matter, what output contract to preserve, and what not to hallucinate when analyzing IPA/Mach-O evidence.

### 2. `.agents/skills/<skill>/SKILL.md`

Codex discovers repo skills from:

```text
.agents/skills/<skill-name>/SKILL.md
```

Radan provides:

```text
.agents/skills/radan-ipa-symbol-architect/SKILL.md
```

That wrapper points Codex to the canonical implementation under:

```text
skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh
skills/ios-reverse-engineering/scripts/macho_symbol_architect.py
```

### 3. `agents/openai.yaml`

Codex skills may include UI/dependency metadata under:

```text
.agents/skills/radan-ipa-symbol-architect/agents/openai.yaml
```

This file gives Codex a display name, short description, default prompt, dependencies and policy.

## Claude Code surfaces

Claude Code compatibility remains under:

```text
commands/analyze-ipa-symbols.md
skills/ios-reverse-engineering/SKILL.md
```

Do not remove those files unless replacing them with compatible equivalents.

## Shared implementation

Both Codex and Claude should use the same implementation:

```text
skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh
skills/ios-reverse-engineering/scripts/macho_symbol_architect.py
```

The Codex wrapper is only a thin dispatcher:

```text
.agents/skills/radan-ipa-symbol-architect/scripts/run-radan.sh
```

## Why not duplicate the full script under `.agents/skills`?

Avoid duplication. The wrapper calls the canonical script so bug fixes land in one place.

## Install patterns

### Use this repo as the project root

Codex will see:

```text
AGENTS.md
.agents/skills/radan-ipa-symbol-architect/SKILL.md
```

Then run:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh /path/to/Instagram.ipa -o ./radan-out
```

### Copy Radan into another Codex project

Copy both trees:

```text
.agents/skills/radan-ipa-symbol-architect/
skills/ios-reverse-engineering/scripts/
```

Keep `AGENTS.md` instructions or merge the relevant parts into the target project’s existing `AGENTS.md`.

## Skill frontmatter rules

Every Codex-compatible `SKILL.md` should keep frontmatter with at least:

```yaml
---
name: radan-ipa-symbol-architect
description: Analyze iOS IPA, .app, Mach-O, dylib, and framework binaries for symbol architecture...
---
```

The description is important because Codex reads it to decide when to activate the skill.

## Validation commands

Run these before committing script changes:

```bash
bash -n skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh
bash -n .agents/skills/radan-ipa-symbol-architect/scripts/run-radan.sh
python3 -m py_compile skills/ios-reverse-engineering/scripts/macho_symbol_architect.py
```

For a real target:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh /path/to/Instagram.ipa -o ./radan-out --max-frameworks 5
```

## Non-goals

Do not repoint this repo toward generic security scanning, cloud credential scanning, or endpoint extraction as the default. Those workflows may exist as inherited scripts, but Radan’s default job is symbol/callsite/patch-validation evidence.
