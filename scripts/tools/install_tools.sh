#!/usr/bin/env bash
set -euo pipefail

OS="$(uname -s)"

function install_macos() {
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew not found. Please install Homebrew: https://brew.sh" >&2
    exit 1
  fi
  brew update
  brew install poppler tesseract
}

function install_linux() {
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y poppler-utils tesseract-ocr curl
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm poppler tesseract curl
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y poppler-utils tesseract curl || sudo dnf install -y poppler tesseract curl
    # On Fedora, English language data may be in tesseract-langpack-eng
    if ! tesseract --list-langs 2>/dev/null | grep -qi '^eng$'; then
      sudo dnf install -y tesseract-langpack-eng || true
    fi
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y poppler-utils tesseract curl || sudo yum install -y poppler tesseract curl
  elif command -v zypper >/dev/null 2>&1; then
    sudo zypper refresh
    sudo zypper install -y poppler-tools tesseract curl || sudo zypper install -y poppler tesseract curl
  else
    echo "Unsupported Linux distro. Please install poppler and tesseract using your package manager." >&2
    exit 1
  fi
}

function ensure_tessdata() {
  : "${TESSDATA_PREFIX:=${HOME}/tessdata}"
  mkdir -p "${TESSDATA_PREFIX}"
  if [ ! -f "${TESSDATA_PREFIX}/eng.traineddata" ]; then
    echo "Downloading eng.traineddata..."
    curl -fsSL "https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/eng.traineddata" -o "${TESSDATA_PREFIX}/eng.traineddata"
  fi
}

case "$OS" in
  Darwin)
    install_macos
    ;;
  Linux)
    install_linux
    ;;
  *)
    echo "Unsupported OS: $OS" >&2
    exit 1
    ;;
 esac

ensure_tessdata

echo "Done. Poppler and Tesseract installed, TESSDATA_PREFIX=${TESSDATA_PREFIX}, eng.traineddata present."
