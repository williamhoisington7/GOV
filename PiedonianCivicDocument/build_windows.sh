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
  -o dist

echo
echo "Build complete:"
echo "  dist/PiedonianCivicDocument.exe"
echo
