# Radan IPA Symbol Architect

Radan IPA Symbol Architect is a portable agent skill/toolkit for **iOS IPA / Mach-O / Objective-C / Swift symbol architecture analysis**.

It is meant for both **OpenAI Codex / ChatGPT Codex** and **Claude Code**. This repo is not just a Claude Code skill.

Its job is to help with tweak and binary-analysis workflows where the important output is not “find every API endpoint”, but:

- which binary/framework owns a selector, class, symbol, string, or MobileConfig getter;
- where a symbol lives in VM address and file offset terms;
- what the first bytes/prologue are before a hook or offline patch is considered;
- which selectors have selrefs and likely callsite anchors;
- which Objective-C/Swift metadata can be used as stable anchors;
- which findings are verified versus guessed.

The default target profile is the RyukGram / Instagram iOS workflow, but the skill works with any IPA, `.app`, Mach-O executable, `.dylib`, or `.framework`.

## Agent compatibility

### OpenAI Codex / ChatGPT Codex

Codex support is provided through:

```text
AGENTS.md
.agents/skills/radan-ipa-symbol-architect/SKILL.md
.agents/skills/radan-ipa-symbol-architect/agents/openai.yaml
.agents/skills/radan-ipa-symbol-architect/scripts/run-radan.sh
```

Codex can read `AGENTS.md` as project instructions and discover the skill from `.agents/skills/radan-ipa-symbol-architect/SKILL.md`.

Manual Codex usage from the repository root:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh /path/to/Instagram.ipa -o ./radan-out
```

Manual Codex usage from the skill wrapper directory:

```bash
bash .agents/skills/radan-ipa-symbol-architect/scripts/run-radan.sh /path/to/Instagram.ipa -o ./radan-out
```

### Claude Code

Claude Code compatibility is provided through:

```text
commands/analyze-ipa-symbols.md
skills/ios-reverse-engineering/SKILL.md
```

Claude command usage:

```text
/analyze-ipa-symbols /path/to/Instagram.ipa
```

### Plain shell / CI

No agent runtime is required for the core analyzer:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh /path/to/Instagram.ipa -o ./radan-out
```

## What this skill optimizes for

Use it when you need hard binary facts:

- IPA extraction and app/framework inventory.
- Main executable and embedded framework discovery.
- Mach-O segment / section mapping.
- VM address to file offset mapping.
- Symbol table exports/imports where available.
- First bytes for target symbols.
- Objective-C class, selector, method, selref and string-section extraction.
- Swift symbol demangling when `swift-demangle` exists.
- Targeted reports for selectors and functions such as:
  - `_IGMobileConfigBooleanValueForInternalUse`
  - `_MCIMobileConfigGetBoolean`
  - `_EasyGatingPlatformGetBoolean`
  - `_EasyGatingGetBoolean_Internal_DoNotUseOrMock`
  - `openWithConfig:onViewController:userSession:`
  - `notesDogfoodingSettingsOpenOnViewController:userSession:`
  - `getBool`
  - `getBool:withDefault:`
  - `getBool:withOptions:`
  - `getStableIdFromParamSpecifier:`
  - `_getTranslatedSpecifier:`

## What this skill deliberately de-prioritizes

The original upstream skill was broad and security-audit oriented. This fork keeps useful tooling ideas but does **not** treat these as primary goals:

- cloud credential scanning;
- generic endpoint inventory;
- CVE reporting;
- broad “security score” reports;
- speculative feature naming.

Those workflows can still be run with the inherited scripts if needed, but the default Radan workflow is symbol/callsite/patch-validation oriented.

## Install for Codex

Inside a Codex project, either keep this repository as the project root or copy the skill folder into your project:

```text
<project>/.agents/skills/radan-ipa-symbol-architect/
```

The skill folder must contain at least:

```text
SKILL.md
agents/openai.yaml
scripts/run-radan.sh
```

The runner expects the canonical scripts to exist at repository root under:

```text
skills/ios-reverse-engineering/scripts/
```

For standalone reuse in another repo, copy both:

```text
.agents/skills/radan-ipa-symbol-architect/
skills/ios-reverse-engineering/scripts/
```

## Install for Claude Code

