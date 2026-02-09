#!/bin/bash
# EVA-01 - Uninstall Script

set -e

INSTALL_DIR="$HOME/.local/bin"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    local level=$1
    local message=$2
    local color=""
    case $level in
        "INFO")  color=$BLUE ;;
        "ERROR") color=$RED ;;
        "SUCCESS") color=$GREEN ;;
    esac
    echo -e "${color}[$(date '+%H:%M:%S')] [$level] $message${NC}"
}

log "INFO" "Uninstalling EVA-01..."

# Remove command scripts
if [[ -f "$INSTALL_DIR/spec-to-prd" ]]; then
    rm -f "$INSTALL_DIR/spec-to-prd"
    log "INFO" "Removed $INSTALL_DIR/spec-to-prd"
fi

if [[ -f "$INSTALL_DIR/impl-prd" ]]; then
    rm -f "$INSTALL_DIR/impl-prd"
    log "INFO" "Removed $INSTALL_DIR/impl-prd"
fi

if [[ -f "$INSTALL_DIR/observe-impl" ]]; then
    rm -f "$INSTALL_DIR/observe-impl"
    log "INFO" "Removed $INSTALL_DIR/observe-impl"
fi

log "SUCCESS" "EVA-01 uninstalled successfully!"
echo ""
echo "Note: The project directory and uv environment are preserved."
echo "To fully remove, delete the project directory manually."
