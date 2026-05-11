# Integrating LIEF, ghidra_load_objc_headers and r2frida

This document defines how Radan IPA Symbol Architect should integrate three external projects:

- `lief-project/LIEF`
- `devm18426/ghidra_load_objc_headers`
- `nowsecure/r2frida`

The goal is to extract as many Instagram feature flags as possible, especially flags that pass through IGMobileConfig / FBMobileConfig / MCI / META Extension getters.

## Core principle

Always analyze a full decrypted IPA or extracted `.app` when the goal is feature discovery.

A single framework is not enough. Instagram commonly splits evidence like this:

```text
FBSharedFramework.framework
  MobileConfig param symbols, mc_bool_param_t data, C getters, param strings.

Payload/Instagram.app/Instagram
  Swift/ObjC helper classes, feature-gating services, selectors, callsites, UI entry points.

Other frameworks
  UI classes, assets, navigation glue, GraphQL helpers, Direct/Notes implementations.
```

Framework-only analysis may be useful for MC ID extraction, but it must be labelled as partial.

## Tool roles

### LIEF

Use LIEF as the deterministic Mach-O parser and optional future patch engine.

Radan should use it for:

- Mach-O segments, sections, symbols and imports/exports;
- Objective-C metadata when available;
- dyld chained fixups / rebases / binds;
- reliable VM address to file offset mapping;
- AArch64 disassembly where available;
- later: offline patch validation and write support.

LIEF should not replace the pure-Python fallback. The fallback keeps the skill usable in restricted environments. LIEF is an enhanced path.

Install:

```bash
pip install lief
# or
brew install lief
```

Preferred Radan output:

```text
11_lief_macho.json
11_lief_objc.json
11_lief_imports_exports.json
11_lief_fixups.json
```

### ghidra_load_objc_headers

Use this after header generation/class-dump and before deep callgraph/decompiler work.

Purpose:

- import Objective-C class/ivar/method type data into Ghidra;
- improve decompiler signatures;
- make `objc_msgSend` callsites easier to reason about;
- preserve class/method names found by class-dump / ipsw / ktool.

It is not the first analysis step. It is a Ghidra enrichment step.

Install pattern:

```bash
git clone https://github.com/devm18426/ghidra_load_objc_headers.git tools/ghidra_load_objc_headers
cd tools/ghidra_load_objc_headers
pip install -r requirements.txt
```

Header generation example:

```bash
classdump-dyld -b -h -o radan-out/headers/FBSharedFramework Payload/Instagram.app/Frameworks/FBSharedFramework.framework/FBSharedFramework
classdump-dyld -b -h -o radan-out/headers/Instagram Payload/Instagram.app/Instagram
```

Radan should emit a handoff script instead of pretending to run Ghidra automatically:

```text
12_ghidra_objc_header_handoff.md
12_ghidra_load_headers.sh
```

### r2frida

Use r2frida only for runtime validation.

Do not use it as the first source of truth. Static analysis should produce candidate symbols/selectors/IDs; r2frida validates whether the target is loaded, called, and what arguments pass at runtime.

Use it for:

- listing runtime classes/methods/protocols;
- confirming module ownership;
- tracing IGMobileConfig getter calls;
- confirming the real specifier value passed into getters;
- validating QuickSnap/FriendMap/Icebreaker/StoryTray helper methods;
- checking whether a static candidate is live on the current account/device.

Install:

```bash
r2pm -ci r2frida
```

Common connection examples:

```bash
r2 'frida://apps/usb//'
r2 'frida://attach/usb//Instagram'
r2 'frida://spawn/usb//com.burbn.instagram'
```

Preferred Radan output:

```text
13_r2frida_runtime_plan.md
13_r2frida_trace_igmobileconfig.js
13_r2frida_trace_selectors.js
```

## Feature-flag extraction pipeline

### Phase 0 — Input

Use a decrypted IPA whenever possible:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh Instagram.decrypted.ipa -o radan-out --max-frameworks 80
```

If using extracted app:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh Payload/Instagram.app -o radan-out --max-frameworks 80
```

Framework-only input is acceptable only for targeted MC param extraction:

