# Piedonian Woods — Combined Civic Document (Windows 11 package)

Standalone **C#** application with **HTML / CSS / JavaScript** UI that combines:

1. `CONSTITUTION_OF_THE_PIEDONIAN_WOODS.md`
2. `SIGNATURE_PACKET.md`

into one electronically signable civic instrument for Windows 11.

| Part | Behavior |
|:--|:--|
| **Combined Document** | Full Constitution + Signature Packet in one viewer (print / Save PDF) |
| **A — Founding Signature** | William Franklin Hoisington IV only · locks permanently after one use |
| **B — Citizen Signature Roll** | Multi-add unlimited citizen enrollments · **signed date required** |
| **C–F** | Optional Co-President, Justice, witness, notary · **signature date required** |

## What you get

Open the app → someone **signs** → they **date** the signature → **save** → keep a permanent **record** (`data/civic_signatures.json`) and optional JSON/Markdown exports.

## Download the Windows package (EXE)

The EXE is **not** stored in git (it is large and rebuilt by CI). Get it from GitHub Actions:

1. Open the repo on GitHub → **Actions**
2. Workflow **Build Civic Document EXE**
3. Open the latest green run → **Artifacts**
4. Download **`PiedonianCivicDocument-windows-x64`** (ZIP)
5. Unzip on Windows 11
6. Double-click **`PiedonianCivicDocument.exe`**

Keep these beside the EXE (they are inside the ZIP):

```text
PiedonianCivicDocument.exe
wwwroot\
Content\
data\          (created automatically for signature records)
```

## Build the package yourself

Requires [.NET 8 SDK](https://dotnet.microsoft.com/download).

On Windows:

```bat
cd PiedonianCivicDocument
build_windows.bat
```

On Linux/macOS (cross-compiles the Windows package):

```bash
cd PiedonianCivicDocument
./build_windows.sh
```

Output:

```text
dist/PiedonianCivicDocument.exe
package/PiedonianCivicDocument-windows-x64.zip
```

## Run from source

```bash
cd PiedonianCivicDocument
dotnet run
```

Self-test (no browser):

```bash
dotnet run -- --self-test
```

The app serves a local UI at `http://127.0.0.1:8777/` (or the next free port) and opens your browser.

## How to sign and keep a record

1. Open the app (EXE or `dotnet run`)
2. Review the **Combined Document** tab
3. Open the signature tab you need (Founding / Citizen / Optional)
4. Enter the typed signature (and drawing if desired)
5. **Enter the date the signee signs** (required for citizen and optional parts)
6. Click save — the app writes `data/civic_signatures.json` next to the EXE
7. Use **Records & Export** to download JSON or Markdown copies for filing

## Stack

- **C#** / .NET 8 — local HTTP host, record store, hash lock for founding signature
- **HTML + CSS + JavaScript** — document viewer, signature pads, tabs, export
- No external NuGet packages required at runtime

## Legal note

Private community instrument. Does **not** supersede United States, Texas, local, or tax law and does not create sovereign statehood.
