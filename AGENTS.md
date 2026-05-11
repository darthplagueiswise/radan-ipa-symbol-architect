# AGENTS.md — Radan IPA Symbol Architect

This repository is used by both Claude Code and Codex/GPT agents.

The project is not only a Claude Code skill. Treat it as a portable analysis toolkit for iOS IPA, Mach-O, Objective-C, Swift metadata, symbols, selectors, selrefs, VM/file offsets, first bytes, callsite triage, hook planning, and offline patch validation.

## Agent priority

When working in this repository, prefer this order:

1. Preserve verifiable binary evidence.
2. Do not invent names for unresolved symbols, MobileConfig IDs, EasyGating tokens, pointers, hashes, or decoded values.
3. Produce deterministic scripts and reports.
4. Keep Claude Code compatibility under `commands/` and `skills/`.
5. Keep Codex/GPT compatibility through this `AGENTS.md`, `README.md`, and shell/Python scripts that can run without Claude-specific runtime variables.
6. Do not turn this back into a broad endpoint/security scanner unless explicitly requested.

## Primary workflow for Codex/GPT agents

Use the script directly:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh <target.ipa|target.app|Mach-O|dylib|framework> -o ./radan-out
```

With explicit patterns:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh <target> \
  -o ./radan-out \
  --pattern _IGMobileConfigBooleanValueForInternalUse \
  --pattern _MCIMobileConfigGetBoolean \
  --pattern openWithConfig:onViewController:userSession:
```

For main binary only:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh <target> -o ./radan-out --no-frameworks
```

For a focused framework:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh Payload/Instagram.app/Frameworks/FBSharedFramework.framework -o ./radan-fbshared
```

## Primary workflow for Claude Code agents

Claude Code may use:

```text
/analyze-ipa-symbols <target> [patterns...]
```

The slash command lives at:

```text
commands/analyze-ipa-symbols.md
```

The Claude skill metadata lives at:

```text
skills/ios-reverse-engineering/SKILL.md
```

Do not remove these files unless replacing them with compatible equivalents.

## Output contract

A good run must produce:

```text
00_inventory.md
binaries.txt
targets.txt
main/01_macho_segments.json
main/02_symbols_exports_imports.json
main/03_objc_sections.json
main/04_swift_demangled_symbols.txt
main/05_selectors_selrefs.json
main/06_strings_by_section.json
main/07_target_matches.md
main/raw/file.txt
main/raw/nm.txt
main/raw/otool_headers.txt
main/raw/otool_load_commands.txt
main/raw/strings.txt
frameworks/<n-name>/...
```

If a file cannot be produced, state why. Missing tool output is acceptable; fake output is not.

## Evidence rules

For every relevant match, preserve:

```text
binary_path
binary_role
architecture
symbol_or_selector_or_string
segment
section
vmaddr
fileoff
first_8_bytes
first_16_bytes
source_tool
confidence
notes
```

If a patch is proposed, include:

```text
symbol_or_selector
binary
vmaddr
fileoff
old_first_8_bytes
old_first_16_bytes
new_bytes
risk
reason
runtime_validation_needed
```

Never suggest a patch based only on a string hit.

## RyukGram / Instagram specific rules

When the target involves RyukGram, Instagram, MobileConfig, EasyGating, Dogfooding, Direct Notes, QuickSnap, Homecoming, Prism, LiquidGlass, TabBar, or MetaLocalExperiment:

- Prefer pass-through observation first.
- Treat `DoNotUseOrMock` symbols as high risk.
- Treat `tryUpdateConfigs`, force-update, and set-overrides paths as high risk during startup.
- Avoid default-on heavy observers.
- Avoid broad blanket override hooks.
- Prefer per-value override namespaces.
- Keep one active owner for central C MobileConfig/EasyGating broker hooks.
- Do not duplicate menus or runtime observers.
- Separate static evidence from runtime evidence.
- Mark unresolved IDs/tokens as unresolved instead of guessing.

## Default target families

The default target profile is stored at:

```text
skills/ios-reverse-engineering/references/ryukgram-instagram-target-profile.md
```

The shell runner also embeds a short default target list so it can run without reading that reference file.

## Tooling expectations

Baseline tools:

```bash
python3
unzip
file
strings
nm
otool
```

Recommended tools:

```bash
ipsw
swift-demangle
radare2
rizin
r2frida
Ghidra headless
lief
ktool
```

The pure Python analyzer must remain usable without LIEF/ktool. LIEF/ktool integrations may be added later, but they should enhance output, not become mandatory for baseline operation.

## Code style

- Scripts should use clear failure messages.
- Bash scripts should use `set -euo pipefail` unless there is a specific reason not to.
- Python scripts should avoid network access by default.
- Do not commit generated IPA dumps or large binary analysis outputs.
- Keep outputs deterministic and easy to diff.

## Commit discipline

For repo edits, prefer small commits with explicit messages:

```text
Add Codex agent instructions
Improve Mach-O selector extraction
Add runtime validation template
Fix IPA framework inventory
```

Do not rewrite large inherited upstream scripts unless the change is needed for the Radan symbol/callsite workflow.
