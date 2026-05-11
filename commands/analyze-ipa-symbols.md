---
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
description: Analyze an IPA, app, Mach-O, dylib, or framework for symbols, selectors, selrefs, VM/file offsets, first bytes, and RyukGram/Instagram target callsites
user-invocable: true
argument-hint: <path to IPA/.app/Mach-O/.framework> [target patterns...]
argument: path to target plus optional symbol/selector/string patterns
---

# /analyze-ipa-symbols

Run the Radan IPA Symbol Architect workflow.

This command is for symbol architecture, not broad API/security scanning. Use it when the user asks about IPA internals, Mach-O layout, selectors, symbols, callsites, VM addresses, file offsets, first bytes, hook targets, MobileConfig/EasyGating getters, Dogfooding, Direct Notes, QuickSnap, Homecoming, Prism, LiquidGlass, or RyukGram branch validation.

## Instructions

### 1. Resolve the target

Use the first argument as the target path. If no path was supplied, ask for the IPA, `.app`, Mach-O binary, `.dylib`, or `.framework` path.

Do not continue without a target path.

### 2. Prepare default output

Use an output directory named:

```bash
./radan-analysis-$(date +%Y%m%d-%H%M%S)
```

unless the user explicitly supplied another directory.

### 3. Parse optional patterns

Everything after the first argument is a target pattern. Pass each one to the script as `--pattern`.

If no explicit patterns were supplied, allow the script to use its built-in RyukGram/Instagram target list.

### 4. Run the analyzer

Run:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh <target> -o <output>
```

With patterns:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh <target> -o <output> \
  --pattern "<pattern1>" \
  --pattern "<pattern2>"
```

### 5. Read the resulting reports

Read at least:

```text
00_inventory.md
binaries.txt
targets.txt
main/07_target_matches.md
```

If frameworks were analyzed, inspect relevant framework `07_target_matches.md` files too.

### 6. Report back

Summarize:

- main binary path;
- frameworks scanned;
- exact target hits;
- VM addresses;
- file offsets;
- first 8/16 bytes;
- selector/class/string ownership;
- unresolved items;
- safe next steps.

For RyukGram work, explicitly separate static evidence, runtime validation still needed, patch candidates, hooks that should stay pass-through, and unsafe broad overrides.
