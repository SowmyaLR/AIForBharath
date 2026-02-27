/**
 * fhir/client/app.js
 * NHCX FHIR Converter — frontend logic
 */

const SERVER_URL = "http://localhost:8001";

// ── State ──────────────────────────────────────────────────────────────────
let selectedFiles = [];   // Array of File objects
let lastBundle = null;    // Last successful FHIR bundle

// ── DOM refs ───────────────────────────────────────────────────────────────
const fileInput = document.getElementById("file-input");
const fileList = document.getElementById("file-list");
const dropZone = document.getElementById("drop-zone");
const pasteArea = document.getElementById("paste-area");
const btnConvert = document.getElementById("btn-convert");
const btnConvText = document.getElementById("btn-convert-text");
const jsonViewer = document.getElementById("json-viewer");
const resultMeta = document.getElementById("result-meta");
const statusDot = document.getElementById("status-dot");
const statusLabel = document.getElementById("status-label");
const btnDownload = document.getElementById("btn-download");
const serverStatus = document.getElementById("server-status");

// ── Tab switching ──────────────────────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const panel = btn.dataset.tab;
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById("tab-" + panel).classList.add("active");
    });
});

// ── Drop zone interactions ─────────────────────────────────────────────────
dropZone.addEventListener("dragover", e => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", e => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    addFiles([...e.dataTransfer.files]);
});

fileInput.addEventListener("change", () => {
    addFiles([...fileInput.files]);
    fileInput.value = "";
});

// ── File management ────────────────────────────────────────────────────────
function addFiles(newFiles) {
    const pdfs = newFiles.filter(f => f.type === "application/pdf" || f.name.endsWith(".pdf"));
    if (pdfs.length !== newFiles.length) {
        showToast("Only PDF files are accepted.", "warn");
    }
    pdfs.forEach(f => {
        if (!selectedFiles.find(x => x.name === f.name && x.size === f.size)) {
            selectedFiles.push(f);
        }
    });
    renderFileList();
}

function removeFile(idx) {
    selectedFiles.splice(idx, 1);
    renderFileList();
}

const HI_LABELS = {
    discharge_summary: "Discharge Summary",
    lab_report: "Lab Report",
    clinical_note: "Clinical Note",
    prescription: "Prescription",
    radiology_report: "Radiology Report",
};

