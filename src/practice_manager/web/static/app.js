/**
 * Practice Manager - Web frontend
 * Matches desktop layout: left sets list, right details pane
 */

const API = {
  library: "/api/library",
  status: "/api/status",
  practice: {
    start: "/api/practice/start",
    success: "/api/practice/success",
    fail: "/api/practice/fail",
    reset: "/api/practice/reset",
  },
};

const INSTRUMENTS = ["bagpipes", "seconds", "bass", "snare", "tenor"];
const PART_LABELS = ["phrase", "line", "part"];

let libraryData = null;
let statusData = null;
let currentSession = null;
let selectedSet = null;

// DOM refs
const setsListEl = document.getElementById("sets-list");
const detailsPlaceholder = document.getElementById("details-placeholder");
const detailsContent = document.getElementById("details-content");
const setInstrumentSelect = document.getElementById("set-instrument");
const focusSetCheckbox = document.getElementById("focus-set");
const tunesGroup = document.getElementById("tunes-group");
const partsGroup = document.getElementById("parts-group");
const decayRateInput = document.getElementById("decay-rate");
const focusOnlyCheckbox = document.getElementById("focus-only");
const sessionView = document.getElementById("session-view");
const pdfFrame = document.getElementById("pdf-frame");
const pdfPlaceholder = document.getElementById("pdf-placeholder");
const audioPlayer = document.getElementById("audio-player");
const audioPlaceholder = document.getElementById("audio-placeholder");
const sessionTitle = document.getElementById("session-title");
const sessionContext = document.getElementById("session-context");
const streakDisplay = document.getElementById("streak-display");
const btnSuccess = document.getElementById("btn-success");
const btnFail = document.getElementById("btn-fail");
const btnEnd = document.getElementById("btn-end");
const recallModeCheckbox = document.getElementById("recall-mode");
const recallShowInput = document.getElementById("recall-show");
const recallHideInput = document.getElementById("recall-hide");
const pdfContainer = document.getElementById("pdf-container");

let recallTimerId = null;
let recallPhaseShow = true;

function getItemStatus(itemId) {
  if (!statusData?.items) return null;
  return statusData.items[itemId] || null;
}

async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

