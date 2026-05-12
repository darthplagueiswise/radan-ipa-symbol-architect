#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Run full IPA analysis and package a local artifact.

Usage:
  scripts/run_full_ipa_artifact.sh <input.ipa|Payload.app> [options]

Options:
  -o, --out DIR                 Output directory. Default: artifacts/radan-full-YYYYmmdd-HHMMSS
  --max-frameworks N            Frameworks to scan with Radan. Default: 80
  --ghidra                      Run Ghidra headless decompile/export phase if GHIDRA_HEADLESS is configured
  --ghidra-headless PATH        Path to Ghidra analyzeHeadless script
  --ghidra-project-dir DIR      Ghidra project directory. Default: <out>/.ghidra
  --ghidra-max-binaries N       Limit binaries imported into Ghidra. Default: 3
  --no-zip                      Do not zip final artifact
  -h, --help                    Show help

Environment:
  GHIDRA_HEADLESS=/path/to/ghidra/support/analyzeHeadless

Examples:
  scripts/run_full_ipa_artifact.sh input/ipa/Instagram.decrypted.ipa
  scripts/run_full_ipa_artifact.sh input/ipa/Instagram.decrypted.ipa --ghidra --ghidra-max-binaries 2
USAGE
}

die() { echo "[radan-full] error: $*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

INPUT=""
OUT=""
MAX_FRAMEWORKS=80
RUN_GHIDRA=0
GHIDRA_HEADLESS_BIN="${GHIDRA_HEADLESS:-}"
GHIDRA_PROJECT_DIR=""
GHIDRA_MAX_BINARIES=3
DO_ZIP=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--out) OUT="${2:-}"; shift 2;;
    --max-frameworks) MAX_FRAMEWORKS="${2:-80}"; shift 2;;
    --ghidra) RUN_GHIDRA=1; shift;;
    --ghidra-headless) GHIDRA_HEADLESS_BIN="${2:-}"; shift 2;;
    --ghidra-project-dir) GHIDRA_PROJECT_DIR="${2:-}"; shift 2;;
    --ghidra-max-binaries) GHIDRA_MAX_BINARIES="${2:-3}"; shift 2;;
    --no-zip) DO_ZIP=0; shift;;
    -h|--help) usage; exit 0;;
    -*) die "unknown option: $1";;
    *) if [[ -z "$INPUT" ]]; then INPUT="$1"; shift; else die "unexpected argument: $1"; fi;;
  esac
done

[[ -n "$INPUT" ]] || { usage; die "missing input"; }
[[ -e "$INPUT" ]] || die "input not found: $INPUT"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER="$REPO_ROOT/skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh"
[[ -f "$RUNNER" ]] || die "missing Radan runner: $RUNNER"

if [[ -z "$OUT" ]]; then OUT="$REPO_ROOT/artifacts/radan-full-$(date +%Y%m%d-%H%M%S)"; fi
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"

LOG="$OUT/run.log"
exec > >(tee -a "$LOG") 2>&1

echo "[radan-full] input: $INPUT"
echo "[radan-full] out:   $OUT"

echo "[radan-full] phase 1: static Radan IPA/Mach-O analysis"
bash "$RUNNER" "$INPUT" -o "$OUT/radan" --max-frameworks "$MAX_FRAMEWORKS"

if [[ "$RUN_GHIDRA" -eq 1 ]]; then
  if [[ -z "$GHIDRA_HEADLESS_BIN" ]]; then
    echo "[radan-full] GHIDRA_HEADLESS not set; skipping Ghidra phase"
  elif [[ ! -x "$GHIDRA_HEADLESS_BIN" ]]; then
    echo "[radan-full] Ghidra analyzeHeadless not executable: $GHIDRA_HEADLESS_BIN; skipping Ghidra phase"
  else
    echo "[radan-full] phase 2: Ghidra headless import/decompile"
    GHIDRA_PROJECT_DIR="${GHIDRA_PROJECT_DIR:-$OUT/.ghidra}"
    mkdir -p "$GHIDRA_PROJECT_DIR" "$OUT/ghidra"
    GHIDRA_SCRIPT_DIR="$REPO_ROOT/ghidra_scripts"
    POST_SCRIPT="ExportRadanDecompile.java"

    mapfile -t GHIDRA_BINS < <(head -n "$GHIDRA_MAX_BINARIES" "$OUT/radan/binaries.txt" || true)
    idx=0
    for bin in "${GHIDRA_BINS[@]}"; do
      [[ -f "$bin" ]] || continue
      idx=$((idx + 1))
      safe="$(basename "$bin" | tr '/ :' '___')"
      proj="radan_${idx}_${safe}"
      outdir="$OUT/ghidra/$idx-$safe"
      mkdir -p "$outdir"
      echo "[radan-full] Ghidra importing $bin"
      "$GHIDRA_HEADLESS_BIN" "$GHIDRA_PROJECT_DIR" "$proj" \
        -import "$bin" \
        -overwrite \
        -scriptPath "$GHIDRA_SCRIPT_DIR" \
        -postScript "$POST_SCRIPT" "$outdir" \
        -deleteProject || echo "[radan-full] Ghidra failed for $bin"
    done
  fi
fi

cat > "$OUT/README_ARTIFACT.md" <<EOF
# Radan Full IPA Artifact

Input: \`$INPUT\`
Generated: \`$(date -u +%Y-%m-%dT%H:%M:%SZ)\`

## Contents

- \`radan/00_inventory.md\` — static inventory and summary.
- \`radan/90_cross_binary_feature_gaps.md\` — feature split/gap report.
- \`radan/main/\` — main executable reports.
- \`radan/frameworks/\` — framework reports.
- \`ghidra/\` — optional headless Ghidra exports if enabled.
- \`run.log\` — full run log.

## Important

This artifact may contain proprietary symbols, decompiler output, strings and metadata. Keep it private unless you have permission to share it.
EOF

if [[ "$DO_ZIP" -eq 1 ]]; then
  ZIP="$OUT.decompile-artifact.zip"
  echo "[radan-full] packaging $ZIP"
  (cd "$(dirname "$OUT")" && zip -qr "$(basename "$ZIP")" "$(basename "$OUT")")
  echo "[radan-full] artifact zip: $ZIP"
fi

echo "[radan-full] done"
