#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Piedonian Woods Civic Document - Windows portable package ==="
dotnet --info
dotnet run -- --self-test

rm -rf dist package
mkdir -p dist package

dotnet publish -c Release -r win-x64 --self-contained true \
  -p:PublishSingleFile=true \
  -p:IncludeNativeLibrariesForSelfExtract=true \
  -p:EnableCompressionInSingleFile=true \
  -o dist

# Portable package: EXE + UI + document content (required together)
rm -f dist/*.pdb dist/*.xml 2>/dev/null || true
mkdir -p dist/data
cp -f data/.gitkeep dist/data/.gitkeep 2>/dev/null || touch dist/data/.gitkeep

PACKAGE_NAME="PiedonianCivicDocument-windows-x64"
STAGE="package/${PACKAGE_NAME}"
rm -rf "${STAGE}"
mkdir -p "${STAGE}"
cp -a dist/. "${STAGE}/"

(
  cd package
  if command -v zip >/dev/null 2>&1; then
    rm -f "${PACKAGE_NAME}.zip"
    zip -r "${PACKAGE_NAME}.zip" "${PACKAGE_NAME}"
    echo
    echo "Build complete:"
    echo "  dist/PiedonianCivicDocument.exe"
    echo "  package/${PACKAGE_NAME}.zip   << download & unzip this on Windows 11"
  else
    echo
    echo "Build complete (zip not available; use dist/ folder):"
    echo "  dist/PiedonianCivicDocument.exe"
    echo "  dist/wwwroot/"
    echo "  dist/Content/"
  fi
)

echo
echo "Keep wwwroot/ and Content/ next to the EXE. Signatures save to data/civic_signatures.json."
echo
