#!/usr/bin/env bash
# build.sh — Build the packaged EDA Report application
#
# Prerequisites
# -------------
# 1. Conda environment eda-report is active: conda activate eda-report
# 2. PyInstaller is installed: pip install pyinstaller>=6.5
# 3. Quarto standalone binary is placed at installer/quarto/
#    Download from https://quarto.org/docs/get-started/
#    Windows: quarto-X.Y.Z-win.zip  → extract to installer/quarto/
#    macOS:   quarto-X.Y.Z-macos.pkg → install, then copy /usr/local/lib/quarto → installer/quarto/
#
# Usage
# -----
#   bash installer/build.sh [windows|macos]   # defaults to current platform

set -euo pipefail

PLATFORM="${1:-$(uname -s | tr '[:upper:]' '[:lower:]')}"

# Normalize platform string
case "$PLATFORM" in
  windows|win|Windows)  PLATFORM="windows" ;;
  darwin|macos|macOS)   PLATFORM="macos"   ;;
  linux|Linux)
    echo "ERROR: Linux packaging is not a target platform for this tool."
    exit 1 ;;
esac

echo "==> Building for platform: $PLATFORM"

# Verify quarto bundle exists
QUARTO_DIR="$(dirname "$0")/quarto"
if [ ! -d "$QUARTO_DIR" ]; then
  echo "ERROR: $QUARTO_DIR not found."
  echo "  Download the Quarto standalone binary for $PLATFORM and extract to installer/quarto/"
  exit 1
fi

# Run PyInstaller
SPEC="$(dirname "$0")/build_${PLATFORM}.spec"
if [ ! -f "$SPEC" ]; then
  echo "ERROR: Spec file not found: $SPEC"
  exit 1
fi

pyinstaller "$SPEC" --clean --noconfirm

echo ""
echo "==> Build complete."
if [ "$PLATFORM" = "windows" ]; then
  echo "    Output: installer/dist/EDA Report.exe"
  echo "    Test on a clean Windows VM with no Python installed."
elif [ "$PLATFORM" = "macos" ]; then
  echo "    Output: installer/dist/EDA Report.app"
  echo "    Sign with: codesign --deep --sign - 'installer/dist/EDA Report.app'"
  echo "    Test on a clean macOS machine with no Python installed."
fi
