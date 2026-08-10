# Piedonian Woods — Signature Manager (EXE)

Desktop tool for the dual signature architecture in `SIGNATURE_PACKET.md`:

| Part | Purpose | App behavior |
|:--|:--|:--|
| **A** | **Founding Signature** — William Franklin Hoisington IV only | One-time lock. Typed name must match exactly. After save: **FOUNDING SIGNATURE CLOSED — DO NOT RE-SIGN** |
| **B** | **Citizen Signature Roll** | Multi-add. Every new citizen gets a new numbered entry |
| **C–D** | Optional Co-President / Justice acknowledgments | Editable acknowledgments |

## Quick start (from source)

```bash
python signature_manager.py
```

The app serves a local UI at `http://127.0.0.1:8765/` and opens your browser.

Self-test (no browser):

```bash
python signature_manager.py --self-test
```

## Build the Windows EXE

On a Windows machine with Python 3.10+ installed:

```bat
cd signature_tool
build_windows.bat
```

Output:

```text
signature_tool\dist\PiedonianSignatureManager.exe
```

Double-click the EXE. It opens the signature UI in your default browser and writes records next to the EXE:

```text
data\civic_signatures.json
```

### Linux/macOS host binary (optional)

```bash
cd signature_tool
chmod +x build_exe.sh
./build_exe.sh
```

This produces a native host binary under `dist/`, not a Windows `.exe`. Use `build_windows.bat` on Windows for the EXE.

## How to use

1. **Part A — Founding Signature**
   - Confirm fixed name: `William Franklin Hoisington IV`
   - Type that exact legal name as the signature
   - Optionally draw a wet-ink style signature on the pad
   - Click **Affix Founding Signature & Close Permanently**
   - Part A locks forever inside the data file
2. **Part B — Citizen Roll**
   - Enter citizen name, grantor, dates, typed signature
   - Optionally draw a signature
   - Click **Add Citizen Signature** as many times as needed
3. **Records & Export**
   - Review the civic record
   - Export JSON or Markdown packet copies

## Data & legal notes

- Storage file: `signature_tool/data/civic_signatures.json` (or `data\` beside the EXE)
- Founding closure is enforced by the application once status is `closed`
- This tool supports the private community signature packet; it does **not** supersede United States, Texas, local, or tax law, and does not create sovereign statehood
- Keep wet-ink originals at the Seat of Record when formal filing is required
