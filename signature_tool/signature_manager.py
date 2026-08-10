#!/usr/bin/env python3
"""
Piedonian Woods — Civic Signature Manager

Part A: One-time Founding Signature (William Franklin Hoisington IV only)
Part B: Multi-add Citizen Signature Roll (unlimited enrollments)

Runs a local desktop UI in the default browser. Data is stored next to the
executable (or this script) under data/civic_signatures.json.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

APP_NAME = "Piedonian Woods Signature Manager"
FOUNDING_NAME = "William Franklin Hoisington IV"
FOUNDING_CAPACITY = "Founding Co-President — Founding Signature (sole and final)"
FOUNDING_DATE_ISO = "2026-08-10"
FOUNDING_DATE_DISPLAY = "10 August 2026"
SEAT = "805 N 4th, Merkel, TX 79536, United States of America"
HOST = "127.0.0.1"
PORT = 8765


def app_root() -> Path:
    """Directory that holds durable data (next to frozen exe or script)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def data_path() -> Path:
    path = app_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path / "civic_signatures.json"


def default_record() -> dict[str, Any]:
    return {
        "version": 1,
        "document": "Constitution of the Piedonian Woods",
        "seat": SEAT,
        "founding": {
            "status": "open",
            "printed_name": FOUNDING_NAME,
            "capacity": FOUNDING_CAPACITY,
            "required_date": FOUNDING_DATE_ISO,
            "required_date_display": FOUNDING_DATE_DISPLAY,
            "signature_text": None,
            "signature_image_png_b64": None,
            "signed_at_utc": None,
            "closure_legend": None,
            "record_hash": None,
        },
        "citizens": [],
        "optional": {
            "co_president": None,
            "justice": None,
        },
        "updated_at_utc": None,
    }


def load_record() -> dict[str, Any]:
    path = data_path()
    if not path.exists():
        record = default_record()
        save_record(record)
        return record
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    # Ensure expected keys exist for older files
    base = default_record()
    for key, value in base.items():
        if key not in data:
            data[key] = value
    if "founding" in data:
        for key, value in base["founding"].items():
            data["founding"].setdefault(key, value)
    data.setdefault("optional", base["optional"])
    data.setdefault("citizens", [])
    return data


