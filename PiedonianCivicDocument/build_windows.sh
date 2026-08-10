#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Piedonian Woods Civic Document - Windows EXE build ==="
dotnet --info
dotnet run -- --self-test

rm -rf dist
mkdir -p dist

dotnet publish -c Release -r win-x64 --self-contained true \
  -p:PublishSingleFile=true \
  -p:IncludeNativeLibrariesForSelfExtract=true \
  -p:EnableCompressionInSingleFile=true \
  -p:DebugType=None \
  -p:DebugSymbols=false \
  -o dist

# Keep only the standalone EXE in dist/ for distribution
find dist -mindepth 1 -maxdepth 1 ! -name 'PiedonianCivicDocument.exe' -exec rm -rf {} +

if [[ ! -f dist/PiedonianCivicDocument.exe ]]; then
  echo "BUILD FAILED: EXE not produced" >&2
  exit 1
fi

echo
echo "Build complete (true single-file EXE):"
echo "  dist/PiedonianCivicDocument.exe"
echo "Runtime data (created on first run beside the EXE):"
echo "  data/civic_signatures.json"
echo
