#!/usr/bin/env bash
# Clickable wrapper for install.sh — same logic, .command extension so
# Finder treats it as double-clickable on macOS.
exec "$(cd "$(dirname "$0")" && pwd)/install.sh"
