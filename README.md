# GOV — Piedonian Woods

Formal civic documents for the **Piedonian Woods**, a private community instrument seated at:

**805 N 4th, Merkel, TX 79536, United States of America**

Prepared for civic record and professional presentment (including informational briefing to external observers such as the United Nations). These materials do **not** claim sovereign statehood or United Nations membership.

## Documents

| File | Purpose |
|------|---------|
| [`CONSTITUTION_OF_THE_PIEDONIAN_WOODS.md`](./CONSTITUTION_OF_THE_PIEDONIAN_WOODS.md) | Full organic constitution, governance, Bill of Rights, and Signature Annex |
| [`SIGNATURE_PACKET.md`](./SIGNATURE_PACKET.md) | Printable founding / citizen-roll / witness / notary packet |
| [`PIEDONIAN_COMBINED_CIVIC_DOCUMENT.md`](./PIEDONIAN_COMBINED_CIVIC_DOCUMENT.md) | **Combined** Constitution + Signature Packet (single application document) |
| [`PiedonianCivicDocument/`](./PiedonianCivicDocument/) | **Windows 11 standalone EXE** (C# + HTML/CSS/JavaScript) — combined document + electronic signatures |
| [`signature_tool/`](./signature_tool/) | Legacy Python Signature Manager + EXE build |

## Standalone Windows 11 application (primary)

Combines the Constitution and Signature Packet into **one** electronically signable desktop app:

| Part | Rule in the app |
|:--|:--|
| **Combined Document** | Full text viewer (Constitution + Packet) · print / Save PDF |
| **A — Founding Signature** | **William Franklin Hoisington IV** only · typed name must match exactly · **locks permanently** after one use |
| **B — Citizen Signature Roll** | **Multi-add** · new numbered entry for every new citizen · **signee must date** the signature |
| **C–F** | Optional Co-President, Justice, witness, and notary acknowledgments · **date required** |

**Workflow:** open app → sign → **date the signature** → save → keep record / export.

**Stack:** C# (.NET 8) backend · HTML + CSS + JavaScript UI

### Download the EXE package

The Windows binary is built by GitHub Actions (not committed to git). After a green run of **Build Civic Document EXE**:

1. GitHub → **Actions** → **Build Civic Document EXE** → latest successful run
2. Download artifact **`PiedonianCivicDocument-windows-x64`** (ZIP)
3. Unzip on Windows 11 and double-click `PiedonianCivicDocument.exe`

Keep `wwwroot\` and `Content\` next to the EXE (included in the ZIP).  
Records save to `data\civic_signatures.json` beside the EXE.

**Run from source:**

```bash
cd PiedonianCivicDocument
dotnet run
```

**Build Windows package** (on Windows, Linux, or via GitHub Actions):

```bat
cd PiedonianCivicDocument
build_windows.bat
```

Output:

- `PiedonianCivicDocument\dist\PiedonianCivicDocument.exe`
- `PiedonianCivicDocument\package\PiedonianCivicDocument-windows-x64.zip`

See [`PiedonianCivicDocument/README.md`](./PiedonianCivicDocument/README.md) for full usage.

## Legacy Python Signature Manager

Still available under [`signature_tool/`](./signature_tool/) if needed:

```bash
python signature_tool/signature_manager.py
```

## Constitution highlights

- Accepts the **United States Constitution** and all US laws
- Accepts the **Texas Constitution** and Texas laws
- Accepts **Merkel, Texas** city ordinances
- Continues **Taylor County** property taxes while Taylor County collects for the seat address
- **Dual Co-Presidents** through **15 November 2027**:
  - William Franklin Hoisington IV
  - Tommy James Lindsey
- **Laws** during Co-Presidency: agreement of both Co-Presidents
- **Amendments**: unanimous vote
- **First election:** 1 November 2027 (five candidates → one President and three Senators); then every two years
- **Only citizens** may run; citizenship granted by a President / Co-President
- Elections by **third-party polling** agreed by all candidates; citizens vote **top two**
- **50/50** President–Senate powers; deadlocks resolved with a three-Senator process and tie-break by **Ramon Santiago IV**, **Justice of Democracy**
- Default if insufficient votes or unresolved tie: Presidency to William Franklin Hoisington IV; Senate to Tommy James Lindsey plus two candidates of his choice
- Candidates need **only one vote** to secure a position (subject to ranking and default rules)
- Internal currency: **Pie Fillings** · Bank: **The First Discordian Bank of Pie**
- **Bill of Rights (2):**
  1. Guest room for **48 hours**, then **30-day** minimum exit before the next stay
  2. **Right to vote** in any election for Piedonian Woods’ Officials

## Signature system

| Class | Rule |
|:--|:--|
| **Founding Signature** | William Franklin Hoisington IV on **10 August 2026** — **once only, never again** |
| **Citizen Signature Roll** | New signature **every time** a new citizen is enrolled — expandable without limit |

## How to execute

1. Download/unzip the Windows package (see above) or run `dotnet run` in `PiedonianCivicDocument/`
2. Open `PiedonianCivicDocument.exe` — browser UI opens locally
3. Review the **Combined Document** tab (Constitution + Signature Packet)
4. Affix the **Founding Signature** (Part A) **once**, then the app closes that block permanently
5. Optionally record Co-President, Justice, witness, and notary acknowledgments (**each requires a signature date**)
6. For each new citizen, add a **Citizen Signature Roll** entry (Part B) with **name, signature, and signed date**
7. Records auto-save to `data/civic_signatures.json` beside the EXE; export JSON / Markdown anytime
8. File wet-ink originals with the civic record at the Seat when required

## Legal note

These materials are a private micronational/community instrument. They do **not** supersede United States, Texas, local, or tax authority law; do not change real-property title; and do not create a sovereign state under international law.
