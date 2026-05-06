#!/usr/bin/env bash
#
# make-zip.sh — Build the customer-facing Playable org bundle.
#
# Uses `git archive HEAD` so only committed files end up in the zip.
# `.gitattributes` already strips CLAUDE.md / .gitignore / .gitattributes
# from the archive (export-ignore). node_modules, dist/, .embeddings-cache,
# lint-report-*.md are excluded automatically because they're gitignored.
#
# Output: playable-org-<YYYY-MM-DD>.zip in the repo root.
#
# Run after each round of changes you want to ship:
#     ./make-zip.sh

set -euo pipefail

cd "$(dirname "$0")"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "✗ Working tree is not clean. Commit or stash first."
  echo
  git status --short
  exit 1
fi

DATE="$(date +%Y-%m-%d)"
OUT="playable-org-$DATE.zip"

# `--prefix` puts everything inside an `playable-org/` folder when the zip is
# extracted, matching what SETUP.md tells the customer to expect.
git archive --format=zip --prefix="playable-org/" --output="$OUT" HEAD

SIZE_KB="$(du -k "$OUT" | cut -f1)"
SIZE_MB=$(( SIZE_KB / 1024 ))
N_FILES="$(unzip -l "$OUT" | tail -1 | awk '{print $2}')"

printf "\n\033[32m✓\033[0m %s\n" "$OUT"
printf "  size:  %s KB (~%s MB)\n" "$SIZE_KB" "$SIZE_MB"
printf "  files: %s\n" "$N_FILES"
printf "\nReady to send. The recipient extracts the zip, opens the resulting\n"
printf "playable-org/ folder, and double-clicks install.command (macOS) or\n"
printf "install.bat (Windows). See SETUP.md for the full procedure.\n"
