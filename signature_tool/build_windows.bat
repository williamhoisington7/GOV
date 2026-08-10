@echo off
setlocal
cd /d "%~dp0"

echo === Piedonian Woods Signature Manager - Windows EXE build ===
python --version || goto :error

python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
if errorlevel 1 goto :error

python signature_manager.py --self-test
if errorlevel 1 goto :error

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m PyInstaller --noconfirm PiedonianSignatureManager.spec
if errorlevel 1 goto :error

echo.
echo Build complete:
echo   dist\PiedonianSignatureManager.exe
echo.
echo Run the EXE on Windows. It opens a local browser UI.
echo Signature data is saved beside the EXE in:
echo   data\civic_signatures.json
echo.
exit /b 0

:error
echo BUILD FAILED
exit /b 1
