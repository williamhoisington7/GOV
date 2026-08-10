# Piedonian Woods — Combined Civic Document (Windows 11 EXE)

Standalone **C#** application with **HTML / CSS / JavaScript** UI that combines:

1. `CONSTITUTION_OF_THE_PIEDONIAN_WOODS.md`
2. `SIGNATURE_PACKET.md`

into one electronically signable civic instrument for Windows 11.

| Part | Behavior |
|:--|:--|
| **Combined Document** | Full Constitution + Signature Packet in one viewer (print / Save PDF) |
| **A — Founding Signature** | William Franklin Hoisington IV only · locks permanently after one use |
| **B — Citizen Signature Roll** | Multi-add unlimited citizen enrollments |
| **C–F** | Optional Co-President, Justice, witness, notary acknowledgments |

## Run from source

Requires [.NET 8 SDK](https://dotnet.microsoft.com/download).

```bash
cd PiedonianCivicDocument
dotnet run
```

Self-test (no browser):

```bash
dotnet run -- --self-test
```

The app serves a local UI at `http://127.0.0.1:8777/` (or the next free port) and opens your browser.

## Build Windows 11 EXE

On Windows (PowerShell / cmd):

```bat
cd PiedonianCivicDocument
build_windows.bat
```

Or:

```bash
cd PiedonianCivicDocument
./build_windows.sh
```

Output (true single-file self-contained EXE — UI + Constitution + Signature Packet embedded):

```text
PiedonianCivicDocument/dist/PiedonianCivicDocument.exe
```

Double-click the EXE on Windows 11. No extra folders are required next to the EXE. Signature data is created beside the EXE on first run:

```text
data/civic_signatures.json
```

GitHub Actions workflow **Build Civic Document EXE** uploads that single EXE artifact on every change under `PiedonianCivicDocument/`.

## Stack

- **C#** / .NET 8 — local HTTP host, record store, hash lock for founding signature
- **HTML + CSS + JavaScript** — document viewer, signature pads, tabs, export (embedded in the EXE)
- Combined Constitution + Signature Packet markdown embedded in the EXE
- No external NuGet packages required at runtime

## Legal note

Private community instrument. Does **not** supersede United States, Texas, local, or tax law and does not create sovereign statehood.