Clone the repository into your Claude Code skills area or add it as a project skill, depending on your local Claude Code setup:

```bash
git clone https://github.com/darthplagueiswise/radan-ipa-symbol-architect.git
```

The canonical skill file is:

```text
skills/ios-reverse-engineering/SKILL.md
```

The skill metadata name is `radan-ipa-symbol-architect`.

## Dependencies

Required for the basic workflow:

```bash
python3
bash
unzip
file
strings
```

Strongly recommended:

```bash
nm
otool
ipsw
swift-demangle
```

Optional but useful:

```bash
pip install lief k2l
r2pm -ci r2frida
radare2
rizin
Ghidra headless
class-dump / classdump-dyld
```

On Linux/WSL2, basic static analysis works for already extracted files. macOS gives better results because `otool`, `nm`, `codesign`, `plutil`, `swift-demangle`, and `ipsw` are easier to use together.

## Main command

Run:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh /path/to/Instagram.ipa -o ./radan-out
```

Add target patterns:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh /path/to/Instagram.ipa \
  -o ./radan-out \
  --pattern _IGMobileConfigBooleanValueForInternalUse \
  --pattern _MCIMobileConfigGetBoolean \
  --pattern openWithConfig:onViewController:userSession:
```

Limit framework scan during heavy IPA analysis:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh /path/to/Instagram.ipa -o ./radan-out --max-frameworks 5
```

Analyze only one framework:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh Payload/Instagram.app/Frameworks/FBSharedFramework.framework -o ./radan-fbshared
```

## Output contract

A valid run should produce a directory with this shape:

```text
radan-out/
├── 00_inventory.md
├── binaries.txt
├── targets.txt
├── main/
│   ├── 01_macho_segments.json
│   ├── 02_symbols_exports_imports.json
│   ├── 03_objc_sections.json
│   ├── 04_swift_demangled_symbols.txt
│   ├── 05_selectors_selrefs.json
│   ├── 06_strings_by_section.json
│   ├── 07_target_matches.md
│   └── raw/
│       ├── file.txt
│       ├── nm.txt
│       ├── otool_headers.txt
│       ├── otool_load_commands.txt
│       ├── strings.txt
│       └── ipsw_class_dump.txt
└── frameworks/
    └── <FrameworkName>/
        └── same report structure...
```

Every symbol-level claim should include as many of these fields as the tooling can verify:

```text
binary
architecture
symbol/selector/string
segment
section
vmaddr
fileoff
first_8_bytes
first_16_bytes
source_tool
confidence
```

## Rules for RyukGram / Instagram work

When the target is Instagram, RyukGram, MobileConfig, Dogfooding, Direct Notes, QuickSnap, Homecoming, Prism, or LiquidGlass:

1. Prefer evidence over guesses.
2. Never invent a feature name from a hash/token.
3. Treat `DoNotUseOrMock` and broad MobileConfig/EasyGating overrides as risky.
4. Prefer pass-through observation and per-value overrides.
5. Always separate:
   - static binary evidence;
   - runtime observation;
   - manual labels;
   - inferred labels;
   - unverified hypotheses.
6. For patch candidates, always report first bytes and file offset before suggesting a stub.
7. For hooks, always report the class/selector/symbol owner and whether it is ObjC, Swift, C, or unknown.

## Recommended tool stack

- `blacktop/ipsw` for class-dump, Mach-O search/disassembly and iOS research automation.
- `LIEF` for repeatable Mach-O parsing, symbol/section metadata and future patch tooling.
- `ktool` for portable Python Mach-O/ObjC metadata extraction.
- `r2frida` for runtime validation on device.
- Ghidra headless for deeper cross-reference and decompiler output when the static CLI result is not enough.

## Current state

This fork has been repointed from a broad iOS security skill into a symbol-architecture skill. The inherited broad scripts remain in place for compatibility, but the intended workflow is now:

```text
OpenAI Codex: .agents/skills/radan-ipa-symbol-architect/SKILL.md
Claude Code: commands/analyze-ipa-symbols.md + skills/ios-reverse-engineering/SKILL.md
CLI/CI: skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh
```

## License

Same license as the upstream fork unless changed explicitly.
