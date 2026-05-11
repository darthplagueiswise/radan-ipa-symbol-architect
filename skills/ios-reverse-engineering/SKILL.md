---
name: radan-ipa-symbol-architect
description: Analyze iOS IPA, .app, Mach-O, .dylib, and .framework targets with a strict symbol-architecture workflow. Use for Objective-C/Swift metadata, Mach-O segments, sections, VM address to file offset mapping, symbols, selectors, selrefs, strings, first bytes/prologues, hook targets, offline patch candidates, MobileConfig/EasyGating getters, Dogfooding/Direct Notes callsites, and RyukGram/Instagram tweak research. Prefer verified evidence over speculation. Do not use as a generic endpoint/security scanner unless explicitly asked.
---

# Radan IPA Symbol Architect

Radan is a focused iOS binary-analysis skill for tweak engineering and IPA architecture work. It is optimized for IPA extraction, Mach-O layout, Objective-C/Swift metadata, selectors, symbols, string anchors, callsite triage, hook target selection, and patch-candidate validation.

The skill should be used when the user asks about IPA architecture, Mach-O segments/sections/symbols/imports/exports/load commands, Objective-C class/method/selector metadata, Swift symbol demangling, VM address to file offset conversion, first bytes/prologue validation, MobileConfig and EasyGating getter analysis, Instagram/RyukGram tweak architecture, Dogfooding, Direct Notes, QuickSnap, Homecoming, Prism, LiquidGlass, TabBar, or MetaLocalExperiment discovery.

Do not treat this skill as a broad security scanner by default. The inherited upstream scripts may still exist, but the primary Radan workflow is symbol/callsite/patch-validation oriented.

## Prime directive

No hallucinated binary facts.

For every symbol, selector, string, or patch candidate, clearly separate verified static evidence, verified runtime evidence, manual labels, inferred labels, and unknown/unresolved items.

Never invent a resolved feature name for a hash, pointer-like token, MobileConfig ID, EasyGating token, or selector. If a value cannot be resolved, say that it is unresolved and preserve the raw value.

## Core commands

### Preferred command

```bash
/analyze-ipa-symbols <ipa-or-app-or-binary> [patterns...]
```

This command should run:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh <target> -o <output>
```

For target patterns:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh <target> \
  -o <output> \
  --pattern _IGMobileConfigBooleanValueForInternalUse \
  --pattern _MCIMobileConfigGetBoolean \
  --pattern openWithConfig:onViewController:userSession:
```

### Legacy command

`/extract-ipa` is still available, but prefer `/analyze-ipa-symbols` when the user is asking about symbols, selectors, callsites, hook targets or patch offsets.

## Required output contract

A completed analysis should produce or request the following output files:

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
frameworks/<name>/...
```

If any file cannot be produced because the tool is missing or the binary is stripped/encrypted, state that explicitly.

## Evidence fields

For every relevant hit, preserve as many of these as possible:

```text
input_path
binary_path
binary_role: main | framework | dylib | extension | unknown
architecture
install_name
symbol
selector
class_name
method_name
string
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

## Workflow

### Phase 1 — Identify target type

Accept `.ipa`, `.app`, executable Mach-O, `.dylib`, `.framework`, extracted `Payload/*.app`, or an individual framework binary.

If the input is an IPA, extract it into the output directory and locate:

```text
Payload/*.app
CFBundleExecutable
Frameworks/*.framework/*
Frameworks/*.dylib
PlugIns/*.appex/*
```

### Phase 2 — Build binary inventory

Create `00_inventory.md` and `binaries.txt`.

For each binary, record path, role, file type, architecture, size, executable bit, framework/app container, encryption hints, stripped-symbol hints, and whether ObjC sections exist.

### Phase 3 — Static Mach-O mapping

For each selected binary, run the Radan analyzer and baseline tools:

```bash
python3 macho_symbol_architect.py --binary <binary> --out <out-dir> --patterns-file <targets.txt>
file <binary>
otool -hv <binary>
otool -l <binary>
nm -m <binary>
strings -a <binary>
```

If available, also run:

```bash
ipsw class-dump <binary>
ipsw macho info <binary>
swift-demangle
```

The minimum useful output is segment/section mapping, symbol table mapping, ObjC metadata sections, selectors and selrefs, string sections, and target matches with VM/file offsets and first bytes.

### Phase 4 — Targeted selector/symbol search

Default RyukGram/Instagram target patterns include:

