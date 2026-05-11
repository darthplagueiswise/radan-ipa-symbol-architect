---
name: radan-ipa-symbol-architect
description: Analyze iOS IPA, .app, Mach-O, .dylib, and .framework targets with a strict symbol-architecture workflow. Use for cross-binary Objective-C/Swift metadata, Mach-O segments, sections, VM address to file offset mapping, symbols, selectors, selrefs, strings, first bytes/prologues, hook targets, MobileConfig/EasyGating getters, mc_bool_param_t stable IDs, Dogfooding/Direct Notes/QuickSnap/Story Tray/FriendMap/Icebreaker callsites, and RyukGram/Instagram tweak research. Prefer verified evidence over speculation. Do not use as a generic endpoint/security scanner unless explicitly asked.
---

# Radan IPA Symbol Architect

Radan is a focused iOS binary-analysis skill for tweak engineering and IPA architecture work. It is optimized for IPA extraction, Mach-O layout, Objective-C/Swift metadata, selectors, symbols, string anchors, callsite triage, hook target selection, and patch-candidate validation.

The skill should be used when the user asks about IPA architecture, Mach-O segments/sections/symbols/imports/exports/load commands, Objective-C class/method/selector metadata, Swift symbol demangling, VM address to file offset conversion, first bytes/prologue validation, MobileConfig and EasyGating getter analysis, Instagram/RyukGram tweak architecture, Dogfooding, Direct Notes, QuickSnap, Homecoming, Prism, LiquidGlass, TabBar, Story Tray, FriendMap, Icebreaker, DM Inline Like, or MetaLocalExperiment discovery.

Do not treat this skill as a broad security scanner by default. The inherited upstream scripts may still exist, but the primary Radan workflow is symbol/callsite/patch-validation oriented.

## Prime directive

No hallucinated binary facts.

For every symbol, selector, string, MobileConfig stable ID, or patch candidate, clearly separate verified static evidence, verified runtime evidence, manual labels, inferred labels, and unknown/unresolved items.

Never invent a resolved feature name for a hash, pointer-like token, MobileConfig ID, EasyGating token, or selector. If a value cannot be resolved, say that it is unresolved and preserve the raw value.

Never conclude that a feature is absent from Instagram after scanning only one framework. Many features split their evidence: MobileConfig params in `FBSharedFramework`, Swift/ObjC helpers in the main `Instagram` executable, and UI assets/strings in other frameworks. A single-binary result may say `not found in this binary`, not `not found in the app`.

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
90_cross_binary_feature_gaps.json
90_cross_binary_feature_gaps.md
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
mc_stable_id_hex
mc_stable_id_normalized_hex
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

For Instagram/RyukGram feature analysis, prefer the full IPA or extracted `.app`. If the user supplies only `FBSharedFramework`, mark the report as framework-only and explicitly require the main executable for helper selectors such as QuickSnap, NotesTray, Icebreaker and Inline Like.

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
_IGMobileConfigSessionlessBooleanValueForInternalUse
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
isQuicksnapEnabled:
isQuicksnapEnabledInInbox:
isQuicksnapEnabledAsPeek:
isQPEnabled:
_isEligibleForQuicksnapCornerStackTransitionDialog
IGDirectNotesExperimentHelper
IGDirectMutualInterestFeatureGatingService
ig_ios_quick_snap
ig_ios_quicksnap
ig_ios_instants
ig_quick_snap_show_peek_in_view_did_appear
ig_instants_hide
ig_test_sessioned_mc_ig_notes_friend_map_enabled
ig_friend_map_location_update
ig_ios_friend_map
ig_ios_friendmap
ig_ios_friends_map
ig_ios_friend_lane
ig_ios_notes_icebreakers
ctd_in_thread_icebreakers_ios_mc
biig_icebreaker_completeness_upsell_mc
igd_ios_default_icebreakers_in_faq_settings
ig_default_icebreaker_appointment
ig_ios_stories_tray
ig_ios_story_tray
ig_story_tray
ig_ios_stories_in_view_nav_tray
ig_empty_story_tray_su_redesign
dm_inline_like
direct_inline_like
inline_like
_METAIsLiquidGlassEnabled
_IGTabBarStyleForLauncherSet
```

When a match is found, report it as one of: symbol table hit, ObjC selector hit, ObjC class hit, C string hit, Swift demangled symbol hit, raw strings hit, decoded MobileConfig param, or unresolved raw byte/string hit.

### Phase 5 — Cross-binary feature gap report

After per-binary analysis, run:

```bash
python3 radan_feature_gap_report.py --report-root <output>
```

This must generate:

```text
90_cross_binary_feature_gaps.json
90_cross_binary_feature_gaps.md
```

Use this report to distinguish:

```text
main_executable_required
framework_evidence_only_need_main_for_callers
split_between_main_and_frameworks
not_found_in_scanned_binaries
```

`mc_bool_param_t` entries in `__TEXT,__const` should be decoded from their first 8 bytes as little-endian `mc_stable_id_hex` and normalized to `mc_stable_id_normalized_hex`. These decoded IDs are the values needed for targeted MC override work.

### Phase 6 — Patch candidate validation

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

### Phase 7 — Runtime validation handoff

When static evidence is insufficient, create a runtime validation plan using Frida/r2frida.

The plan should include bundle id, binary/module name, symbol or selector, expected address, hook type, log fields to capture, pass-through behavior, and crash-risk note.

Prefer pass-through logging before overriding values.

### Phase 8 — RyukGram branch guidance

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
