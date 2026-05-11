# Radan IPA Symbol Architect

Radan IPA Symbol Architect is a Claude Code skill for **iOS IPA / Mach-O / Objective-C / Swift symbol architecture analysis**.

This fork is intentionally narrower than the original generic iOS reverse-engineering skill. Its job is to help with tweak and binary-analysis workflows where the important output is not “find every API endpoint”, but:

- which binary/framework owns a selector, class, symbol, string, or MobileConfig getter;
- where a symbol lives in VM address and file offset terms;
- what the first bytes/prologue are before a hook or offline patch is considered;
- which selectors have selrefs and likely callsites;
- which Objective-C/Swift metadata can be used as stable anchors;
- which findings are verified versus guessed.

The default target profile is the RyukGram / Instagram iOS workflow, but the skill works with any IPA, `.app`, Mach-O executable, `.dylib`, or `.framework`.

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

## Install

Clone the repository into your Claude Code skills area or add it as a skill, depending on your local Claude Code setup:

```bash
git clone https://github.com/darthplagueiswise/radan-ipa-symbol-architect.git
```

The main skill file is:

```text
skills/ios-reverse-engineering/SKILL.md
```

The skill metadata name is `radan-ipa-symbol-architect`.

## Dependencies

Required for the basic workflow:

```bash
python3
unzip
file
strings
nm
otool
```

Strongly recommended:

```bash
brew install blacktop/tap/ipsw
pip install lief
r2pm -ci r2frida
```

Optional but useful:

```bash
radare2
rizin
Ghidra headless
swift-demangle
class-dump / classdump-dyld
```

On Linux/WSL2, basic static analysis works for already extracted files. macOS gives better results because `otool`, `nm`, `codesign`, `plutil`, `swift-demangle`, and `ipsw` are easier to use together.

## Main command

Use the new command:

```text
/analyze-ipa-symbols /path/to/Instagram.ipa
```

or run the script directly:

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

This fork has been repointed from a broad iOS security skill into a symbol-architecture skill. The inherited broad scripts remain in place for compatibility, but the intended workflow is now `/analyze-ipa-symbols` and `radan-symbol-architect.sh`.

## License

Same license as the upstream fork unless changed explicitly.
