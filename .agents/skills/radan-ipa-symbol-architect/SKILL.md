---
name: radan-ipa-symbol-architect
description: Analyze iOS IPA, .app, Mach-O, dylib, and framework binaries for symbol architecture: Mach-O segments, sections, VM-to-file offsets, Objective-C selectors, selrefs, strings, Swift symbols, first bytes/prologues, hook targets, MobileConfig/EasyGating/Dogfooding/Direct Notes/QuickSnap/LiquidGlass callsites, and RyukGram/Instagram patch validation. Use when the user needs verifiable binary evidence, not generic endpoint/security scanning.
metadata:
  short-description: IPA/Mach-O symbols, selectors, offsets, first bytes, and RyukGram targets
---

# Radan IPA Symbol Architect

This is the Codex-discoverable wrapper for the canonical Radan skill.

Canonical files live at:

```text
skills/ios-reverse-engineering/SKILL.md
skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh
skills/ios-reverse-engineering/scripts/macho_symbol_architect.py
skills/ios-reverse-engineering/references/ryukgram-instagram-target-profile.md
```

Use this skill for iOS IPA / Mach-O / Objective-C / Swift symbol architecture work. It is optimized for verifiable evidence: binary owner, architecture, segment, section, VM address, file offset, first bytes, selectors, selrefs, strings, class names, Swift demangled names, and target matches.

## Preferred command

Run from the repository root:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh <target.ipa|target.app|Mach-O|dylib|framework> -o ./radan-out
```

Focused example:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh /path/to/Instagram.ipa \
  -o ./radan-out \
  --pattern _IGMobileConfigBooleanValueForInternalUse \
  --pattern _MCIMobileConfigGetBoolean \
  --pattern openWithConfig:onViewController:userSession:
```

If running from inside this `.agents/skills/radan-ipa-symbol-architect` directory, use the wrapper:

```bash
bash scripts/run-radan.sh <target> -o ./radan-out
```

## Output contract

A useful run should produce:

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

Never invent feature names from hashes, pointer-like tokens, MobileConfig IDs, EasyGating tokens, selectors, or decoded values. Mark unresolved values as unresolved.

Never suggest an offline patch without:

```text
binary
symbol_or_selector
vmaddr
fileoff
old_first_8_bytes
old_first_16_bytes
new_bytes
risk
reason
runtime_validation_needed
```

## RyukGram / Instagram defaults

Default target families include:

```text
_IGMobileConfigBooleanValueForInternalUse
_MCIMobileConfigGetBoolean
_EasyGatingPlatformGetBoolean
_EasyGatingGetBoolean_Internal_DoNotUseOrMock
_IGAppIsInstagramInternalAppsInstalledAndNotHiddenAfteriOS18
openWithConfig:onViewController:userSession:
notesDogfoodingSettingsOpenOnViewController:userSession:
getBool
getBool:withDefault:
_getTranslatedSpecifier:
getStableIdFromParamSpecifier:
MetaLocalExperimentListViewController
IGDogfoodingSettingsViewController
IGDirectNotesDogfoodingSettings
IGQuickSnapExperimentationHelper
_METAIsLiquidGlassEnabled
_IGTabBarStyleForLauncherSet
```

Treat `DoNotUseOrMock`, `tryUpdateConfigs`, force-update and set-overrides paths as high risk. Prefer pass-through observation and per-value override workflows.

## Baseline validation

Before changing scripts, run syntax checks:

```bash
bash -n skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh
python3 -m py_compile skills/ios-reverse-engineering/scripts/macho_symbol_architect.py
```

If tools such as `ipsw`, `otool`, `nm`, or `swift-demangle` are missing, do not fake output. Continue with available evidence and report missing tools.
