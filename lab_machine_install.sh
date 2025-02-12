#!/bin/sh
# This script installs Ollama on Linux to a user-specified home directory.

set -eu

red="$( (/usr/bin/tput bold || :; /usr/bin/tput setaf 1 || :) 2>&-)"
plain="$( (/usr/bin/tput sgr0 || :) 2>&-)"

status() { echo ">>> $*" >&2; }
error() { echo "${red}ERROR:${plain} $*"; exit 1; }
warning() { echo "${red}WARNING:${plain} $*"; }

TEMP_DIR=$(mktemp -d)
cleanup() { rm -rf $TEMP_DIR; }
trap cleanup EXIT

available() { command -v $1 >/dev/null; }
require() {
    local MISSING=''
    for TOOL in $*; do
        if ! available $TOOL; then
            MISSING="$MISSING $TOOL"
        fi
    done
    echo $MISSING
}

[ "$(uname -s)" = "Linux" ] || error 'This script is intended to run on Linux only.'

ARCH=$(uname -m)
case "$ARCH" in
    x86_64) ARCH="amd64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *) error "Unsupported architecture: $ARCH" ;;
esac

USERNAME=$(whoami)  # Get the current username dynamically
OLLAMA_INSTALL_DIR="/cs/student/projects1/2021/${USERNAME}/ollama"

mkdir -p "$OLLAMA_INSTALL_DIR/bin"

status "Downloading Linux ${ARCH} bundle"
curl --fail --show-error --location --progress-bar \
    "https://ollama.com/download/ollama-linux-${ARCH}.tgz" | \
    tar -xzf - -C "$OLLAMA_INSTALL_DIR"

ln -sf "$OLLAMA_INSTALL_DIR/bin/ollama" "$OLLAMA_INSTALL_DIR/ollama"

install_success() {
    status 'The Ollama API is now available at 127.0.0.1:11434.'
    status 'Install complete. Run "ollama" from the command line by adding the install directory to your PATH.'
    status 'For example, run: export PATH=$OLLAMA_INSTALL_DIR/bin:$PATH'
}
trap install_success EXIT

status "Installation complete. Add $OLLAMA_INSTALL_DIR/bin to your PATH to use Ollama."
