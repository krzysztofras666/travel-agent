#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MORNING_SRC="$ROOT/scripts/com.wizzair.daily.plist"
AFTERNOON_SRC="$ROOT/scripts/com.wizzair.afternoon.plist"
MORNING_DEST="$HOME/Library/LaunchAgents/com.wizzair.daily.plist"
AFTERNOON_DEST="$HOME/Library/LaunchAgents/com.wizzair.afternoon.plist"

mkdir -p "$HOME/Library/LaunchAgents"
sed "s|__PROJECT_ROOT__|$ROOT|g" "$MORNING_SRC" >"$MORNING_DEST"
sed "s|__PROJECT_ROOT__|$ROOT|g" "$AFTERNOON_SRC" >"$AFTERNOON_DEST"

launchctl bootout "gui/$(id -u)/com.wizzair.daily" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/com.wizzair.afternoon" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$MORNING_DEST"
launchctl bootstrap "gui/$(id -u)" "$AFTERNOON_DEST"
launchctl enable "gui/$(id -u)/com.wizzair.daily"
launchctl enable "gui/$(id -u)/com.wizzair.afternoon"
echo "Installed:"
echo "  $MORNING_DEST   (08:00 — pełny digest)"
echo "  $AFTERNOON_DEST (13:00 — tylko zmiany)"