async function fetchPost(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

async function saveStatus() {
  if (!statusData) return;
  await fetchPost(API.status, statusData);
}

async function loadData() {
  const [lib, status] = await Promise.all([
    fetchJson(API.library),
    fetchJson(API.status),
  ]);
  libraryData = lib;
  statusData = status;
}

function escapeHtml(s) {
  if (!s) return "";
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function escapeAttr(s) {
  if (!s) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function renderSetsList() {
  if (!libraryData?.sets || !statusData) return;

  const focusIds = new Set(statusData.focus_set_ids || []);
  const showFocusOnly = statusData.show_focus_only || false;
  const items = statusData.items || {};

  let html = "";
  for (const s of libraryData.sets) {
    const setId = s.set_id;
    if (showFocusOnly && !focusIds.has(setId)) continue;

    const tuneIds = (s.tunes || []).map((t) => t.tune_id);
    const partIds = (s.parts || []).map((p) => p.part_full_id || `${setId}|Parts|${p.part_id}`);
    const practiced = [...tuneIds, ...partIds];
    const mastered = practiced.filter((id) => (items[id] || {}).score >= 100).length;
    const total = practiced.length;
    const summary = total ? `${mastered}/${total}` : "—";

    const isFocus = focusIds.has(setId);
    const star = isFocus ? "★ " : "";
    const selected = selectedSet?.set_id === setId ? " selected" : "";

    html += `
      <div class="set-list-item${selected}" data-set-id="${escapeAttr(setId)}">
        <div class="set-name">${star}${escapeHtml(s.set_folder_name)}</div>
        <div class="set-summary">[${summary}]</div>
      </div>
    `;
  }

  setsListEl.innerHTML = html;
  setsListEl.querySelectorAll(".set-list-item").forEach((el) => {
    el.addEventListener("click", () => selectSet(el.dataset.setId));
  });
}

function selectSet(setId) {
  const set = libraryData?.sets?.find((s) => s.set_id === setId);
  if (!set) return;
  selectedSet = set;
  renderSetsList();
  renderDetails();
}

function renderDetails() {
  if (!selectedSet || !statusData) {
    detailsPlaceholder.classList.remove("hidden");
    detailsContent.classList.add("hidden");
    return;
  }

  detailsPlaceholder.classList.add("hidden");
  detailsContent.classList.remove("hidden");

  const setId = selectedSet.set_id;
  const setPath = selectedSet.set_path || "";
  const setInstruments = statusData.set_instruments || {};
  const focusIds = statusData.focus_set_ids || [];
  const defaultInst = statusData.focus_instrument || "bass";
  const instrument = setInstruments[setId] || defaultInst;

  // Instrument selector
  setInstrumentSelect.innerHTML = INSTRUMENTS.map(
    (i) => `<option value="${i}" ${i === instrument ? "selected" : ""}>${i}</option>`
  ).join("");
  setInstrumentSelect.onchange = () => {
    setInstruments[setId] = setInstrumentSelect.value;
    statusData.set_instruments = { ...setInstruments };
    statusData.focus_instrument = setInstrumentSelect.value;
    saveStatus();
  };

  // Focus set
  focusSetCheckbox.checked = focusIds.includes(setId);
  focusSetCheckbox.onchange = () => {
    if (focusSetCheckbox.checked && !focusIds.includes(setId)) {
      focusIds.push(setId);
    } else if (!focusSetCheckbox.checked) {
      const idx = focusIds.indexOf(setId);
      if (idx >= 0) focusIds.splice(idx, 1);
    }
    statusData.focus_set_ids = [...focusIds];
    saveStatus();
    renderSetsList();
  };

  // Tunes
  tunesGroup.innerHTML = "";
  const tunesGroupTitle = document.createElement("h3");
  tunesGroupTitle.textContent = "Tunes";
  tunesGroup.appendChild(tunesGroupTitle);

  for (const t of selectedSet.tunes || []) {
    const rec = getItemStatus(t.tune_id) || {};
    const score = rec.score ?? 0;
    const streak = rec.streak ?? 0;
    const row = document.createElement("div");
    row.className = "item-row";
    row.innerHTML = `
      <span class="item-info">${escapeHtml(t.tune_name)}: ${score.toFixed(0)}% | ${streak}</span>
      <div class="item-actions">
        <button class="btn btn-success btn-small start-session">Start Session</button>
      </div>
    `;
    row.querySelector(".start-session").onclick = () =>
      startSession("tune", t.tune_id, t.tune_name, setInstrumentSelect.value, {
        set_id: setId,
        set_path: setPath,
        tune_name: t.tune_name,
      });
    tunesGroup.appendChild(row);
  }

  // Parts (grouped by tune)
  partsGroup.innerHTML = "";
  const parts = selectedSet.parts || [];
  if (parts.length) {
    const partsGroupTitle = document.createElement("h3");
    partsGroupTitle.textContent = "Parts";
    partsGroup.appendChild(partsGroupTitle);

    const byTune = {};
    for (const p of parts) {
      const tid = p.tune_id || "";
      const tname = p.tune_name || "Parts";
      const lbl = p.label || "part";
      if (!byTune[tid]) byTune[tid] = { tune_name: tname, phrase: [], line: [], part: [] };
      if (PART_LABELS.includes(lbl)) {
        byTune[tid][lbl].push(p);
      }
    }

    const tuneOrder = (selectedSet.tunes || []).map((t) => t.tune_id);
    const orderedTuneIds = [...new Set([...tuneOrder, ...Object.keys(byTune)])];

    for (const tid of orderedTuneIds) {
      if (!byTune[tid]) continue;
      const tdata = byTune[tid];
      const subheader = document.createElement("div");
      subheader.className = "tune-subheader";
      subheader.textContent = tdata.tune_name;
      partsGroup.appendChild(subheader);

      for (const lbl of PART_LABELS) {
        for (const p of tdata[lbl] || []) {
          const pid = p.part_full_id || `${setId}|Parts|${p.part_id}`;
          const rec = getItemStatus(pid) || {};
          const score = rec.score ?? 0;
          const streak = rec.streak ?? 0;
          const display = p.short_label || p.part_id;

          const row = document.createElement("div");
          row.className = "item-row part-indent";
          row.innerHTML = `
            <span class="item-info">${escapeHtml(display)} (${lbl}): ${score.toFixed(0)}% | ${streak}</span>
            <div class="item-actions">
              <button class="btn btn-success btn-small start-session">Start Session</button>
              <button class="btn btn-secondary btn-small reset-part">Reset</button>
            </div>
          `;
          row.querySelector(".start-session").onclick = () =>
            startSession("part", pid, display, setInstrumentSelect.value, {
              set_id: setId,
              part_record: { pdf_path: p.pdf_path, wav_path: p.wav_path, part_id: p.part_id },
            });
          row.querySelector(".reset-part").onclick = () => resetPart(pid);
          partsGroup.appendChild(row);
        }
      }
    }
  }
}

async function startSession(itemType, itemId, displayName, instrument, context) {
  const body = {
    item_type: itemType,
    item_id: itemId,
    display_name: displayName,
    instrument,
    set_id: context.set_id,
  };
  if (itemType === "tune") {
    body.set_path = context.set_path;
    body.tune_name = context.tune_name;
  } else if (context.part_record?.pdf_path && context.part_record?.wav_path) {
    body.part_record = context.part_record;
  }

  try {
    const result = await fetchPost(API.practice.start, body);
    showSession({
      itemType,
      itemId,
      displayName,
      context: context.set_id ? context.set_id.replace(/\|/g, " | ") : "",
      pdfUrl: result.pdf_url,
      wavUrl: result.wav_url,
      streak: result.streak ?? 0,
    });
  } catch (err) {
    alert("Failed to start session: " + err.message);
  }
}

async function resetPart(partId) {
  try {
    await fetchPost(API.practice.reset, { item_id: partId, item_type: "part" });
    await loadData();
    renderSetsList();
    if (selectedSet) renderDetails();
  } catch (err) {
    alert("Failed to reset: " + err.message);
  }
}

function setRecallVisible(visible) {
  if (visible) {
    pdfContainer.classList.remove("recall-hidden");
  } else {
    pdfContainer.classList.add("recall-hidden");
  }
}

function recallTick() {
  if (!currentSession || !recallModeCheckbox.checked) return;
  const showSec = Math.max(5, parseInt(recallShowInput.value, 10) || 60);
  const hideSec = Math.max(5, parseInt(recallHideInput.value, 10) || 30);
  setRecallVisible(recallPhaseShow);
  const ms = recallPhaseShow ? showSec * 1000 : hideSec * 1000;
  recallPhaseShow = !recallPhaseShow;
  recallTimerId = setTimeout(recallTick, ms);
}

function stopRecallMode() {
  if (recallTimerId) {
    clearTimeout(recallTimerId);
    recallTimerId = null;
  }
  recallModeCheckbox.checked = false;
  recallPhaseShow = true;
  setRecallVisible(true);
}

function showSession(session) {
  currentSession = session;
  sessionView.classList.remove("hidden");
  stopRecallMode();

  sessionTitle.textContent = session.displayName;
  sessionContext.textContent = session.context;
  streakDisplay.textContent = `Streak: ${session.streak}`;

  if (session.pdfUrl) {
    pdfFrame.src = session.pdfUrl;
    pdfFrame.classList.remove("hidden");
    pdfPlaceholder.classList.add("hidden");
  } else {
    pdfFrame.src = "";
    pdfFrame.classList.add("hidden");
    pdfPlaceholder.classList.remove("hidden");
  }

  if (session.wavUrl) {
    audioPlayer.src = session.wavUrl;
    audioPlayer.classList.remove("hidden");
    audioPlaceholder.classList.add("hidden");
    audioPlayer.play().catch(() => {});
  } else {
    audioPlayer.src = "";
    audioPlayer.classList.add("hidden");
    audioPlaceholder.classList.remove("hidden");
  }
}

function hideSession() {
  stopRecallMode();
  currentSession = null;
  sessionView.classList.add("hidden");
  pdfFrame.src = "";
  audioPlayer.pause();
  audioPlayer.src = "";
  loadData().then(() => {
    renderSetsList();
    if (selectedSet) renderDetails();
  });
}

async function recordSuccess() {
  if (!currentSession) return;
  try {
    const result = await fetchPost(API.practice.success, {
      item_id: currentSession.itemId,
      item_type: currentSession.itemType,
    });
    currentSession.streak = result.streak;
    streakDisplay.textContent = `Streak: ${result.streak}`;
    if (result.streak >= 10) {
      hideSession();
    }
  } catch (err) {
    alert("Failed to record success: " + err.message);
  }
}

async function recordFail() {
  if (!currentSession) return;
  try {
    await fetchPost(API.practice.fail, {
      item_id: currentSession.itemId,
      item_type: currentSession.itemType,
    });
    currentSession.streak = 0;
    streakDisplay.textContent = "Streak: 0";
  } catch (err) {
    alert("Failed to record fail: " + err.message);
  }
}

function init() {
  btnSuccess.addEventListener("click", recordSuccess);
  btnFail.addEventListener("click", recordFail);
  btnEnd.addEventListener("click", hideSession);

  recallModeCheckbox.addEventListener("change", () => {
    if (recallModeCheckbox.checked) {
      recallPhaseShow = true;
      recallTick();
    } else {
      stopRecallMode();
    }
  });

  function restartRecallTimer() {
    if (!currentSession || !recallModeCheckbox.checked || !recallTimerId) return;
    clearTimeout(recallTimerId);
    const showSec = Math.max(5, parseInt(recallShowInput.value, 10) || 60);
    const hideSec = Math.max(5, parseInt(recallHideInput.value, 10) || 30);
    const ms = recallPhaseShow ? showSec * 1000 : hideSec * 1000;
    recallTimerId = setTimeout(recallTick, ms);
  }
  recallShowInput.addEventListener("change", restartRecallTimer);
  recallHideInput.addEventListener("change", restartRecallTimer);

  decayRateInput.value = statusData?.decay_rate_percent_per_day ?? 1;
  decayRateInput.onchange = () => {
    statusData.decay_rate_percent_per_day = parseFloat(decayRateInput.value);
    saveStatus();
  };

  focusOnlyCheckbox.checked = statusData?.show_focus_only ?? false;
  focusOnlyCheckbox.onchange = () => {
    statusData.show_focus_only = focusOnlyCheckbox.checked;
    saveStatus();
    renderSetsList();
  };

  loadData()
    .then(() => {
      decayRateInput.value = statusData?.decay_rate_percent_per_day ?? 1;
      focusOnlyCheckbox.checked = statusData?.show_focus_only ?? false;
      renderSetsList();
    })
    .catch((err) => {
      setsListEl.innerHTML = `<div class="placeholder">Error: ${escapeHtml(err.message)}</div>`;
    });
}

init();
