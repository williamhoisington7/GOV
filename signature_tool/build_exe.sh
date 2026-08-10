#!/usr/bin/env bash
# Build a one-file executable with PyInstaller (Linux/macOS host binary).
# For a Windows .exe, run build_windows.bat on Windows (or Windows CI).
set -euo pipefail
cd "$(dirname "$0")"

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-build.txt
python3 signature_manager.py --self-test

rm -rf build dist
python3 -m PyInstaller --noconfirm PiedonianSignatureManager.spec

echo
echo "Build complete under: dist/"
ls -la dist || true
echo "On Windows, prefer build_windows.bat to produce PiedonianSignatureManager.exe"
