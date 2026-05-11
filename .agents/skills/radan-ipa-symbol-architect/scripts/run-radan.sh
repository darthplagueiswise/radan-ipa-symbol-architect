#!/usr/bin/env bash
set -euo pipefail

# Codex-discoverable wrapper. The canonical runner lives outside .agents so the
# same implementation is shared by Claude Code, Codex, and manual CLI use.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
CANONICAL="$REPO_ROOT/skills/ios-reverse-engineering/scripts/radan-symbol-architect.sh"

if [[ ! -f "$CANONICAL" ]]; then
  echo "[radan] canonical runner not found: $CANONICAL" >&2
  exit 1
fi

exec bash "$CANONICAL" "$@"
