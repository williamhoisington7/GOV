/* Piedonian Woods — combined civic document UI (JavaScript) */
(function () {
  "use strict";

  let META = {
    foundingName: "William Franklin Hoisington IV",
    foundingCapacity: "Founding Co-President — Founding Signature (sole and final)",
    foundingDateDisplay: "10 August 2026",
    seat: "805 N 4th, Merkel, TX 79536, United States of America",
    app: "Piedonian Woods Civic Document"
  };

  function pad(canvas) {
    const ctx = canvas.getContext("2d");
    let drawing = false;
    let dirty = false;
    function pos(e) {
      const r = canvas.getBoundingClientRect();
      const x = ("touches" in e ? e.touches[0].clientX : e.clientX) - r.left;
      const y = ("touches" in e ? e.touches[0].clientY : e.clientY) - r.top;
      return [x * (canvas.width / r.width), y * (canvas.height / r.height)];
    }
    function start(e) {
      drawing = true;
      dirty = true;
      const [x, y] = pos(e);
      ctx.beginPath();
      ctx.moveTo(x, y);
      e.preventDefault();
    }
    function move(e) {
      if (!drawing) return;
      const [x, y] = pos(e);
      ctx.lineWidth = 2.2;
      ctx.lineCap = "round";
      ctx.strokeStyle = "#111";
      ctx.lineTo(x, y);
      ctx.stroke();
      e.preventDefault();
    }
    function end() {
      drawing = false;
    }
    canvas.addEventListener("mousedown", start);
    canvas.addEventListener("mousemove", move);
    window.addEventListener("mouseup", end);
    canvas.addEventListener("touchstart", start, { passive: false });
    canvas.addEventListener("touchmove", move, { passive: false });
    canvas.addEventListener("touchend", end);
    return {
      clear: function () {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        dirty = false;
      },
      toDataUrl: function () {
        if (!dirty) return null;
        return canvas.toDataURL("image/png");
      }
    };
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function safeBase64(s) {
    const cleaned = String(s || "").replace(/[^A-Za-z0-9+/=]/g, "");
    return cleaned.length ? cleaned : "";
  }

  function todayISO() {
    const d = new Date();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return d.getFullYear() + "-" + m + "-" + day;
  }

  async function api(path, opts) {
    const res = await fetch(path, opts);
    const ct = res.headers.get("content-type") || "";
    if (ct.indexOf("application/json") >= 0) {
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || ("HTTP " + res.status));
      return data;
    }
    const text = await res.text();
    if (!res.ok) throw new Error(text || ("HTTP " + res.status));
    return text;
  }

  // Lightweight markdown → HTML (tables, headings, lists, code, emphasis)
  function renderMarkdown(md) {
    const lines = String(md).replace(/\r\n/g, "\n").split("\n");
    const out = [];
    let i = 0;
    let inUl = false;
    let inOl = false;
    let inCode = false;
    let codeBuf = [];
    let tableBuf = [];

    function closeLists() {
      if (inUl) { out.push("</ul>"); inUl = false; }
      if (inOl) { out.push("</ol>"); inOl = false; }
    }

    function flushTable() {
      if (!tableBuf.length) return;
      const rows = tableBuf.slice();
      tableBuf = [];
      if (rows.length < 2) {
        rows.forEach(function (r) { out.push("<p>" + inline(r) + "</p>"); });
        return;
      }
      const splitRow = function (row) {
        return row.replace(/^\|/, "").replace(/\|$/, "").split("|").map(function (c) { return c.trim(); });
      };
      const isSep = function (row) {
        return /^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$/.test(row.trim());
      };
      let head = splitRow(rows[0]);
      let bodyStart = 1;
      if (rows[1] && isSep(rows[1])) bodyStart = 2;
      out.push("<table><thead><tr>");
      head.forEach(function (h) { out.push("<th>" + inline(h) + "</th>"); });
      out.push("</tr></thead><tbody>");
      for (let r = bodyStart; r < rows.length; r++) {
        if (isSep(rows[r])) continue;
        const cells = splitRow(rows[r]);
        out.push("<tr>");
        cells.forEach(function (c) { out.push("<td>" + inline(c) + "</td>"); });
        out.push("</tr>");
      }
      out.push("</tbody></table>");
    }

    function inline(text) {
      let t = escapeHtml(text);
      t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
      t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
      t = t.replace(/\*([^*]+)\*/g, "<em>$1</em>");
      t = t.replace(/_([^_]+)_/g, "<em>$1</em>");
      return t;
    }

    while (i < lines.length) {
      const line = lines[i];

      if (line.trim().indexOf("```") === 0) {
        flushTable();
        closeLists();
        if (!inCode) {
          inCode = true;
          codeBuf = [];
        } else {
          out.push("<pre><code>" + escapeHtml(codeBuf.join("\n")) + "</code></pre>");
          inCode = false;
        }
        i++;
        continue;
      }
      if (inCode) {
        codeBuf.push(line);
        i++;
        continue;
      }

      if (/^\s*\|/.test(line) && line.indexOf("|") !== line.lastIndexOf("|")) {
        closeLists();
        tableBuf.push(line);
        i++;
        continue;
      } else {
        flushTable();
      }

      if (/^\s*---+\s*$/.test(line)) {
        closeLists();
        out.push("<hr/>");
        i++;
        continue;
      }

      const hm = /^(#{1,6})\s+(.*)$/.exec(line);
      if (hm) {
        closeLists();
        const level = hm[1].length;
        out.push("<h" + level + ">" + inline(hm[2]) + "</h" + level + ">");
        i++;
        continue;
      }

      if (/^\s*>\s?/.test(line)) {
        closeLists();
        out.push("<blockquote>" + inline(line.replace(/^\s*>\s?/, "")) + "</blockquote>");
        i++;
        continue;
      }

      const ul = /^\s*[-*]\s+(.*)$/.exec(line);
      if (ul) {
        if (inOl) { out.push("</ol>"); inOl = false; }
        if (!inUl) { out.push("<ul>"); inUl = true; }
        out.push("<li>" + inline(ul[1]) + "</li>");
        i++;
        continue;
      }

      const ol = /^\s*\d+\.\s+(.*)$/.exec(line);
      if (ol) {
        if (inUl) { out.push("</ul>"); inUl = false; }
        if (!inOl) { out.push("<ol>"); inOl = true; }
        out.push("<li>" + inline(ol[1]) + "</li>");
        i++;
        continue;
      }

      if (!line.trim()) {
        closeLists();
        i++;
        continue;
      }

      closeLists();
      out.push("<p>" + inline(line) + "</p>");
      i++;
    }
    flushTable();
    closeLists();
    if (inCode) out.push("<pre><code>" + escapeHtml(codeBuf.join("\n")) + "</code></pre>");
    return out.join("\n");
  }

  function foundingOf(rec) {
    return rec.founding || {};
  }

  function field(obj, camel, snake) {
    if (!obj) return undefined;
    if (obj[camel] != null) return obj[camel];
    if (obj[snake] != null) return obj[snake];
    return undefined;
  }

  function setFoundingUI(rec) {
    const f = foundingOf(rec);
    const banner = document.getElementById("founding-banner");
    const saveBtn = document.getElementById("f-save");
    const clearBtn = document.getElementById("f-clear");
    const sigText = document.getElementById("f-sig-text");
    const status = field(f, "status", "status");
    if (status === "closed") {
      banner.className = "banner ok";
      const hash = field(f, "recordHash", "record_hash") || "";
      banner.innerHTML =
        "<strong>FOUNDING SIGNATURE CLOSED — DO NOT RE-SIGN</strong><br/>Signed by " +
        escapeHtml(field(f, "printedName", "printed_name") || "") +
        " on " +
        escapeHtml(field(f, "requiredDateDisplay", "required_date_display") || "") +
        (field(f, "signedAtUtc", "signed_at_utc")
          ? " · recorded " + escapeHtml(field(f, "signedAtUtc", "signed_at_utc"))
          : "") +
        (hash ? " · hash " + escapeHtml(String(hash).slice(0, 16)) + "…" : "");
      saveBtn.disabled = true;
      clearBtn.disabled = true;
      sigText.disabled = true;
      sigText.value = field(f, "signatureText", "signature_text") || "";
      document.getElementById("founding-result").textContent =
        "This Part A lock cannot be reopened by the application.";
    } else {
      banner.className = "banner warn";
      banner.innerHTML =
        "<strong>WARNING:</strong> Only <em>" +
        escapeHtml(META.foundingName) +
        "</em> may execute this signature, once only, for founding date <strong>" +
        escapeHtml(META.foundingDateDisplay) +
        "</strong>. After save, this block locks forever.";
      saveBtn.disabled = false;
      clearBtn.disabled = false;
      sigText.disabled = false;
    }
  }

  function renderRecords(rec) {
    const f = foundingOf(rec);
    const status = field(f, "status", "status");
    const pill =
      status === "closed"
        ? '<span class="status-pill closed">CLOSED</span>'
        : '<span class="status-pill open">OPEN</span>';
    let html = "<p><strong>Founding status:</strong> " + pill + "</p>";
    html += "<p><strong>Document:</strong> " + escapeHtml(rec.document || "") + "</p>";
    html += "<p><strong>Seat:</strong> " + escapeHtml(rec.seat || "") + "</p>";
    if (status === "closed") {
      html +=
        "<p><strong>Founding signatory:</strong> " +
        escapeHtml(field(f, "printedName", "printed_name") || "") +
        "</p>";
      html +=
        "<p><strong>Typed signature:</strong> " +
        escapeHtml(field(f, "signatureText", "signature_text") || "") +
        "</p>";
      html +=
        "<p><strong>Closure:</strong> " +
        escapeHtml(field(f, "closureLegend", "closure_legend") || "") +
        "</p>";
      const img = field(f, "signatureImagePngB64", "signature_image_png_b64");
      if (img) {
        const b64 = safeBase64(img);
        if (b64) {
          html +=
            '<p><img class="thumb" alt="Founding signature" src="data:image/png;base64,' +
            b64 +
            '" /></p>';
        }
      }
    }

    const opt = rec.optional || {};
    const co = opt.coPresident || opt.co_president;
    const ju = opt.justice;
    const wit = opt.witness;
    const notary = opt.notary;
    if (co) {
      html +=
        "<p><strong>Co-President ack:</strong> " +
        escapeHtml(field(co, "signatureText", "signature_text") || "") +
        " (" +
        escapeHtml(co.date || "") +
        ")</p>";
    }
    if (ju) {
      html +=
        "<p><strong>Justice ack:</strong> " +
        escapeHtml(field(ju, "signatureText", "signature_text") || "") +
        " (" +
        escapeHtml(ju.date || "") +
        ")</p>";
    }
    if (wit) {
      html +=
        "<p><strong>Witness:</strong> " +
        escapeHtml(field(wit, "printedName", "printed_name") || "") +
        " / " +
        escapeHtml(field(wit, "signatureText", "signature_text") || "") +
        " (" +
        escapeHtml(wit.date || "") +
        ")</p>";
    }
    if (notary) {
      html +=
        "<p><strong>Notary:</strong> " +
        escapeHtml(field(notary, "printedName", "printed_name") || "") +
        " / " +
        escapeHtml(field(notary, "signatureText", "signature_text") || "") +
        " (" +
        escapeHtml(notary.date || "") +
        ")</p>";
    }

    html +=
      '<p class="muted">Citizens enrolled: ' +
      (rec.citizens || []).length +
      " · Last update: " +
      escapeHtml(field(rec, "updatedAtUtc", "updated_at_utc") || "n/a") +
      "</p>";
    document.getElementById("record-summary").innerHTML = html;

    const citizens = rec.citizens || [];
    if (!citizens.length) {
      document.getElementById("citizen-table").innerHTML =
        '<p class="muted">No citizen signatures yet.</p>';
    } else {
      let t =
        "<table><thead><tr><th>#</th><th>Name</th><th>Granted by</th><th>Dates</th><th>Signature</th></tr></thead><tbody>";
      citizens
        .slice()
        .reverse()
        .forEach(function (c) {
          t +=
            "<tr><td>" +
            escapeHtml(field(c, "entryNo", "entry_no")) +
            "</td><td>" +
            escapeHtml(field(c, "printedName", "printed_name") || "") +
            "</td><td>" +
            escapeHtml(field(c, "grantedBy", "granted_by") || "") +
            "</td><td>granted " +
            escapeHtml(field(c, "grantedDate", "granted_date") || "") +
            "<br/>signed " +
            escapeHtml(field(c, "signedDate", "signed_date") || "") +
            "</td><td>" +
            escapeHtml(field(c, "signatureText", "signature_text") || "");
          const img = field(c, "signatureImagePngB64", "signature_image_png_b64");
          if (img) {
            const b64 = safeBase64(img);
            if (b64) {
              t +=
                '<br/><img class="thumb" alt="sig" src="data:image/png;base64,' +
                b64 +
                '" />';
            }
          }
          t += "</td></tr>";
        });
      t += "</tbody></table>";
      document.getElementById("citizen-table").innerHTML = t;
    }

    const next =
      field(rec, "nextCitizenNo", "next_citizen_no") != null
        ? field(rec, "nextCitizenNo", "next_citizen_no")
        : (rec.citizens || []).length + 1;
    document.getElementById("c-entry").value = String(next);
  }

  async function refresh() {
    const rec = await api("/api/record");
    setFoundingUI(rec);
    renderRecords(rec);
    const opt = rec.optional || {};
    const co = opt.coPresident || opt.co_president;
    const ju = opt.justice;
    const wit = opt.witness;
    const notary = opt.notary;
    if (co) {
      document.getElementById("o-co-sig").value = field(co, "signatureText", "signature_text") || "";
      document.getElementById("o-co-date").value = co.date || "";
    }
    if (ju) {
      document.getElementById("o-j-sig").value = field(ju, "signatureText", "signature_text") || "";
      document.getElementById("o-j-date").value = ju.date || "";
    }
    if (wit) {
      document.getElementById("o-w-name").value = field(wit, "printedName", "printed_name") || "";
      document.getElementById("o-w-sig").value = field(wit, "signatureText", "signature_text") || "";
      document.getElementById("o-w-date").value = wit.date || "";
    }
    if (notary) {
      document.getElementById("o-n-name").value = field(notary, "printedName", "printed_name") || "";
      document.getElementById("o-n-sig").value = field(notary, "signatureText", "signature_text") || "";
      document.getElementById("o-n-county").value = notary.county || "";
      document.getElementById("o-n-commission").value =
        field(notary, "commissionExpires", "commission_expires") || "";
      document.getElementById("o-n-date").value = notary.date || "";
    }
  }

  async function loadDocument(kind) {
    const map = {
      combined: "/api/document/combined",
      constitution: "/api/document/constitution",
      packet: "/api/document/packet"
    };
    const path = map[kind] || map.combined;
    const view = document.getElementById("doc-view");
    view.innerHTML = "<p class='muted'>Loading…</p>";
    try {
      const md = await api(path);
      view.innerHTML = renderMarkdown(md);
    } catch (err) {
      view.innerHTML = "<p class='banner warn'>" + escapeHtml(err.message) + "</p>";
    }
  }

  function wireTabs() {
    document.querySelectorAll(".tab").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll(".tab").forEach(function (b) {
          b.classList.remove("active");
        });
        document.querySelectorAll(".panel").forEach(function (p) {
          p.classList.remove("active");
        });
        btn.classList.add("active");
        document.getElementById(btn.dataset.tab).classList.add("active");
      });
    });
  }

  async function boot() {
    wireTabs();
    try {
      META = Object.assign(META, await api("/api/meta"));
    } catch (_) {
      /* keep defaults */
    }
    document.getElementById("app-title").textContent = META.app || META.document || document.title;
    document.getElementById("app-seat").textContent = "Seat of Record: " + (META.seat || "");
    document.getElementById("f-name").value = META.foundingName || "";
    document.getElementById("f-capacity").value = META.foundingCapacity || "";
    document.getElementById("f-date").value = META.foundingDateDisplay || "";
    document.getElementById("f-sig-text").placeholder = META.foundingName || "";

    const fPad = pad(document.getElementById("f-canvas"));
    const cPad = pad(document.getElementById("c-canvas"));

    document.querySelectorAll("[data-doc]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        loadDocument(btn.getAttribute("data-doc"));
      });
    });
    document.getElementById("btn-print-doc").addEventListener("click", function () {
      window.print();
    });

    document.getElementById("f-clear").onclick = function () {
      fPad.clear();
    };
    document.getElementById("c-clear").onclick = function () {
      cPad.clear();
    };
    document.getElementById("btn-refresh").onclick = function () {
      refresh().catch(function (err) {
        alert(err.message);
      });
    };

    document.getElementById("f-save").onclick = async function () {
      try {
        const signature_text = document.getElementById("f-sig-text").value.trim();
        if (signature_text !== META.foundingName) {
          alert("Typed signature must exactly match: " + META.foundingName);
          return;
        }
        if (
          !confirm(
            "Affix the ONE-TIME founding signature and permanently close Part A? This cannot be undone in the app."
          )
        ) {
          return;
        }
        const rec = await api("/api/founding", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            signature_text: signature_text,
            signature_image_data_url: fPad.toDataUrl()
          })
        });
        document.getElementById("founding-result").textContent =
          "Founding signature recorded and closed.";
        setFoundingUI(rec);
        renderRecords(rec);
      } catch (err) {
        alert(err.message);
      }
    };

    document.getElementById("c-save").onclick = async function () {
      try {
        const body = {
          printed_name: document.getElementById("c-name").value.trim(),
          granted_by: document.getElementById("c-granted-by").value.trim(),
          granted_date: document.getElementById("c-granted-date").value,
          signed_date: document.getElementById("c-signed-date").value || todayISO(),
          witness: document.getElementById("c-witness").value.trim(),
          signature_text: document.getElementById("c-sig-text").value.trim(),
          signature_image_data_url: cPad.toDataUrl()
        };
        if (!body.printed_name || !body.granted_by || !body.granted_date || !body.signature_text) {
          alert("Citizen name, granted by, granted date, and typed signature are required.");
          return;
        }
        const rec = await api("/api/citizen", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        const citizens = rec.citizens || [];
        const last = citizens[citizens.length - 1] || {};
        document.getElementById("citizen-result").textContent =
          "Citizen entry #" + (field(last, "entryNo", "entry_no") || "?") + " added.";
        document.getElementById("c-name").value = "";
        document.getElementById("c-sig-text").value = "";
        document.getElementById("c-witness").value = "";
        cPad.clear();
        renderRecords(rec);
      } catch (err) {
        alert(err.message);
      }
    };

    document.getElementById("o-co-save").onclick = async function () {
      try {
        const rec = await api("/api/optional/co_president", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            signature_text: document.getElementById("o-co-sig").value.trim(),
            date: document.getElementById("o-co-date").value || todayISO()
          })
        });
        document.getElementById("optional-result").textContent =
          "Co-President acknowledgment saved.";
        renderRecords(rec);
      } catch (err) {
        alert(err.message);
      }
    };

    document.getElementById("o-j-save").onclick = async function () {
      try {
        const rec = await api("/api/optional/justice", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            signature_text: document.getElementById("o-j-sig").value.trim(),
            date: document.getElementById("o-j-date").value || todayISO()
          })
        });
        document.getElementById("optional-result").textContent = "Justice acknowledgment saved.";
        renderRecords(rec);
      } catch (err) {
        alert(err.message);
      }
    };

    document.getElementById("o-w-save").onclick = async function () {
      try {
        const rec = await api("/api/optional/witness", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            printed_name: document.getElementById("o-w-name").value.trim(),
            signature_text: document.getElementById("o-w-sig").value.trim(),
            date: document.getElementById("o-w-date").value || todayISO()
          })
        });
        document.getElementById("optional-result").textContent = "Witness acknowledgment saved.";
        renderRecords(rec);
      } catch (err) {
        alert(err.message);
      }
    };

    document.getElementById("o-n-save").onclick = async function () {
      try {
        const rec = await api("/api/optional/notary", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            printed_name: document.getElementById("o-n-name").value.trim(),
            signature_text: document.getElementById("o-n-sig").value.trim(),
            county: document.getElementById("o-n-county").value.trim(),
            commission_expires: document.getElementById("o-n-commission").value,
            date: document.getElementById("o-n-date").value || todayISO()
          })
        });
        document.getElementById("optional-result").textContent = "Notary acknowledgment saved.";
        renderRecords(rec);
      } catch (err) {
        alert(err.message);
      }
    };

    document.getElementById("btn-export-json").onclick = function () {
      window.location.href = "/api/export.json";
    };
    document.getElementById("btn-export-md").onclick = function () {
      window.location.href = "/api/export.md";
    };

    ["c-granted-date", "c-signed-date", "o-co-date", "o-j-date", "o-w-date", "o-n-date"].forEach(
      function (id) {
        document.getElementById(id).value = todayISO();
      }
    );

    await loadDocument("combined");
    await refresh();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      boot().catch(function (err) {
        alert("Failed to start UI: " + err.message);
      });
    });
  } else {
    boot().catch(function (err) {
      alert("Failed to start UI: " + err.message);
    });
  }
})();
