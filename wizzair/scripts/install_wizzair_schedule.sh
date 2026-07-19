#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_SRC="$ROOT/scripts/com.wizzair.daily.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.wizzair.daily.plist"

mkdir -p "$HOME/Library/LaunchAgents"
sed "s|__PROJECT_ROOT__|$ROOT|g" "$PLIST_SRC" >"$PLIST_DEST"
launchctl bootout "gui/$(id -u)/com.wizzair.daily" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DEST"
launchctl enable "gui/$(id -u)/com.wizzair.daily"
echo "Installed $PLIST_DEST"
