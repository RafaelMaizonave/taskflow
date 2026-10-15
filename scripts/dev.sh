#!/usr/bin/env bash
# Interface CLI multiplataforma (Linux, macOS, WSL) para o TaskFlow.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

dispatch "${1:-help}" "${@:2}"