```bash
bash skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh Payload/Instagram.app/Frameworks/FBSharedFramework.framework -o radan-fbshared-only
```

The report must say framework-only/partial.

### Phase 1 — Static inventory

Use current Radan scripts:

```text
00_inventory.md
binaries.txt
targets.txt
main/...
frameworks/...
90_cross_binary_feature_gaps.md
```

### Phase 2 — LIEF enhanced parsing

For every selected Mach-O, LIEF should export:

- header;
- commands;
- segments;
- sections;
- symbols;
- imports;
- exports;
- Objective-C metadata when exposed;
- dyld chained fixups;
- function starts if available.

Output should be normalized so the pure-Python and LIEF reports can be joined by:

```text
binary_path
segment
section
vmaddr
fileoff
symbol/string/selector
```

### Phase 3 — MC param extraction

From symbol + section data, identify likely MobileConfig params:

```text
name starts with _ig_, _ctd_, _biig_, _igd_, _msgc_, _mci_, _meta_
section is __TEXT,__const or another const/data section
first 8 bytes decode as little-endian uint64 stable ID
```

Output fields:

```text
name
binary
fileoff
vmaddr
section
first_8_bytes
mc_stable_id_hex
mc_stable_id_normalized_hex
feature_family_guess
```

### Phase 4 — Cross-binary feature grouping

Join MC params with main executable helpers/selectors.

Examples:

```text
QuickSnap/Instants:
  MC params: FBSharedFramework
  helpers/selectors: Instagram main executable

FriendMap/Maps:
  MC params: FBSharedFramework
  helpers/selectors: Instagram main executable / Direct Notes frameworks

Icebreaker:
  MC params: FBSharedFramework
  helper class: IGDirectMutualInterestFeatureGatingService in main executable

Story Tray:
  MC params: FBSharedFramework
  selector/callsite owners: main executable and nav/story frameworks
```

### Phase 5 — Ghidra enrichment

Generate headers and import them into Ghidra with `ghidra_load_objc_headers`.

Use this phase when:

- selectors exist but callsites are unclear;
- class/method ownership is ambiguous;
- Swift/ObjC bridge thunks hide arguments;
- `objc_msgSend` sites need type recovery.

Do not make final hook decisions from header names alone. Headers improve decompiler structure; they do not prove runtime eligibility.

### Phase 6 — r2frida runtime validation

Use static candidates to generate small runtime trace scripts.

Trace targets:

```text
_IGMobileConfigBooleanValueForInternalUse
_IGMobileConfigSessionlessBooleanValueForInternalUse
_MCIMobileConfigGetBoolean
IGMobileConfigContextManager getBool variants
QuickSnap helper selectors
FriendMap / DirectNotes helper selectors
Icebreaker gating selectors
Story Tray selectors
```

Runtime validation should answer:

- Is this symbol/class loaded?
- Which module owns it?
- Is it called on this account/session?
- What stable ID/specifier value is passed?
- What is the original return value?
- Which caller address/module triggered it?

## Radan output contract extension

Future runs should include:

```text
11_lief_macho.json
11_lief_objc.json
11_lief_imports_exports.json
11_lief_fixups.json
12_ghidra_objc_header_handoff.md
12_ghidra_load_headers.sh
13_r2frida_runtime_plan.md
13_r2frida_trace_igmobileconfig.js
13_r2frida_trace_selectors.js
```

## Why full decrypted IPA is better

Yes: send the full decrypted IPA when the task is feature extraction.

Reasons:

1. MC params often live in `FBSharedFramework`.
2. Swift helpers often live in `Instagram` main executable.
3. UI/nav callsites may live in other frameworks.
4. Cross-binary ownership is required to avoid false negatives.
5. Runtime trace scripts need module names from the whole app.

Send only a framework when the task is narrow, for example:

- extract all `_ig_*` MC param IDs from FBSharedFramework;
- verify one symbol fingerprint;
- compare one framework across versions;
- compute file offset for one known symbol.

For `todas features flags que passam pelo IGMobileConfig`, framework-only is not enough. Use full decrypted IPA.
