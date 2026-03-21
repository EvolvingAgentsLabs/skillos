#!/bin/bash
# SkillOS Terminal Launcher
# Delegates to the Python runtime for markdown rendering

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/skillos.py" "$@"