```text
_IGMobileConfigBooleanValueForInternalUse
_IGMobileConfigForceUpdateConfigs
_IGMobileConfigSetConfigOverrides
_IGMobileConfigTryUpdateConfigsWithCompletion
_MCIMobileConfigGetBoolean
_MCIExperimentCacheGetMobileConfigBoolean
_MCIExtensionExperimentCacheGetMobileConfigBoolean
_METAExtensionsExperimentGetBoolean
_METAExtensionsExperimentGetBooleanWithoutExposure
_MSGCSessionedMobileConfigGetBoolean
_EasyGatingPlatformGetBoolean
_EasyGatingGetBoolean_Internal_DoNotUseOrMock
_EasyGatingGetBooleanUsingAuthDataContext_Internal_DoNotUseOrMock
_MCQEasyGatingGetBooleanInternalDoNotUseOrMock
_IGAppIsInstagramInternalAppsInstalledAndNotHiddenAfteriOS18
openWithConfig:onViewController:userSession:
notesDogfoodingSettingsOpenOnViewController:userSession:
initWithConfig:userSession:
getBool
getBool:
getBool:withDefault:
getBool:withOptions:
getBool:withOptions:withDefault:
getBoolWithoutLogging
_getTranslatedSpecifier:
getStableIdFromParamSpecifier:
MetaLocalExperimentListViewController
MetaLocalExperimentDetailViewController
IGDogfoodingSettingsViewController
IGDogfoodingSettingsSelectionViewController
IGDirectNotesDogfoodingSettings
IGQuickSnapExperimentationHelper
IGNotesTrayController
_METAIsLiquidGlassEnabled
_IGTabBarStyleForLauncherSet
```

When a match is found, report it as one of: symbol table hit, ObjC selector hit, ObjC class hit, C string hit, Swift demangled symbol hit, raw strings hit, or unresolved raw byte/string hit.

### Phase 5 — Patch candidate validation

Never suggest an offline patch without all of this:

```text
symbol_or_selector
binary
vmaddr
fileoff
first_8_bytes
first_16_bytes
expected_stub_bytes
risk
reason
```

For AArch64 boolean/enum force-on patches, common bytes are:

```text
mov w0, #1 ; ret
20 00 80 52 c0 03 5f d6
```

But do not apply this blindly. Confirm whether the target is a bool getter, enum getter, C function, Swift thunk, ObjC method IMP, branch gate, or wrapper. If unknown, mark it unsafe.

### Phase 6 — Runtime validation handoff

When static evidence is insufficient, create a runtime validation plan using Frida/r2frida.

The plan should include bundle id, binary/module name, symbol or selector, expected address, hook type, log fields to capture, pass-through behavior, and crash-risk note.

Prefer pass-through logging before overriding values.

### Phase 7 — RyukGram branch guidance

When the analysis is for RyukGram branches such as `dev`, `alpha3`, `beta1`, or `beta2`, connect the binary evidence back to code architecture without inventing facts.

The safe architecture direction is one owner for C MobileConfig/EasyGating broker hooks; ObjC getter observer remains pass-through unless explicitly toggled; per-value override namespace; no startup-wide blanket observer; no default-on heavy observer; no default-on `DoNotUseOrMock` overrides; no UI menu duplication; resolver output must carry source labels such as `manual`, `runtime-callsite`, `schema`, `id_name_mapping`, `mach-o`, `decoded-id`, or `unresolved`.

## Tool preferences

Preferred stack:

1. `blacktop/ipsw` for class-dump, Mach-O info/search/disassembly and dyld/iOS research.
2. `LIEF` for deterministic Mach-O parsing and future patch tooling.
3. `ktool` for portable Python Mach-O/ObjC extraction.
4. `otool`, `nm`, `strings`, `plutil`, `codesign` for baseline verification.
5. `swift-demangle` for Swift names.
6. `r2frida` for runtime verification.
7. Ghidra headless for deeper callgraph/decompiler work.

## Response style for this skill

When reporting findings, be direct; include exact paths and offsets; do not over-explain generic iOS concepts; mark uncertainty visibly; prefer tables for symbol/callsite findings; never bury first bytes or file offsets; separate “safe to hook”, “needs runtime validation”, and “unsafe to patch”.

## Failure handling

If a tool is missing, do not fake its output. Say what was missing and continue with lower-level tools when possible. For example, if `ipsw` is missing, still run the Python Mach-O analyzer, `nm`, `otool`, and `strings`.

If the binary appears encrypted or unreadable, report that static results are incomplete and request a decrypted IPA or dumped binary.
