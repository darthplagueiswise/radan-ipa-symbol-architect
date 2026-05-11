#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Radan IPA Symbol Architect

Usage:
  radan-symbol-architect.sh <target.ipa|target.app|Mach-O|dylib|framework> [options]

Options:
  -o, --out DIR              Output directory
  --pattern TEXT             Add target symbol/selector/string pattern
  --patterns-file FILE       Add target patterns from file
  --max-frameworks N         Limit frameworks analyzed after main binary (default: 25)
  --no-frameworks            Analyze only the main binary
  -h, --help                 Show this help

Examples:
  bash radan-symbol-architect.sh Instagram.ipa -o ./radan-out
  bash radan-symbol-architect.sh Instagram.ipa -o ./radan-out --pattern _MCIMobileConfigGetBoolean
USAGE
}

die() { echo "[radan] error: $*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

TARGET=""
OUT=""
PATTERNS=()
PATTERNS_FILE=""
MAX_FRAMEWORKS=25
SCAN_FRAMEWORKS=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--out) OUT="${2:-}"; shift 2;;
    --pattern) PATTERNS+=("${2:-}"); shift 2;;
    --patterns-file) PATTERNS_FILE="${2:-}"; shift 2;;
    --max-frameworks) MAX_FRAMEWORKS="${2:-25}"; shift 2;;
    --no-frameworks) SCAN_FRAMEWORKS=0; shift;;
    -h|--help) usage; exit 0;;
    -*) die "unknown option: $1";;
    *)
      if [[ -z "$TARGET" ]]; then TARGET="$1"; shift
      else PATTERNS+=("$1"); shift
      fi;;
  esac
done

[[ -n "$TARGET" ]] || { usage; die "missing target"; }
[[ -e "$TARGET" ]] || die "target not found: $TARGET"

if [[ -z "$OUT" ]]; then OUT="./radan-analysis-$(date +%Y%m%d-%H%M%S)"; fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_ANALYZER="$SCRIPT_DIR/macho_symbol_architect.py"
[[ -f "$PY_ANALYZER" ]] || die "missing analyzer: $PY_ANALYZER"

mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"

DEFAULT_TARGETS="$OUT/default-ryukgram-targets.txt"
cat > "$DEFAULT_TARGETS" <<'EOF'
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
IGLiquidGlassInteractiveTabBar
IGLiquidGlassTabBarIndicatorView
IGDSColorLiquidGlassElevatedSeparator
EOF

TARGETS_FILE="$OUT/targets.txt"
if [[ -n "$PATTERNS_FILE" ]]; then cp "$PATTERNS_FILE" "$TARGETS_FILE"; else cp "$DEFAULT_TARGETS" "$TARGETS_FILE"; fi
for p in "${PATTERNS[@]}"; do [[ -n "$p" ]] && echo "$p" >> "$TARGETS_FILE"; done
awk 'NF && !seen[$0]++' "$TARGETS_FILE" > "$TARGETS_FILE.tmp" && mv "$TARGETS_FILE.tmp" "$TARGETS_FILE"

WORK="$OUT/work"
mkdir -p "$WORK"
APP_DIR=""
MAIN_BINARY=""
lower_target="$(printf '%s' "$TARGET" | tr '[:upper:]' '[:lower:]')"

if [[ "$lower_target" == *.ipa ]]; then
  have unzip || die "unzip is required for IPA extraction"
  EXTRACT_DIR="$WORK/extracted"
  mkdir -p "$EXTRACT_DIR"
  unzip -q "$TARGET" -d "$EXTRACT_DIR"
  APP_DIR="$(find "$EXTRACT_DIR/Payload" -maxdepth 1 -type d -name "*.app" | head -n 1 || true)"
  [[ -n "$APP_DIR" ]] || die "could not find Payload/*.app inside IPA"
elif [[ -d "$TARGET" && "$lower_target" == *.app ]]; then
  APP_DIR="$TARGET"
elif [[ -d "$TARGET" && "$lower_target" == *.framework ]]; then
  base="$(basename "$TARGET" .framework)"
  MAIN_BINARY="$TARGET/$base"
  [[ -f "$MAIN_BINARY" ]] || MAIN_BINARY="$(find "$TARGET" -maxdepth 1 -type f | head -n 1 || true)"
else
  MAIN_BINARY="$TARGET"
fi

if [[ -n "$APP_DIR" ]]; then
  plist="$APP_DIR/Info.plist"
  exe=""
  if have /usr/libexec/PlistBuddy && [[ -f "$plist" ]]; then exe="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$plist" 2>/dev/null || true)"; fi
  if [[ -z "$exe" && -f "$plist" ]] && have plutil; then exe="$(plutil -extract CFBundleExecutable raw -o - "$plist" 2>/dev/null || true)"; fi
  if [[ -z "$exe" ]]; then exe="$(basename "$APP_DIR" .app)"; fi
  MAIN_BINARY="$APP_DIR/$exe"
  [[ -f "$MAIN_BINARY" ]] || die "main executable not found: $MAIN_BINARY"
fi