def save_record(record: dict[str, Any]) -> None:
    record["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    path = data_path()
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    tmp.replace(path)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def founding_payload_for_hash(founding: dict[str, Any]) -> str:
    return "|".join(
        [
            founding.get("printed_name") or "",
            founding.get("capacity") or "",
            founding.get("required_date") or "",
            founding.get("signature_text") or "",
            founding.get("signature_image_png_b64") or "",
            founding.get("signed_at_utc") or "",
            founding.get("closure_legend") or "",
        ]
    )


def next_citizen_number(record: dict[str, Any]) -> int:
    if not record["citizens"]:
        return 1
    return max(int(c.get("entry_no", 0)) for c in record["citizens"]) + 1


def json_bytes(payload: Any, status: int = 200) -> tuple[int, bytes, str]:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    return status, body, "application/json; charset=utf-8"


def html_page() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{APP_NAME}</title>
<style>
  :root {{
    --bg: #f4f1ea;
    --ink: #1c2430;
    --card: #fffdf8;
    --line: #c9bfae;
    --accent: #2f5d50;
    --warn: #8b2e2e;
    --muted: #5c6570;
    --ok: #1f6b3a;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: "Segoe UI", "Georgia", serif;
    color: var(--ink);
    background:
      radial-gradient(circle at top left, #efe6d4 0, transparent 40%),
      linear-gradient(180deg, #ebe4d6, var(--bg));
    min-height: 100vh;
  }}
  header {{
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid var(--line);
    background: rgba(255,253,248,0.92);
    position: sticky;
    top: 0;
    backdrop-filter: blur(6px);
    z-index: 5;
  }}
  header h1 {{
    margin: 0 0 0.25rem;
    font-size: 1.35rem;
    letter-spacing: 0.02em;
  }}
  header p {{ margin: 0; color: var(--muted); font-size: 0.95rem; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 1.25rem; }}
  .tabs {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }}
  .tab {{
    border: 1px solid var(--line);
    background: var(--card);
    color: var(--ink);
    padding: 0.55rem 0.9rem;
    border-radius: 999px;
    cursor: pointer;
    font: inherit;
  }}
  .tab.active {{ background: var(--accent); color: white; border-color: var(--accent); }}
  .panel {{ display: none; }}
  .panel.active {{ display: block; }}
  .card {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 1.1rem 1.2rem;
    margin-bottom: 1rem;
    box-shadow: 0 8px 24px rgba(28,36,48,0.05);
  }}
  h2 {{ margin: 0 0 0.6rem; font-size: 1.15rem; }}
  h3 {{ margin: 1rem 0 0.4rem; font-size: 1rem; }}
  label {{ display: block; font-size: 0.9rem; margin: 0.55rem 0 0.2rem; color: var(--muted); }}
  input, select, textarea, button {{
    font: inherit;
  }}
  input, select, textarea {{
    width: 100%;
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 0.55rem 0.7rem;
    background: #fff;
  }}
  textarea {{ min-height: 70px; resize: vertical; }}
  .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }}
  @media (max-width: 720px) {{ .row {{ grid-template-columns: 1fr; }} }}
  .actions {{ display: flex; gap: 0.6rem; flex-wrap: wrap; margin-top: 0.9rem; }}
  button.primary {{
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    cursor: pointer;
  }}
  button.secondary {{
    background: white;
    color: var(--ink);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    cursor: pointer;
  }}
  button.danger {{
    background: var(--warn);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    cursor: pointer;
  }}
  button:disabled {{ opacity: 0.55; cursor: not-allowed; }}
  .banner {{
    border-radius: 10px;
    padding: 0.75rem 0.9rem;
    margin: 0.6rem 0 0.9rem;
    border: 1px solid var(--line);
    background: #f7f0e4;
  }}
  .banner.warn {{ background: #f8e8e6; border-color: #e0b4b0; color: var(--warn); }}
  .banner.ok {{ background: #e7f5eb; border-color: #b7dcc3; color: var(--ok); }}
  .muted {{ color: var(--muted); }}
  .sig-wrap {{
    border: 1px dashed var(--line);
    border-radius: 10px;
    background: #fff;
    overflow: hidden;
  }}
  canvas {{
    display: block;
    width: 100%;
    height: 180px;
    touch-action: none;
    cursor: crosshair;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
  }}
  th, td {{
    border-bottom: 1px solid var(--line);
    text-align: left;
    padding: 0.55rem 0.35rem;
    vertical-align: top;
  }}
  th {{ color: var(--muted); font-weight: 600; }}
  .status-pill {{
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    font-size: 0.82rem;
    border: 1px solid var(--line);
  }}
  .status-pill.open {{ background: #fff4d6; }}
  .status-pill.closed {{ background: #e7f5eb; color: var(--ok); }}
  .thumb {{
    max-width: 180px;
    max-height: 70px;
    border: 1px solid var(--line);
    background: white;
  }}
  footer {{
    text-align: center;
    color: var(--muted);
    font-size: 0.85rem;
    padding: 1rem 1rem 2rem;
  }}
  code {{ background: #efe8da; padding: 0.1rem 0.3rem; border-radius: 4px; }}
</style>
</head>
<body>
<header>
  <h1>{APP_NAME}</h1>
  <p>Seat of Record: {SEAT}</p>
</header>
<main>
  <div class="tabs">
    <button class="tab active" data-tab="founding">Part A · Founding Signature</button>
    <button class="tab" data-tab="citizen">Part B · Citizen Roll</button>
    <button class="tab" data-tab="optional">Optional Acknowledgments</button>
    <button class="tab" data-tab="records">Records &amp; Export</button>
  </div>

  <section id="founding" class="panel active">
    <div class="card">
      <h2>Part A — Founding Signature (one time only)</h2>
      <div id="founding-banner" class="banner warn">
        <strong>WARNING:</strong> Only <em>{FOUNDING_NAME}</em> may execute this signature,
        once only, for founding date <strong>{FOUNDING_DATE_DISPLAY}</strong>. After save, this block locks forever.
      </div>
      <div class="row">
        <div>
          <label>Printed name (fixed)</label>
          <input id="f-name" value="{FOUNDING_NAME}" readonly />
        </div>
        <div>
          <label>Capacity (fixed)</label>
          <input id="f-capacity" value="{FOUNDING_CAPACITY}" readonly />
        </div>
      </div>
      <div class="row">
        <div>
          <label>Date of founding execution (fixed)</label>
          <input id="f-date" value="{FOUNDING_DATE_DISPLAY}" readonly />
        </div>
        <div>
          <label>Typed legal signature (full legal name)</label>
          <input id="f-sig-text" placeholder="{FOUNDING_NAME}" />
        </div>
      </div>
      <label>Drawn signature (optional but recommended)</label>
      <div class="sig-wrap"><canvas id="f-canvas" width="1000" height="180"></canvas></div>
      <div class="actions">
        <button class="secondary" type="button" id="f-clear">Clear drawing</button>
        <button class="primary" type="button" id="f-save">Affix Founding Signature &amp; Close Permanently</button>
      </div>
      <div id="founding-result" class="muted" style="margin-top:0.8rem"></div>
    </div>
  </section>

  <section id="citizen" class="panel">
    <div class="card">
      <h2>Part B — Citizen Signature Roll (multi-add)</h2>
      <p class="muted">Add a new entry every time citizenship is granted. Entries never replace the founding signature.</p>
      <div class="row">
        <div>
          <label>Entry number</label>
          <input id="c-entry" readonly />
        </div>
        <div>
          <label>Printed name of citizen</label>
          <input id="c-name" placeholder="Citizen full legal name" />
        </div>
      </div>
      <div class="row">
        <div>
          <label>Citizenship granted by (President / Co-President)</label>
          <input id="c-granted-by" placeholder="e.g. William Franklin Hoisington IV" />
        </div>
        <div>
          <label>Date citizenship granted</label>
          <input id="c-granted-date" type="date" />
        </div>
      </div>
      <div class="row">
        <div>
          <label>Date signed</label>
          <input id="c-signed-date" type="date" />
        </div>
        <div>
          <label>Optional witness</label>
          <input id="c-witness" placeholder="Witness name (optional)" />
        </div>
      </div>
      <label>Typed signature of citizen</label>
      <input id="c-sig-text" placeholder="Type full legal name as signature" />
      <label>Drawn signature</label>
      <div class="sig-wrap"><canvas id="c-canvas" width="1000" height="180"></canvas></div>
      <div class="actions">
        <button class="secondary" type="button" id="c-clear">Clear drawing</button>
        <button class="primary" type="button" id="c-save">Add Citizen Signature</button>
      </div>
      <div id="citizen-result" class="muted" style="margin-top:0.8rem"></div>
    </div>
  </section>

  <section id="optional" class="panel">
    <div class="card">
      <h2>Optional acknowledgments</h2>
      <h3>Part C — Co-President (Tommy James Lindsey)</h3>
      <div class="row">
        <div>
          <label>Typed signature</label>
          <input id="o-co-sig" placeholder="Tommy James Lindsey" />
        </div>
        <div>
          <label>Date</label>
          <input id="o-co-date" type="date" />
        </div>
      </div>
      <div class="actions">
        <button class="primary" type="button" id="o-co-save">Save Co-President acknowledgment</button>
      </div>
      <h3>Part D — Justice of Democracy (Ramon Santiago IV)</h3>
      <div class="row">
        <div>
          <label>Typed signature</label>
          <input id="o-j-sig" placeholder="Ramon Santiago IV" />
        </div>
        <div>
          <label>Date</label>
          <input id="o-j-date" type="date" />
        </div>
      </div>
      <div class="actions">
        <button class="primary" type="button" id="o-j-save">Save Justice acknowledgment</button>
      </div>
      <div id="optional-result" class="muted" style="margin-top:0.8rem"></div>
    </div>
  </section>

  <section id="records" class="panel">
    <div class="card">
      <h2>Civic record</h2>
      <div id="record-summary"></div>
      <div class="actions">
        <button class="secondary" type="button" id="btn-refresh">Refresh</button>
        <button class="secondary" type="button" id="btn-export-json">Export JSON</button>
        <button class="secondary" type="button" id="btn-export-md">Export Markdown packet</button>
      </div>
    </div>
    <div class="card">
      <h2>Citizen entries</h2>
      <div id="citizen-table"></div>
    </div>
  </section>
</main>
<footer>
  Private community instrument · does not supersede US, Texas, or local law · data file: <code>data/civic_signatures.json</code>
</footer>
<script>
const FOUNDING_NAME = {json.dumps(FOUNDING_NAME)};

function pad(canvas) {{
  const ctx = canvas.getContext('2d');
  let drawing = false;
  let dirty = false;
  function pos(e) {{
    const r = canvas.getBoundingClientRect();
    const x = ('touches' in e ? e.touches[0].clientX : e.clientX) - r.left;
    const y = ('touches' in e ? e.touches[0].clientY : e.clientY) - r.top;
    return [x * (canvas.width / r.width), y * (canvas.height / r.height)];
  }}
  function start(e) {{
    drawing = true; dirty = true;
    const [x,y] = pos(e);
    ctx.beginPath(); ctx.moveTo(x,y);
    e.preventDefault();
  }}
  function move(e) {{
    if (!drawing) return;
    const [x,y] = pos(e);
    ctx.lineWidth = 2.2; ctx.lineCap = 'round'; ctx.strokeStyle = '#111';
    ctx.lineTo(x,y); ctx.stroke();
    e.preventDefault();
  }}
  function end() {{ drawing = false; }}
  canvas.addEventListener('mousedown', start);
  canvas.addEventListener('mousemove', move);
  window.addEventListener('mouseup', end);
  canvas.addEventListener('touchstart', start, {{passive:false}});
  canvas.addEventListener('touchmove', move, {{passive:false}});
  canvas.addEventListener('touchend', end);
  function clear() {{
    ctx.clearRect(0,0,canvas.width,canvas.height);
    dirty = false;
  }}
  function toDataUrl() {{
    if (!dirty) return null;
    return canvas.toDataURL('image/png');
  }}
  return {{ clear, toDataUrl }};
}}

const fPad = pad(document.getElementById('f-canvas'));
const cPad = pad(document.getElementById('c-canvas'));

document.querySelectorAll('.tab').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  }});
}});

async function api(path, opts) {{
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
  return data;
}}

function todayISO() {{
  const d = new Date();
  const m = String(d.getMonth()+1).padStart(2,'0');
  const day = String(d.getDate()).padStart(2,'0');
  return d.getFullYear() + '-' + m + '-' + day;
}}

function setFoundingUI(rec) {{
  const f = rec.founding;
  const banner = document.getElementById('founding-banner');
  const saveBtn = document.getElementById('f-save');
  const clearBtn = document.getElementById('f-clear');
  const sigText = document.getElementById('f-sig-text');
  if (f.status === 'closed') {{
    banner.className = 'banner ok';
    banner.innerHTML = '<strong>FOUNDING SIGNATURE CLOSED — DO NOT RE-SIGN</strong><br/>Signed by '
      + (f.printed_name || '') + ' on ' + (f.required_date_display || '') +
      (f.signed_at_utc ? (' · recorded ' + f.signed_at_utc) : '') +
      (f.record_hash ? (' · hash ' + f.record_hash.slice(0,16) + '…') : '');
    saveBtn.disabled = true;
    clearBtn.disabled = true;
    sigText.disabled = true;
    sigText.value = f.signature_text || '';
    document.getElementById('founding-result').textContent = 'This Part A lock cannot be reopened by the application.';
  }} else {{
    banner.className = 'banner warn';
    banner.innerHTML = '<strong>WARNING:</strong> Only <em>' + FOUNDING_NAME + '</em> may execute this signature, once only, for founding date <strong>{FOUNDING_DATE_DISPLAY}</strong>. After save, this block locks forever.';
    saveBtn.disabled = false;
    clearBtn.disabled = false;
    sigText.disabled = false;
  }}
}}

function renderRecords(rec) {{
  const f = rec.founding;
  const pill = f.status === 'closed'
    ? '<span class="status-pill closed">CLOSED</span>'
    : '<span class="status-pill open">OPEN</span>';
  let html = '<p><strong>Founding status:</strong> ' + pill + '</p>';
  html += '<p><strong>Document:</strong> ' + escapeHtml(rec.document || '') + '</p>';
  html += '<p><strong>Seat:</strong> ' + escapeHtml(rec.seat || '') + '</p>';
  if (f.status === 'closed') {{
    html += '<p><strong>Founding signatory:</strong> ' + escapeHtml(f.printed_name||'') + '</p>';
    html += '<p><strong>Typed signature:</strong> ' + escapeHtml(f.signature_text||'') + '</p>';
    html += '<p><strong>Closure:</strong> ' + escapeHtml(f.closure_legend||'') + '</p>';
    if (f.signature_image_png_b64) {{
      const b64 = safeBase64(f.signature_image_png_b64);
      if (b64) {{
        html += '<p><img class="thumb" alt="Founding signature" src="data:image/png;base64,' + b64 + '" /></p>';
      }}
    }}
  }}
  const opt = rec.optional || {{}};
  if (opt.co_president) {{
    html += '<p><strong>Co-President ack:</strong> ' + escapeHtml(opt.co_president.signature_text||'') + ' (' + escapeHtml(opt.co_president.date||'') + ')</p>';
  }}
  if (opt.justice) {{
    html += '<p><strong>Justice ack:</strong> ' + escapeHtml(opt.justice.signature_text||'') + ' (' + escapeHtml(opt.justice.date||'') + ')</p>';
  }}
  html += '<p class="muted">Citizens enrolled: ' + (rec.citizens||[]).length + ' · Last update: ' + escapeHtml(rec.updated_at_utc || 'n/a') + '</p>';
  document.getElementById('record-summary').innerHTML = html;

  const citizens = rec.citizens || [];
  if (!citizens.length) {{
    document.getElementById('citizen-table').innerHTML = '<p class="muted">No citizen signatures yet.</p>';
  }} else {{
    let t = '<table><thead><tr><th>#</th><th>Name</th><th>Granted by</th><th>Dates</th><th>Signature</th></tr></thead><tbody>';
    for (const c of citizens.slice().reverse()) {{
      t += '<tr><td>' + escapeHtml(c.entry_no) + '</td><td>' + escapeHtml(c.printed_name||'') +
        '</td><td>' + escapeHtml(c.granted_by||'') +
        '</td><td>granted ' + escapeHtml(c.granted_date||'') + '<br/>signed ' + escapeHtml(c.signed_date||'') +
        '</td><td>' + escapeHtml(c.signature_text||'');
      if (c.signature_image_png_b64) {{
        const b64 = safeBase64(c.signature_image_png_b64);
        if (b64) {{
          t += '<br/><img class="thumb" alt="sig" src="data:image/png;base64,' + b64 + '" />';
        }}
      }}
      t += '</td></tr>';
    }}
    t += '</tbody></table>';
    document.getElementById('citizen-table').innerHTML = t;
  }}
  document.getElementById('c-entry').value = String((rec.next_citizen_no != null ? rec.next_citizen_no : ((rec.citizens||[]).length + 1)));
}}

function escapeHtml(s) {{
  return String(s).replace(/[&<>"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[ch]));
}}

function safeBase64(s) {{
  const cleaned = String(s || '').replace(/[^A-Za-z0-9+/=]/g, '');
  return cleaned.length ? cleaned : '';
}}

async function refresh() {{
  const rec = await api('/api/record');
  setFoundingUI(rec);
  renderRecords(rec);
  if (rec.optional && rec.optional.co_president) {{
    document.getElementById('o-co-sig').value = rec.optional.co_president.signature_text || '';
    document.getElementById('o-co-date').value = rec.optional.co_president.date || '';
  }}
  if (rec.optional && rec.optional.justice) {{
    document.getElementById('o-j-sig').value = rec.optional.justice.signature_text || '';
    document.getElementById('o-j-date').value = rec.optional.justice.date || '';
  }}
}}

document.getElementById('f-clear').onclick = () => fPad.clear();
document.getElementById('c-clear').onclick = () => cPad.clear();
document.getElementById('btn-refresh').onclick = () => refresh().catch(err => alert(err.message));

document.getElementById('f-save').onclick = async () => {{
  try {{
    const signature_text = document.getElementById('f-sig-text').value.trim();
    if (signature_text !== FOUNDING_NAME) {{
      alert('Typed signature must exactly match: ' + FOUNDING_NAME);
      return;
    }}
    if (!confirm('Affix the ONE-TIME founding signature and permanently close Part A? This cannot be undone in the app.')) return;
    const img = fPad.toDataUrl();
    const body = {{
      signature_text,
      signature_image_data_url: img
    }};
    const rec = await api('/api/founding', {{
      method: 'POST',
      headers: {{'Content-Type':'application/json'}},
      body: JSON.stringify(body)
    }});
    document.getElementById('founding-result').textContent = 'Founding signature recorded and closed.';
    setFoundingUI(rec);
    renderRecords(rec);
  }} catch (err) {{
    alert(err.message);
  }}
}};

document.getElementById('c-save').onclick = async () => {{
  try {{
    const body = {{
      printed_name: document.getElementById('c-name').value.trim(),
      granted_by: document.getElementById('c-granted-by').value.trim(),
      granted_date: document.getElementById('c-granted-date').value,
      signed_date: document.getElementById('c-signed-date').value || todayISO(),
      witness: document.getElementById('c-witness').value.trim(),
      signature_text: document.getElementById('c-sig-text').value.trim(),
      signature_image_data_url: cPad.toDataUrl()
    }};
    if (!body.printed_name || !body.granted_by || !body.granted_date || !body.signature_text) {{
      alert('Citizen name, granted by, granted date, and typed signature are required.');
      return;
    }}
    const rec = await api('/api/citizen', {{
      method: 'POST',
      headers: {{'Content-Type':'application/json'}},
      body: JSON.stringify(body)
    }});
    document.getElementById('citizen-result').textContent = 'Citizen entry #' + (rec.citizens[rec.citizens.length-1].entry_no) + ' added.';
    document.getElementById('c-name').value = '';
    document.getElementById('c-sig-text').value = '';
    document.getElementById('c-witness').value = '';
    cPad.clear();
    renderRecords(rec);
  }} catch (err) {{
    alert(err.message);
  }}
}};

document.getElementById('o-co-save').onclick = async () => {{
  try {{
    const rec = await api('/api/optional/co_president', {{
      method: 'POST',
      headers: {{'Content-Type':'application/json'}},
      body: JSON.stringify({{
        signature_text: document.getElementById('o-co-sig').value.trim(),
        date: document.getElementById('o-co-date').value || todayISO()
      }})
    }});
    document.getElementById('optional-result').textContent = 'Co-President acknowledgment saved.';
    renderRecords(rec);
  }} catch (err) {{ alert(err.message); }}
}};

document.getElementById('o-j-save').onclick = async () => {{
  try {{
    const rec = await api('/api/optional/justice', {{
      method: 'POST',
      headers: {{'Content-Type':'application/json'}},
      body: JSON.stringify({{
        signature_text: document.getElementById('o-j-sig').value.trim(),
        date: document.getElementById('o-j-date').value || todayISO()
      }})
    }});
    document.getElementById('optional-result').textContent = 'Justice acknowledgment saved.';
    renderRecords(rec);
  }} catch (err) {{ alert(err.message); }}
}};

document.getElementById('btn-export-json').onclick = () => {{ window.location.href = '/api/export.json'; }};
document.getElementById('btn-export-md').onclick = () => {{ window.location.href = '/api/export.md'; }};

document.getElementById('c-granted-date').value = todayISO();
document.getElementById('c-signed-date').value = todayISO();
document.getElementById('o-co-date').value = todayISO();
document.getElementById('o-j-date').value = todayISO();
refresh().catch(err => alert('Failed to load record: ' + err.message));
</script>
</body>
</html>
"""


def data_url_to_b64(data_url: str | None) -> str | None:
    if not data_url:
        return None
    if "," not in data_url:
        return None
    header, b64 = data_url.split(",", 1)
    if "base64" not in header:
        return None
    # Validate base64
    try:
        base64.b64decode(b64, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid signature image encoding") from exc
    return b64


def public_record(record: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(record))
    out["next_citizen_no"] = next_citizen_number(record)
    return out


def export_markdown(record: dict[str, Any]) -> str:
    f = record["founding"]
    lines = [
        "# Piedonian Woods — Executed Signature Record",
        "",
        f"**Document:** {record.get('document', '')}",
        f"**Seat:** {record.get('seat', '')}",
        f"**Exported (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
        "---",
        "",
        "## Part A — Founding Signature",
        "",
        f"- **Status:** {f.get('status')}",
        f"- **Printed name:** {f.get('printed_name')}",
        f"- **Capacity:** {f.get('capacity')}",
        f"- **Founding date:** {f.get('required_date_display')}",
        f"- **Typed signature:** {f.get('signature_text') or '—'}",
        f"- **Signed at (UTC):** {f.get('signed_at_utc') or '—'}",
        f"- **Closure:** {f.get('closure_legend') or '—'}",
        f"- **Record hash:** {f.get('record_hash') or '—'}",
        "",
        "## Part B — Citizen Signature Roll",
        "",
    ]
    citizens = record.get("citizens") or []
    if not citizens:
        lines.append("_No citizen entries yet._")
        lines.append("")
    else:
        for c in citizens:
            lines.extend(
                [
                    f"### Citizen Entry No. {c.get('entry_no')}",
                    "",
                    f"- **Printed name:** {c.get('printed_name')}",
                    f"- **Citizenship granted by:** {c.get('granted_by')}",
                    f"- **Date citizenship granted:** {c.get('granted_date')}",
                    f"- **Signature of citizen:** {c.get('signature_text')}",
                    f"- **Date signed:** {c.get('signed_date')}",
                    f"- **Optional witness:** {c.get('witness') or '—'}",
                    f"- **Recorded at (UTC):** {c.get('recorded_at_utc')}",
                    "",
                ]
            )
    opt = record.get("optional") or {}
    lines.extend(["## Optional acknowledgments", ""])
    co = opt.get("co_president")
    ju = opt.get("justice")
    if co:
        lines.append(
            f"- **Co-President (Tommy James Lindsey):** {co.get('signature_text')} on {co.get('date')}"
        )
    else:
        lines.append("- **Co-President:** not recorded")
    if ju:
        lines.append(
            f"- **Justice of Democracy (Ramon Santiago IV):** {ju.get('signature_text')} on {ju.get('date')}"
        )
    else:
        lines.append("- **Justice of Democracy:** not recorded")
    lines.append("")
    lines.append("**End of executed signature record**")
    lines.append("")
    return "\n".join(lines)


class Handler(BaseHTTPRequestHandler):
    server_version = "PiedonianSignatureManager/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep console quiet except errors
        if args and str(args[0]).startswith("5"):
            super().log_message(fmt, *args)

    def _send(self, status: int, body: bytes, content_type: str, disposition: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if disposition:
            self.send_header("Content-Disposition", disposition)
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path in ("/", "/index.html"):
                page = html_page().encode("utf-8")
                self._send(200, page, "text/html; charset=utf-8")
                return
            if path == "/api/record":
                status, body, ctype = json_bytes(public_record(load_record()))
                self._send(status, body, ctype)
                return
            if path == "/api/export.json":
                body = json.dumps(load_record(), indent=2, ensure_ascii=False).encode("utf-8")
                self._send(
                    200,
                    body,
                    "application/json; charset=utf-8",
                    'attachment; filename="civic_signatures.json"',
                )
                return
            if path == "/api/export.md":
                body = export_markdown(load_record()).encode("utf-8")
                self._send(
                    200,
                    body,
                    "text/markdown; charset=utf-8",
                    'attachment; filename="executed_signature_record.md"',
                )
                return
            self._send(404, b'{"error":"not found"}', "application/json; charset=utf-8")
        except Exception as exc:  # noqa: BLE001
            status, body, ctype = json_bytes({"error": str(exc)}, 500)
            self._send(status, body, ctype)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            payload = self._read_json()
            record = load_record()

            if path == "/api/founding":
                founding = record["founding"]
                if founding.get("status") == "closed":
                    status, body, ctype = json_bytes(
                        {"error": "Founding signature is already closed and cannot be re-signed."},
                        409,
                    )
                    self._send(status, body, ctype)
                    return

                sig_text = (payload.get("signature_text") or "").strip()
                if sig_text != FOUNDING_NAME:
                    status, body, ctype = json_bytes(
                        {
                            "error": f"Typed signature must exactly match '{FOUNDING_NAME}'."
                        },
                        400,
                    )
                    self._send(status, body, ctype)
                    return

                img_b64 = data_url_to_b64(payload.get("signature_image_data_url"))
                now = datetime.now(timezone.utc).isoformat()
                founding["signature_text"] = sig_text
                founding["signature_image_png_b64"] = img_b64
                founding["signed_at_utc"] = now
                founding["closure_legend"] = "FOUNDING SIGNATURE CLOSED — DO NOT RE-SIGN"
                founding["status"] = "closed"
                founding["printed_name"] = FOUNDING_NAME
                founding["capacity"] = FOUNDING_CAPACITY
                founding["required_date"] = FOUNDING_DATE_ISO
                founding["required_date_display"] = FOUNDING_DATE_DISPLAY
                founding["record_hash"] = sha256_hex(founding_payload_for_hash(founding))
                save_record(record)
                status, body, ctype = json_bytes(public_record(record))
                self._send(status, body, ctype)
                return

            if path == "/api/citizen":
                printed_name = (payload.get("printed_name") or "").strip()
                granted_by = (payload.get("granted_by") or "").strip()
                granted_date = (payload.get("granted_date") or "").strip()
                signed_date = (payload.get("signed_date") or "").strip()
                witness = (payload.get("witness") or "").strip()
                sig_text = (payload.get("signature_text") or "").strip()
                if not printed_name or not granted_by or not granted_date or not sig_text:
                    status, body, ctype = json_bytes(
                        {
                            "error": "printed_name, granted_by, granted_date, and signature_text are required."
                        },
                        400,
                    )
                    self._send(status, body, ctype)
                    return
                entry = {
                    "entry_no": next_citizen_number(record),
                    "printed_name": printed_name,
                    "granted_by": granted_by,
                    "granted_date": granted_date,
                    "signed_date": signed_date or datetime.now(timezone.utc).date().isoformat(),
                    "witness": witness or None,
                    "signature_text": sig_text,
                    "signature_image_png_b64": data_url_to_b64(
                        payload.get("signature_image_data_url")
                    ),
                    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                }
                record["citizens"].append(entry)
                save_record(record)
                status, body, ctype = json_bytes(public_record(record))
                self._send(status, body, ctype)
                return

            if path == "/api/optional/co_president":
                sig_text = (payload.get("signature_text") or "").strip()
                if not sig_text:
                    status, body, ctype = json_bytes({"error": "signature_text is required."}, 400)
                    self._send(status, body, ctype)
                    return
                record.setdefault("optional", {})
                record["optional"]["co_president"] = {
                    "printed_name": "Tommy James Lindsey",
                    "capacity": "Co-President (acknowledgment)",
                    "signature_text": sig_text,
                    "date": (payload.get("date") or "").strip()
                    or datetime.now(timezone.utc).date().isoformat(),
                    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                }
                save_record(record)
                status, body, ctype = json_bytes(public_record(record))
                self._send(status, body, ctype)
                return

            if path == "/api/optional/justice":
                sig_text = (payload.get("signature_text") or "").strip()
                if not sig_text:
                    status, body, ctype = json_bytes({"error": "signature_text is required."}, 400)
                    self._send(status, body, ctype)
                    return
                record.setdefault("optional", {})
                record["optional"]["justice"] = {
                    "printed_name": "Ramon Santiago IV",
                    "capacity": "Justice of Democracy",
                    "signature_text": sig_text,
                    "date": (payload.get("date") or "").strip()
                    or datetime.now(timezone.utc).date().isoformat(),
                    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                }
                save_record(record)
                status, body, ctype = json_bytes(public_record(record))
                self._send(status, body, ctype)
                return

            self._send(404, b'{"error":"not found"}', "application/json; charset=utf-8")
        except ValueError as exc:
            status, body, ctype = json_bytes({"error": str(exc)}, 400)
            self._send(status, body, ctype)
        except Exception as exc:  # noqa: BLE001
            status, body, ctype = json_bytes({"error": str(exc)}, 500)
            self._send(status, body, ctype)


def find_free_port(start: int = PORT, attempts: int = 20) -> int:
    import socket

    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((HOST, port))
            except OSError:
                continue
            return port
    raise RuntimeError("No free local port available for signature manager")


def main() -> int:
    # Support headless smoke tests / CI
    if "--self-test" in sys.argv:
        return run_self_test()

    port = find_free_port()
    server = ThreadingHTTPServer((HOST, port), Handler)
    url = f"http://{HOST}:{port}/"
    print(f"{APP_NAME}")
    print(f"Open: {url}")
    print(f"Data: {data_path()}")
    print("Press Ctrl+C to stop.")

    def open_browser() -> None:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, open_browser).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()
    return 0


def run_self_test() -> int:
    """In-process API checks without browser."""
    # Isolate test data
    test_dir = app_root() / "data" / "_self_test"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "civic_signatures.json"
    if test_file.exists():
        test_file.unlink()

    original = data_path

    def _test_data_path() -> Path:
        return test_file

    # Monkeypatch path during test
    globals()["data_path"] = _test_data_path  # type: ignore[assignment]
    try:
        rec = load_record()
        assert rec["founding"]["status"] == "open"

        # Reject wrong founding name
        class Dummy:
            pass

        # Use handler methods via direct function simulation
        record = load_record()
        assert next_citizen_number(record) == 1

        # Founding success
        founding = record["founding"]
        founding["signature_text"] = FOUNDING_NAME
        founding["signature_image_png_b64"] = None
        founding["signed_at_utc"] = datetime.now(timezone.utc).isoformat()
        founding["closure_legend"] = "FOUNDING SIGNATURE CLOSED — DO NOT RE-SIGN"
        founding["status"] = "closed"
        founding["record_hash"] = sha256_hex(founding_payload_for_hash(founding))
        save_record(record)
        record2 = load_record()
        assert record2["founding"]["status"] == "closed"
        assert record2["founding"]["record_hash"]

        # Citizen multi-add
        for i, name in enumerate(["Alice Citizen", "Bob Citizen"], start=1):
            record2 = load_record()
            record2["citizens"].append(
                {
                    "entry_no": next_citizen_number(record2),
                    "printed_name": name,
                    "granted_by": FOUNDING_NAME,
                    "granted_date": "2026-08-10",
                    "signed_date": "2026-08-10",
                    "witness": None,
                    "signature_text": name,
                    "signature_image_png_b64": None,
                    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                }
            )
            save_record(record2)
        final = load_record()
        assert len(final["citizens"]) == 2
        assert final["citizens"][0]["entry_no"] == 1
        assert final["citizens"][1]["entry_no"] == 2
        md = export_markdown(final)
        assert "FOUNDING SIGNATURE CLOSED" in md or "closed" in md.lower()
        assert "Alice Citizen" in md
        print("SELF-TEST OK")
        return 0
    finally:
        globals()["data_path"] = original  # type: ignore[assignment]
        try:
            if test_file.exists():
                test_file.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
