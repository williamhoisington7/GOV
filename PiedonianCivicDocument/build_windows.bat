@echo off
setlocal
cd /d "%~dp0"

echo === Piedonian Woods Civic Document - Windows portable package ===
dotnet --info
if errorlevel 1 exit /b 1

dotnet run -- --self-test
if errorlevel 1 exit /b 1

if exist dist rmdir /s /q dist
if exist package rmdir /s /q package
mkdir dist
mkdir package

dotnet publish -c Release -r win-x64 --self-contained true ^
  -p:PublishSingleFile=true ^
  -p:IncludeNativeLibrariesForSelfExtract=true ^
  -p:EnableCompressionInSingleFile=true ^
  -o dist
if errorlevel 1 exit /b 1

del /q dist\*.pdb 2>nul
if not exist dist\data mkdir dist\data
if exist data\.gitkeep copy /y data\.gitkeep dist\data\.gitkeep >nul

set PACKAGE_NAME=PiedonianCivicDocument-windows-x64
mkdir "package\%PACKAGE_NAME%"
xcopy /e /i /y dist "package\%PACKAGE_NAME%" >nul

powershell -NoProfile -Command "Compress-Archive -Path 'package\%PACKAGE_NAME%\*' -DestinationPath 'package\%PACKAGE_NAME%.zip' -Force"
if errorlevel 1 (
  echo WARNING: Could not create ZIP. Use the dist\ folder directly.
) else (
  echo.
  echo Build complete:
  echo   dist\PiedonianCivicDocument.exe
  echo   package\%PACKAGE_NAME%.zip   ^<^< download ^& unzip this on Windows 11
)

echo.
echo Keep wwwroot\ and Content\ next to the EXE.
echo Signatures save to data\civic_signatures.json beside the EXE.
echo.
endlocal