[[ -f "$MAIN_BINARY" ]] || die "binary not found: $MAIN_BINARY"

BINARIES="$OUT/binaries.txt"
: > "$BINARIES"
echo "$MAIN_BINARY" >> "$BINARIES"
if [[ "$SCAN_FRAMEWORKS" -eq 1 && -n "$APP_DIR" && -d "$APP_DIR/Frameworks" ]]; then
  find "$APP_DIR/Frameworks" -type f \( -perm -111 -o -name "*.dylib" \) | head -n "$MAX_FRAMEWORKS" >> "$BINARIES" || true
fi

write_raws() {
  local bin="$1"; local dir="$2"
  mkdir -p "$dir/raw"
  (file "$bin" || true) > "$dir/raw/file.txt" 2>&1
  (strings -a "$bin" || true) > "$dir/raw/strings.txt" 2>&1
  if have nm; then (nm -m "$bin" || nm "$bin" || true) > "$dir/raw/nm.txt" 2>&1; else echo "nm not available" > "$dir/raw/nm.txt"; fi
  if have otool; then
    (otool -hv "$bin" || true) > "$dir/raw/otool_headers.txt" 2>&1
    (otool -l "$bin" || true) > "$dir/raw/otool_load_commands.txt" 2>&1
    (otool -Iv "$bin" || true) > "$dir/raw/otool_indirect_symbols.txt" 2>&1
  else
    echo "otool not available" > "$dir/raw/otool_headers.txt"
    echo "otool not available" > "$dir/raw/otool_load_commands.txt"
    echo "otool not available" > "$dir/raw/otool_indirect_symbols.txt"
  fi
  if have ipsw; then
    (ipsw class-dump "$bin" || true) > "$dir/raw/ipsw_class_dump.txt" 2>&1
    (ipsw macho info "$bin" || true) > "$dir/raw/ipsw_macho_info.txt" 2>&1
  else
    echo "ipsw not available" > "$dir/raw/ipsw_class_dump.txt"
    echo "ipsw not available" > "$dir/raw/ipsw_macho_info.txt"
  fi
  if have swift-demangle; then
    grep -E '(__T|_\$s|_\$S|_Tt[CVOP])' "$dir/raw/strings.txt" 2>/dev/null | swift-demangle > "$dir/04_swift_demangled_symbols.txt" 2>/dev/null || true
  else
    echo "swift-demangle not available" > "$dir/04_swift_demangled_symbols.txt"
  fi
}

analyze_one() {
  local bin="$1"; local dir="$2"
  mkdir -p "$dir"
  write_raws "$bin" "$dir"
  python3 "$PY_ANALYZER" --binary "$bin" --out "$dir" --patterns-file "$TARGETS_FILE" || {
    echo "# Analyzer failed" > "$dir/07_target_matches.md"
    echo "" >> "$dir/07_target_matches.md"
    echo "Binary: \`$bin\`" >> "$dir/07_target_matches.md"
    echo "" >> "$dir/07_target_matches.md"
    echo "The pure-Python Mach-O analyzer could not parse this file. Check raw/file.txt and raw/otool_load_commands.txt." >> "$dir/07_target_matches.md"
  }
}

analyze_one "$MAIN_BINARY" "$OUT/main"

fw_count=0
if [[ "$SCAN_FRAMEWORKS" -eq 1 ]]; then
  while IFS= read -r bin; do
    [[ "$bin" == "$MAIN_BINARY" ]] && continue
    [[ -f "$bin" ]] || continue
    fw_count=$((fw_count + 1))
    name="$(basename "$bin" | tr '/ :' '___')"
    analyze_one "$bin" "$OUT/frameworks/$fw_count-$name"
  done < "$BINARIES"
fi

{
  echo "# Radan IPA Symbol Architect Inventory"
  echo
  echo "- Target: \`$TARGET\`"
  echo "- Output: \`$OUT\`"
  echo "- App dir: \`${APP_DIR:-n/a}\`"
  echo "- Main binary: \`$MAIN_BINARY\`"
  echo "- Framework scan: \`$SCAN_FRAMEWORKS\`"
  echo "- Frameworks analyzed: \`$fw_count\`"
  echo
  echo "## Tool availability"
  echo
  for t in python3 unzip file strings nm otool ipsw swift-demangle; do
    if have "$t"; then echo "- $t: $(command -v "$t")"; else echo "- $t: missing"; fi
  done
  echo
  echo "## Binaries"
  echo
  sed 's/^/- `/' "$BINARIES" | sed 's/$/`/'
  echo
  echo "## Main target matches"
  echo
  if [[ -f "$OUT/main/07_target_matches.md" ]]; then cat "$OUT/main/07_target_matches.md"; else echo "No main target match report was produced."; fi
} > "$OUT/00_inventory.md"

echo "[radan] done"
echo "[radan] inventory: $OUT/00_inventory.md"
echo "[radan] binaries:   $OUT/binaries.txt"
echo "[radan] targets:    $OUT/targets.txt"
echo "[radan] main hits:  $OUT/main/07_target_matches.md"