function guessHiType(filename) {
    const n = filename.toLowerCase();
    if (n.includes("discharge") || n.includes("summary")) return "discharge_summary";
    if (n.includes("lab") || n.includes("path") || n.includes("test") || n.includes("blood")) return "lab_report";
    if (n.includes("radio") || n.includes("xray") || n.includes("mri") || n.includes("ct")) return "radiology_report";
    if (n.includes("prescription") || n.includes("rx")) return "prescription";
    return "clinical_note";
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function renderFileList() {
    fileList.innerHTML = "";
    if (!selectedFiles.length) {
        btnConvert.disabled = true;
        return;
    }
    btnConvert.disabled = false;
    selectedFiles.forEach((file, idx) => {
        const hiType = guessHiType(file.name);
        const item = document.createElement("div");
        item.className = "file-item";
        item.innerHTML = `
      <span class="fi-icon">📄</span>
      <span class="fi-name" title="${file.name}">${file.name}</span>
      <span class="hi-badge ${hiType}">${HI_LABELS[hiType] || hiType}</span>
      <span class="fi-size">${formatBytes(file.size)}</span>
      <button class="fi-remove" title="Remove" onclick="removeFile(${idx})">✕</button>
    `;
        fileList.appendChild(item);
    });
}

// ── Server health check ────────────────────────────────────────────────────
async function checkServerHealth() {
    try {
        const r = await fetch(`${SERVER_URL}/health`, { signal: AbortSignal.timeout(3000) });
        if (r.ok) {
            const data = await r.json();
            serverStatus.innerHTML = `
        <span style="color:var(--green)">● Online</span>
        &nbsp;|&nbsp; MedGemma: <span style="color:${data.medgemma_available ? 'var(--green)' : 'var(--yellow)'}">${data.medgemma_available ? 'Available' : 'Unavailable (fallback)'}</span>
        &nbsp;|&nbsp; Profile: <code style="font-size:11px">${data.fhir_profile.split('/').pop()}</code>
      `;
            return;
        }
    } catch (_) { }
    serverStatus.innerHTML = `<span style="color:var(--red)">● Offline — start nhir/server on port 8001</span>`;
}
checkServerHealth();

// ── Conversion ─────────────────────────────────────────────────────────────
async function runConversion(formData, isBtnEl) {
    setStatus("loading", "Converting…");
    isBtnEl.disabled = true;
    resultMeta.innerHTML = "";
    jsonViewer.innerHTML = `<div class="empty-state"><div class="spinner"></div><p>Processing with MedGemma…</p></div>`;

    try {
        const resp = await fetch(`${SERVER_URL}/convert/${formData instanceof FormData ? "claim" : "text"}`, {
            method: "POST",
            body: formData,
            headers: formData instanceof FormData ? {} : { "Content-Type": "application/json" },
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || `Server error ${resp.status}`);
        }

        const data = await resp.json();
        lastBundle = data.fhir_bundle;
        btnDownload.style.display = "flex";

        // Render meta badges
        resultMeta.innerHTML = `
      <span class="result-badge rb-docs">${data.documents_processed} doc${data.documents_processed > 1 ? "s" : ""}</span>
      <span class="result-badge ${data.metadata.medgemma_used ? "rb-medgemma" : "rb-fallback"}">${data.metadata.medgemma_used ? "MedGemma" : "Deterministic"}</span>
      <span class="result-badge rb-nhcx">NHCX Claim</span>
      ${data.detected_hi_types.map(t => `<span class="hi-badge ${t}">${HI_LABELS[t] || t}</span>`).join("")}
    `;

        // Update file list badges from actual server-detected types
        if (data.document_results) {
            data.document_results.forEach(dr => {
                const fi = selectedFiles.find(f => f.name === dr.filename);
                if (!fi) return;
                const idx = selectedFiles.indexOf(fi);
                const items = fileList.querySelectorAll(".file-item");
                if (items[idx]) {
                    const badge = items[idx].querySelector(".hi-badge");
                    if (badge) {
                        badge.className = `hi-badge ${dr.detected_hi_type}`;
                        badge.textContent = HI_LABELS[dr.detected_hi_type] || dr.detected_hi_type;
                    }
                }
            });
        }

        // Render JSON
        jsonViewer.innerHTML = syntaxHighlight(data.fhir_bundle);
        setStatus("ready", `Bundle generated • ${data.metadata.fhir_version}`);

    } catch (err) {
        setStatus("error", "Error");
        jsonViewer.innerHTML = `<div class="empty-state" style="color:var(--red)"><span style="font-size:36px">⚠</span><p>${err.message}</p></div>`;
        showToast(err.message, "error");
    } finally {
        isBtnEl.disabled = false;
    }
}

// ── PDF submit ─────────────────────────────────────────────────────────────
btnConvert.addEventListener("click", async () => {
    if (!selectedFiles.length) return;
    const fd = new FormData();
    selectedFiles.forEach(f => fd.append("files", f));
    const fields = ["patient-name", "patient-id", "insurer-name", "policy-number"];
    const keys = ["patient_name", "patient_id", "insurer_name", "policy_number"];
    fields.forEach((id, i) => {
        const val = document.getElementById(id)?.value?.trim();
        if (val) fd.append(keys[i], val);
    });
    await runConversion(fd, btnConvert);
});

// ── Text submit ────────────────────────────────────────────────────────────
btnConvText.addEventListener("click", async () => {
    const text = pasteArea.value.trim();
    if (!text) { showToast("Please paste some clinical text first.", "warn"); return; }
    const body = JSON.stringify({
        text,
        patient_name: document.getElementById("pt-name-text")?.value?.trim() || null,
        patient_id: document.getElementById("pt-id-text")?.value?.trim() || null,
        insurer_name: document.getElementById("insurer-text")?.value?.trim() || null,
        use_case: "claim",
    });
    await runConversion(body, btnConvText);
});

// ── Download ───────────────────────────────────────────────────────────────
btnDownload.addEventListener("click", () => {
    if (!lastBundle) return;
    const blob = new Blob([JSON.stringify(lastBundle, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `nhcx_claim_bundle_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
});

// ── Helpers ────────────────────────────────────────────────────────────────
function setStatus(state, label) {
    statusDot.className = "status-dot " + state;
    statusLabel.textContent = label;
}

function syntaxHighlight(obj) {
    const str = JSON.stringify(obj, null, 2);
    return str.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, match => {
        let cls = "jn";
        if (/^"/.test(match)) {
            cls = /:$/.test(match) ? "jk" : "jv";
        } else if (/true|false|null/.test(match)) {
            cls = "jb";
        }
        return `<span class="${cls}">${match}</span>`;
    });
}

function showToast(msg, type = "info") {
    const t = document.createElement("div");
    const colors = { warn: "#f59e0b", error: "#ef4444", info: "#3b82f6" };
    t.style.cssText = `position:fixed;bottom:24px;right:24px;z-index:999;padding:12px 20px;border-radius:10px;background:rgba(15,23,42,0.95);border:1px solid ${colors[type] || colors.info};color:#f0f4ff;font-size:13px;font-family:'Inter',sans-serif;box-shadow:0 8px 24px rgba(0,0,0,0.5);animation:fadeIn 0.3s ease`;
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 4000);
}

// ── Init ───────────────────────────────────────────────────────────────────
btnConvert.disabled = true;
btnDownload.style.display = "none";
setStatus("", "Waiting for input");
