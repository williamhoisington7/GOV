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
  -p:DebugType=None ^
  -p:DebugSymbols=false ^
  -o dist
if errorlevel 1 goto :error

rem Keep only the standalone EXE for distribution
if exist dist\wwwroot rmdir /s /q dist\wwwroot
if exist dist\Content rmdir /s /q dist\Content
if exist dist\*.pdb del /q dist\*.pdb
if exist dist\*.json del /q dist\*.json

if not exist dist\PiedonianCivicDocument.exe goto :error

echo.
echo Build complete (true single-file EXE):
echo   dist\PiedonianCivicDocument.exe
echo.
echo Run on Windows 11. Data file created on first run:
echo   data\civic_signatures.json
echo.
exit /b 0

:error
echo BUILD FAILED
exit /b 1
