@echo off
setlocal
cd /d "%~dp0"

echo === Piedonian Woods Civic Document - Windows EXE build ===
dotnet --info || goto :error

dotnet run -- --self-test
if errorlevel 1 goto :error

if exist dist rmdir /s /q dist
mkdir dist

dotnet publish -c Release -r win-x64 --self-contained true ^
  -p:PublishSingleFile=true ^
  -p:IncludeNativeLibrariesForSelfExtract=true ^
  -p:EnableCompressionInSingleFile=true ^
  -o dist
if errorlevel 1 goto :error

echo.
echo Build complete:
echo   dist\PiedonianCivicDocument.exe
echo.
echo Run on Windows 11. Data file:
echo   data\civic_signatures.json
echo.
exit /b 0

:error
echo BUILD FAILED
exit /b 1
