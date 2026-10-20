"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

let image = null;          // working copy from the server
let status = null;         // last /api/status
let logNext = 0;
let logLines = [];         // all log lines fetched so far
let lastJobFinished = 0;
let capture = null;        // call button capture {index, startedLog, found}
let connFailed = false;    // last connection test without response

// ------------------------------------------------------------------- i18n
// Texts come from the server (window.I18N, see ui_texts.py) in the active language.
const I18N = window.I18N || {};
function t(key, params = {}) {
  const s = I18N[key] ?? key;
  return s.replace(/\{(\w+)\}/g, (m, k) => (k in params ? params[k] : m));
}
const LOCALE = document.documentElement.lang === "de" ? "de-DE" : "en-GB";

$$("[data-lang]").forEach(b => b.addEventListener("click", () => {
  document.cookie = `lang=${b.dataset.lang}; path=/; max-age=31536000; SameSite=Lax`;
  location.reload();
}));

async function api(method, url, body) {
  const opts = { method, headers: {} };
  if (body instanceof FormData) opts.body = body;
  else if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(url, opts);
  const data = res.headers.get("content-type")?.includes("json") ? await res.json() : null;
  if (!res.ok) throw new Error(data?.error || `${res.status} ${res.statusText}`);
  return data;
}

function setStatus(text, isError = false) {
  const el = $("#status");
  el.textContent = text;
  el.classList.toggle("error", isError);
}

async function guarded(fn) {
  try { await fn(); } catch (e) { setStatus(e.message, true); }
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// --------------------------------------------------------------- Tooltips
//
// Help texts (<p class="help"> in forms, [data-help] on elements) become an "i"
// symbol with a tooltip. The tooltip is a popover (top layer) so it also lies
// above modal dialogs.

const tip = document.createElement("div");
tip.id = "tip";
tip.className = "tip";
tip.setAttribute("role", "tooltip");
tip.setAttribute("popover", "manual");
document.body.append(tip);
let tipFor = null;

function showTip(btn) {
  tipFor = btn;
  tip.innerHTML = btn._help;
  if (!tip.matches(":popover-open")) tip.showPopover();
  btn.setAttribute("aria-describedby", "tip");
  const r = btn.getBoundingClientRect(), t = tip.getBoundingClientRect();
  const left = Math.min(Math.max(8, r.left + r.width / 2 - t.width / 2), innerWidth - t.width - 8);
  const below = r.bottom + 8 + t.height < innerHeight;
  tip.style.left = `${left}px`;
  tip.style.top = `${below ? r.bottom + 8 : r.top - t.height - 8}px`;
}

function hideTip() {
  if (tipFor) tipFor.removeAttribute("aria-describedby");
  tipFor = null;
  if (tip.matches(":popover-open")) tip.hidePopover();
}

function infoButton(html, label) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "info";
  b.textContent = "i";
  b.setAttribute("aria-label", `${t("js.explanation")}${label ? ": " + label : ""}`);
  b._help = html;
  b.addEventListener("mouseenter", () => showTip(b));
  b.addEventListener("mouseleave", hideTip);
  b.addEventListener("focus", () => showTip(b));
  b.addEventListener("blur", hideTip);
  b.addEventListener("click", e => {  // touch: tapping shows the text without triggering the label
    e.preventDefault();
    e.stopPropagation();
    showTip(b);
  });
  return b;
}

/** Put the symbol right after the visible text of an element. */
function attachInfo(target, html) {
  if (target._info) {  // append further paragraphs for the same item
    target._info._help += `<p>${html}</p>`;
    return;
  }
  const label = target.textContent.trim().split("\n")[0].slice(0, 40);
  const btn = infoButton(`<p>${html}</p>`, label);
  target._info = btn;
  // for <label>text <input></label>: text + symbol on one line, field below
  const field = target.matches("label") && target.querySelector("input:not([type=radio]):not([type=checkbox]), select");
  if (field) {
    const line = document.createElement("span");
    line.className = "label-line";
    while (target.firstChild && target.firstChild !== field) line.append(target.firstChild);
    line.append(btn);
    target.insertBefore(line, field);
  } else {
    target.append(btn);
  }
}

function initTooltips(root) {
  for (const p of $$("p.help", root)) {
    // data-for="legend": explanation of the whole group -> symbol at the heading
    let target = p.dataset.for === "legend" ? p.closest("fieldset")?.querySelector("legend") : p.previousElementSibling;
    while (target && target.matches("p.help")) target = target.previousElementSibling;
    if (!target) continue;
    attachInfo(target, p.innerHTML);
    p.remove();
  }
  for (const el of $$("[data-help]", root)) attachInfo(el, esc(el.dataset.help));
}

["#cfg-form", "#entry-form", '#tk [data-step="3"]', "#pb thead"].forEach(sel => initTooltips($(sel)));
document.addEventListener("keydown", e => { if (e.key === "Escape") hideTip(); });
addEventListener("scroll", hideTip, true);
document.addEventListener("click", e => { if (tipFor && !e.target.closest(".info")) hideTip(); });

// fill door station selects
for (const sel of $$(".ts-select")) {
  if (!sel.required) sel.append(new Option("–", "0"));
  for (let i = 1; i <= 9; i++) sel.append(new Option(String(i), String(i)));
}

// ------------------------------------------------------------------ Tabs

$$(".tabs button").forEach(btn => btn.addEventListener("click", () => {
  $$(".tabs button").forEach(b => b.setAttribute("aria-selected", b === btn));
  $$(".tab").forEach(t => t.classList.toggle("active", t.id === `tab-${btn.dataset.tab}`));
  history.replaceState(null, "", `#${btn.dataset.tab}`);
  try { localStorage.setItem("tab", btn.dataset.tab); } catch {}
  if (btn.dataset.tab === "help") renderHelp();
  if (btn.dataset.tab === "licenses") renderLicenses();
}));

// help: load mermaid only when the tab is shown (diagrams need a visible container)
let helpRendered = null;
function renderHelp() {
  helpRendered ??= new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = $("#tab-help").dataset.mermaid;
    s.onload = resolve;
    s.onerror = reject;
    document.head.append(s);
  }).then(() => {
    const dark = matchMedia("(prefers-color-scheme: dark)").matches;
    mermaid.initialize({
      startOnLoad: false, theme: dark ? "dark" : "neutral", securityLevel: "strict",
      themeVariables: { fontSize: "14px" },
    });
    return mermaid.run({ querySelector: "#tab-help pre.mermaid" });
  }).catch(err => {
    helpRendered = null;
    console.error(err);
  });
}
// licenses: determined by the server from the installed packages
let licensesLoaded = null;
function renderLicenses() {
  const body = $("#lic tbody");
  const texts = $("#lic-texts");
  licensesLoaded ??= (async () => {
    body.innerHTML = `<tr><td colspan="5" class="hint">${esc(t("js.lic.loading"))}</td></tr>`;
    const { components } = await api("GET", "/api/licenses");
    body.innerHTML = "";
    texts.innerHTML = "";
    components.forEach((c, i) => {
      const id = `lic-${i}`;
      const link = c.url ? `<a href="${esc(c.url)}" target="_blank" rel="noopener noreferrer">${esc(c.url.replace(/^https?:\/\//, ""))}</a>` : "";
      const own = i === 0 && c.kind === "python" ? ` <span class="tag on">${esc(t("js.lic.own"))}</span>` : "";
      body.insertAdjacentHTML("beforeend", `<tr>
        <td><a href="#${id}" data-lic="${id}">${esc(c.name)}</a>${own}</td>
        <td class="mono">${esc(c.version)}</td>
        <td><span class="tag${c.spdx ? "" : " undoc"}">${esc(c.license)}</span></td>
        <td>${esc(t(`js.lic.${c.kind}`))}</td>
        <td>${link}</td></tr>`);
      const extra = [];
      if (c.requires.length) extra.push(`<p class="hint">${esc(t("js.lic.requires"))}: ${c.requires.map(esc).join(", ")}</p>`);
      if (c.note) extra.push(`<p class="hint">${esc(c.note)}</p>`);
      if (c.bundled.length) extra.push(`<details><summary>${esc(t("js.lic.bundled"))} (${c.bundled.length})</summary><p class="mono small">${c.bundled.map(esc).join(", ")}</p></details>`);
      const lic = c.texts.map(x => `<details><summary>${esc(t("js.lic.text"))} · ${esc(x.file)}</summary><pre class="license-text">${esc(x.text)}</pre></details>`).join("");
      texts.insertAdjacentHTML("beforeend", `<section class="lic-item" id="${id}">
        <h3>${esc(c.name)} <span class="mono">${esc(c.version)}</span> <span class="tag${c.spdx ? "" : " undoc"}">${esc(c.license)}</span></h3>
        ${c.summary ? `<p>${esc(c.summary)}</p>` : ""}${extra.join("")}${lic}</section>`);
    });
    $$("#lic a[data-lic]").forEach(a => a.addEventListener("click", ev => {
      ev.preventDefault();
      const sec = $(`#${a.dataset.lic}`);
      sec.scrollIntoView({ behavior: "smooth", block: "start" });
      const d = $("details", sec);
      if (d) d.open = true;
    }));
  })().catch(err => {
    licensesLoaded = null;
    body.innerHTML = `<tr><td colspan="5" class="warn">${esc(t("js.lic.failed", { err: err.message }))}</td></tr>`;
  });
}

// table of contents: scroll instead of changing the hash (the hash selects the tab)
$$(".help-toc a").forEach(a => a.addEventListener("click", ev => {
  ev.preventDefault();
  $(a.getAttribute("href"))?.scrollIntoView({ behavior: "smooth", block: "start" });
}));
addEventListener("hashchange", () => $(`.tabs button[data-tab="${location.hash.slice(1)}"]`)?.click());
{
  let saved = location.hash.slice(1);
  if (!saved) try { saved = localStorage.getItem("tab"); } catch {}
  if (saved) $(`.tabs button[data-tab="${saved}"]`)?.click();
}

// --------------------------------------------------------- serial port

async function loadPorts() {
  const [{ ports, device }, st] = await Promise.all([api("GET", "/api/ports"), api("GET", "/api/status")]);
  const sel = $("#port");
  sel.innerHTML = "";
  if (st.sim) {
    sel.append(new Option(t("js.simulation"), "", true, true));
    sel.disabled = true;
    return;
  }
  sel.append(new Option(t("js.none_option"), ""));
  const known = new Set(ports.map(p => p.device));
  if (device && !known.has(device)) ports.unshift({ device, description: "" });
  for (const p of ports) sel.append(new Option(`${p.device} ${p.description || ""}`.trim(), p.device));
  sel.value = device || "";
}
$("#port").addEventListener("change", e => guarded(async () => {
  await api("POST", "/api/settings", { device: e.target.value });
  setStatus(t("js.port_set", { port: e.target.value || t("js.none") }));
}));
$("#btn-ports").addEventListener("click", () => guarded(loadPorts));

// --------------------------------------------------------- configuration

const cfgForm = $("#cfg-form");

function fillConfig(c) {
  for (const [key, value] of Object.entries(c)) {
    for (const el of $$(`[name="${key}"]`, cfgForm)) {
      if (el.type === "radio") el.checked = el.value === String(value);
      else if (el.type === "checkbox") el.checked = !!value;
      else el.value = value;
    }
  }
}

function readConfig() {
  const f = new FormData(cfgForm);
  return {
    anschlussart: f.get("anschlussart"),
    pin: f.get("pin"),
    tuergespraechszeit: f.get("tuergespraechszeit"),
    lokale_rufzeit: f.get("lokale_rufzeit"),
    externe_rufzeit: f.get("externe_rufzeit"),
    variante: Number(f.get("variante")),
    mithoeren: f.get("mithoeren") === "true",
    masterumleitung: f.get("masterumleitung"),
    master_anrufbeantworter: f.get("master_anrufbeantworter") === "on",
    masterumleitungsnummer: f.get("masterumleitungsnummer"),
  };
}

function checkConfigConflict() {
  const warn = $("#cfg-warn");
  const verzoegert = image?.konfiguration.masterumleitung === "verzoegert";
  const ab = image?.telefonbuch.some(e => e.ab_v1 || e.ab_v2);
  warn.hidden = !(verzoegert && ab);
  warn.textContent = t("js.cfg_conflict");
}

async function pushConfig() {
  if (!cfgForm.reportValidity()) throw new Error(t("js.fix_fields"));
  render(await api("PUT", "/api/config", readConfig()));
}
cfgForm.addEventListener("change", () => guarded(async () => {
  await pushConfig();
  setStatus(t("js.cfg_changed"));
}));

// ----------------------------------------------------------- phonebook

function isUsed(e) {
  return e.bezeichnung || e.nummer_v1 || e.nummer_v2 || e.gefangen || e.tuerstation;
}

function entryLabel(e) {
  return `${e.index}${e.bezeichnung ? " · " + e.bezeichnung : ""}`;
}

/** Phonebook entry whose call button matches this button code (5 address bytes). */
function entryForCode(code) {
  if (!image || !code) return null;
  return image.telefonbuch.find(e => e.gefangen && e.tastercode.slice(0, 14) === code.slice(0, 14)) || null;
}

function renderPhonebook() {
  const showAll = $("#pb-all").checked;
  const rows = image.telefonbuch
    .filter(e => showAll || isUsed(e))
    .map(e => `
      <tr class="${isUsed(e) ? "" : "free"}">
        <td>${e.index}</td>
        <td>${esc(e.bezeichnung) || "–"}</td>
        <td class="mono">${esc(e.nummer_v1)}</td>
        <td>${e.ab_v1 ? '<span class="tag on">AB</span>' : ""}</td>
        <td class="mono">${esc(e.nummer_v2)}</td>
        <td>${e.ab_v2 ? '<span class="tag on">AB</span>' : ""}</td>
        <td>${e.tuerstation || "–"}</td>
        <td><span class="tag ${e.gefangen ? "on" : ""}" title="${e.tastercode}">${e.gefangen ? t("js.captured") : t("js.free")}</span></td>
        <td class="row-actions">
          <button data-edit="${e.index}">${t("js.edit")}</button>
          <button data-learn="${e.index}">${t("js.button_dlg")}</button>
          <button data-del="${e.index}" class="danger" title="${t("js.delete_entry")}" aria-label="${t("js.delete_entry_n", { n: e.index })}">✕</button>
        </td>
      </tr>`);
  $("#pb tbody").innerHTML = rows.join("") ||
    `<tr class="free"><td colspan="9">${t("js.no_entries")}</td></tr>`;
}
$("#pb-all").addEventListener("change", renderPhonebook);

$("#pb tbody").addEventListener("click", e => {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.dataset.edit) openEntry(Number(b.dataset.edit));
  if (b.dataset.learn) openRuftaste(Number(b.dataset.learn));
  if (b.dataset.del && confirm(t("js.confirm_delete")))
    guarded(async () => render(await api("DELETE", `/api/phonebook/${b.dataset.del}`)));
});

async function putEntry(index, changes) {
  const e = { ...image.telefonbuch[index - 1], ...changes };
  render(await api("PUT", `/api/phonebook/${index}`, {
    bezeichnung: e.bezeichnung, nummer_v1: e.nummer_v1, nummer_v2: e.nummer_v2,
    ab_v1: e.ab_v1, ab_v2: e.ab_v2, tuerstation: Number(e.tuerstation), tastercode: e.tastercode,
  }));
}

const dlg = $("#entry-dlg");
const entryForm = $("#entry-form");
function openEntry(index) {
  const e = image.telefonbuch[index - 1];
  $("#entry-idx").textContent = index;
  entryForm.dataset.index = index;
  for (const [k, v] of Object.entries(e)) {
    const el = entryForm.elements[k];
    if (!el) continue;
    if (el.type === "checkbox") el.checked = v; else el.value = v;
  }
  dlg.showModal();
}
dlg.addEventListener("close", () => {
  if (dlg.returnValue !== "ok") return;
  const f = entryForm.elements;
  guarded(async () => {
    await putEntry(Number(entryForm.dataset.index), {
      bezeichnung: f.bezeichnung.value, nummer_v1: f.nummer_v1.value, nummer_v2: f.nummer_v2.value,
      ab_v1: f.ab_v1.checked, ab_v2: f.ab_v2.checked, tuerstation: f.tuerstation.value,
      tastercode: f.tastercode.value,
    });
    setStatus(t("js.entry_changed"));
  });
});

// ------------------------------------------------------ assign call button

const rtDlg = $("#rt-dlg");

function updateRtDtmf() {
  const idx = String(rtDlg.dataset.index).padStart(2, "0");
  $("#rt-dtmf").textContent = `R * 0 * PIN #   * 7 * ${$("#rt-ts").value} * ${idx} #`;
}

function openRuftaste(index) {
  const e = image.telefonbuch[index - 1];
  rtDlg.dataset.index = index;
  $("#rt-idx").textContent = entryLabel(e);
  $("#rt-ts").value = String(e.tuerstation || 1);
  $("#rt-cap-state").textContent = "";
  $("#rt-cap-take").hidden = true;
  $("#rt-cap").disabled = false;
  updateRtDtmf();
  rtDlg.showModal();
}
$("#rt-ts").addEventListener("change", updateRtDtmf);

$("#rt-fetch").addEventListener("click", () => guarded(async () => {
  const index = Number(rtDlg.dataset.index);
  await putEntry(index, { tuerstation: $("#rt-ts").value });
  await api("POST", `/api/gateway/ruftaste/${index}`);
  rtDlg.close();
  setStatus(t("js.fetching"));
}));

$("#rt-cap").addEventListener("click", () => guarded(async () => {
  const startedLog = !status?.log_active;
  if (startedLog) await api("POST", "/api/log/start");
  capture = { index: Number(rtDlg.dataset.index), startedLog, found: null };
  $("#rt-cap").disabled = true;
  $("#rt-cap-state").textContent = t("js.waiting_call");
}));

$("#rt-cap-take").addEventListener("click", () => guarded(async () => {
  if (!capture?.found) return;
  await putEntry(capture.index, { tastercode: capture.found, tuerstation: $("#rt-ts").value });
  await endCapture();
  rtDlg.close();
  setStatus(t("js.button_taken"));
}));

async function endCapture() {
  if (capture?.startedLog) await api("POST", "/api/log/stop").catch(() => {});
  capture = null;
}
$("#rt-close").addEventListener("click", () => rtDlg.close());
rtDlg.addEventListener("close", () => guarded(endCapture));

function onCaptured(code) {
  if (!capture || capture.found) return;
  capture.found = code;
  const known = entryForCode(code);
  $("#rt-cap-state").textContent = t("js.detected_code", { code: code.slice(0, 14) }) +
    (known ? t("js.already_entry", { entry: entryLabel(known) }) : "");
  $("#rt-cap-take").hidden = false;
}

// --------------------------------------- wizard: learn call buttons passively

const wizDlg = $("#wiz");
let wiz = null;  // {step, prepared, startedLog, found: Map(code -> row), order: [code]}

/** Wait for the end of a background job (independent of the global polling). */
async function waitJob(prevFinished) {
  for (;;) {
    const st = await api("GET", "/api/status");
    if (!st.job.busy && st.job.finished_at !== prevFinished) return st.job;
    await new Promise(r => setTimeout(r, 300));
  }
}

async function runJob(url, body) {
  const prev = (await api("GET", "/api/status")).job.finished_at;
  await api("POST", url, body);
  return waitJob(prev);
}

async function setLog(on) {
  await api("POST", on ? "/api/log/start" : "/api/log/stop");
  for (let i = 0; i < 30; i++) {  // wait until the serial port is free or busy
    const st = await api("GET", "/api/status");
    if (st.log_active === on) return;
    await new Promise(r => setTimeout(r, 200));
  }
}

function openWizard() {
  wiz = { step: 1, prepared: false, startedLog: false, found: new Map(), order: [] };
  $("#wz-c-conn").className = "";
  $("#wz-c-read").className = "";
  $("#wz-backup").disabled = true;
  $("#wz-prepare").disabled = false;
  $("#wz-found tbody").innerHTML = "";
  $("#wz-msg").textContent = "";
  showWizStep(1);
  wizDlg.showModal();
}

function showWizStep(n) {
  wiz.step = n;
  $$(".wiz-step", wizDlg).forEach(s => { s.hidden = Number(s.dataset.step) !== n; });
  $$(".steps li", wizDlg).forEach(li => {
    const s = Number(li.dataset.step);
    li.className = s < n ? "done" : s === n ? "current" : "";
  });
  $("#wz-back").hidden = n === 1 || n === 4;
  $("#wz-cancel").hidden = n === 4;
  $("#wz-next").textContent = { 1: t("js.next"), 2: t("js.next"), 3: t("js.save_gw"), 4: t("js.close") }[n];
  updateWizNext();
}

function wizAssignments() {
  return wiz.order.map(c => wiz.found.get(c)).filter(f => !f.ignored);
}

function wizProblems() {
  const errors = [], warnings = [];
  const seen = new Map();
  for (const f of wizAssignments()) {
    if (seen.has(f.index)) errors.push(t("js.dup_entry", { n: f.index }));
    seen.set(f.index, f.code);
    const e = image.telefonbuch[f.index - 1];
    if (e.gefangen && e.tastercode.slice(0, 14) !== f.code.slice(0, 14))
      warnings.push(t("js.replaces", { entry: entryLabel(e) }));
  }
  return { errors, warnings };
}

function updateWizNext() {
  const next = $("#wz-next");
  if (wiz.step === 1) next.disabled = !wiz.prepared;
  else if (wiz.step === 2) next.disabled = !wizAssignments().length || wizProblems().errors.length > 0;
  else next.disabled = false;
  if (wiz.step === 2) {
    const { errors } = wizProblems();
    $("#wz-msg").textContent = errors[0] || "";
  }
}

function nextFreeIndex() {
  const taken = new Set(wizAssignments().map(f => f.index));
  const free = image.telefonbuch.find(e => !isUsed(e) && !taken.has(e.index));
  return free ? free.index : 1;
}

function wizOnTuerruf(code) {
  if (!wiz || wiz.step !== 2) return;
  let f = wiz.found.get(code);
  if (f) {
    f.count++;
  } else {
    const known = entryForCode(code);
    f = {
      code, count: 1, ignored: false, known: known ? known.index : null,
      index: known ? known.index : nextFreeIndex(),
      ts: known && known.tuerstation ? known.tuerstation : 1,
      name: known ? known.bezeichnung : "",
      nummer: known ? known.nummer_v1 : "",
    };
    wiz.found.set(code, f);
    wiz.order.push(code);
  }
  f.last = new Date().toLocaleTimeString(LOCALE);
  let tr = $(`#wz-found tr[data-code="${code}"]`);
  if (!tr) {  // only append a new row – input in other rows is kept
    tr = wizRow(f);
    $("#wz-found tbody").append(tr);
  } else {
    $(".count", tr).textContent = `${f.count}× · ${f.last}`;
  }
  tr.classList.remove("flash");
  void tr.offsetWidth;  // restart the animation
  tr.classList.add("flash");
  $("#wz-empty").hidden = true;
  updateWizNext();
}

function wizRow(f) {
  const tr = document.createElement("tr");
  tr.dataset.code = f.code;
  const opts = image.telefonbuch.map(e =>
    `<option value="${e.index}">${esc(entryLabel(e))}${e.gefangen ? t("js.taken") : isUsed(e) ? "" : t("js.free_suffix")}</option>`).join("");
  const tsOpts = Array.from({ length: 9 }, (_, i) => `<option>${i + 1}</option>`).join("");
  tr.innerHTML = `
    <td class="mono">${f.code.slice(0, 14)}${f.known ? `<br><span class="tag on">${t("js.known_entry", { n: f.known })}</span>` : ""}</td>
    <td class="count">${f.count}× · ${f.last}</td>
    <td><select data-f="index" aria-label="${t("js.entry")}">${opts}</select></td>
    <td><select data-f="ts" aria-label="${t("js.door_station")}">${tsOpts}</select></td>
    <td><input data-f="name" maxlength="20" value="${esc(f.name)}" aria-label="${t("js.name")}"></td>
    <td><input data-f="nummer" maxlength="24" inputmode="tel" pattern="[0-9*#PFf]{0,24}" value="${esc(f.nummer)}" aria-label="${t("js.number_v1")}"></td>
    <td><button data-f="ignore"></button></td>`;
  $("[data-f=index]", tr).value = String(f.index);
  $("[data-f=ts]", tr).value = String(f.ts);
  setRowIgnored(tr, f);
  return tr;
}

function setRowIgnored(tr, f) {
  tr.classList.toggle("ignored", f.ignored);
  $$("select, input", tr).forEach(el => { el.disabled = f.ignored; });
  $("[data-f=ignore]", tr).textContent = f.ignored ? t("js.add_again") : t("js.discard");
}

function renderWizFound() {
  $("#wz-found tbody").replaceChildren(...wiz.order.map(c => wizRow(wiz.found.get(c))));
  $("#wz-empty").hidden = wiz.order.length > 0;
  updateWizNext();
}

$("#wz-found tbody").addEventListener("change", e => {
  const tr = e.target.closest("tr");
  const f = wiz.found.get(tr.dataset.code);
  const k = e.target.dataset.f;
  if (k === "index" || k === "ts") f[k] = Number(e.target.value);
  else f[k] = e.target.value;
  updateWizNext();
});
$("#wz-found tbody").addEventListener("click", e => {
  const b = e.target.closest("[data-f=ignore]");
  if (!b) return;
  const tr = b.closest("tr");
  const f = wiz.found.get(tr.dataset.code);
  f.ignored = !f.ignored;
  setRowIgnored(tr, f);
  updateWizNext();
});

$("#wz-prepare").addEventListener("click", () => guarded(async () => {
  $("#wz-prepare").disabled = true;
  try {
    if (status?.log_active) await setLog(false);
    $("#wz-c-conn").className = "busy";
    let job = await runJob("/api/gateway/version");
    if (job.error) { $("#wz-c-conn").className = "fail"; throw new Error(job.error); }
    $("#wz-c-conn").className = "ok";
    $("#wz-c-read").className = "busy";
    job = await runJob("/api/gateway/read");
    if (job.error) { $("#wz-c-read").className = "fail"; throw new Error(job.error); }
    $("#wz-c-read").className = "ok";
    render(await api("GET", "/api/image"));
    wiz.prepared = true;
    $("#wz-backup").disabled = false;
    $("#wz-msg").textContent = t("js.ready_backup");
  } finally {
    $("#wz-prepare").disabled = wiz.prepared;
    updateWizNext();
  }
}));
$("#wz-backup").addEventListener("click", () => download("/api/export/bin"));

$("#wz-back").addEventListener("click", () => guarded(async () => {
  if (wiz.step === 3) { await setLog(true); wiz.startedLog = true; }
  showWizStep(wiz.step - 1);
}));

$("#wz-next").addEventListener("click", () => guarded(async () => {
  const next = $("#wz-next");
  next.disabled = true;
  try {
    if (wiz.step === 1) {
      if (!status?.log_active) { await setLog(true); wiz.startedLog = true; }
      showWizStep(2);
      renderWizFound();
    } else if (wiz.step === 2) {
      if ($$("#wz-found input:invalid").length) throw new Error(t("js.number_chars"));
      const { warnings } = wizProblems();
      $("#wz-summary").innerHTML = wizAssignments().map(f =>
        `<li>${t("js.wz_line", { code: `<span class="mono">${f.code.slice(0, 14)}</span>`, n: f.index })}` +
        `${f.name ? ` „${esc(f.name)}“` : ""}${t("js.door_station_n", { n: f.ts })}` +
        `${f.nummer ? t("js.number_n", { nr: esc(f.nummer) }) : ""}` +
        `${f.known === f.index ? ` <span class="hint">${t("js.already_assigned")}</span>` : ""}</li>`).join("");
      $("#wz-warn").hidden = !warnings.length;
      $("#wz-warn").innerHTML = warnings.map(esc).join("<br>");
      showWizStep(3);
    } else if (wiz.step === 3) {
      $("#wz-msg").textContent = t("js.saving");
      await setLog(false);
      wiz.startedLog = false;
      for (const f of wizAssignments()) {
        const changes = { tastercode: f.code, tuerstation: f.ts };
        if (f.name) changes.bezeichnung = f.name;
        if (f.nummer) changes.nummer_v1 = f.nummer;
        await putEntry(f.index, changes);
      }
      const job = await runJob("/api/gateway/write", { part: "telefonbuch" });
      render(await api("GET", "/api/image"));
      $("#wz-result").textContent = job.error
        ? t("js.save_failed_pb", { err: job.error })
        : t("js.wz_saved", { n: wizAssignments().length });
      $("#wz-result").className = job.error ? "warn" : "";
      $("#wz-msg").textContent = "";
      showWizStep(4);
    } else {
      wizDlg.close();
    }
  } finally {
    if (wiz) updateWizNext();
  }
}));

$("#wz-cancel").addEventListener("click", () => wizDlg.close());
wizDlg.addEventListener("close", () => guarded(async () => {
  if (wiz?.startedLog) await setLog(false);
  wiz = null;
}));

// ------------------------------------- wizard: connect to PBX

const tkDlg = $("#tk");
let tk = null;  // {step, prepared}

function tkType() { return $('input[name="tk-type"]:checked', tkDlg).value; }
function tkMode() { return $('input[name="tk-mode"]:checked', tkDlg).value; }

function tkApplyType() {
  const fritz = tkType() === "fritz";
  $$(".fritz", tkDlg).forEach(el => { el.hidden = !fritz; });
  $$(".andere", tkDlg).forEach(el => { el.hidden = fritz; });
  if (fritz && !$("#tk-group").value) $("#tk-group").value = "**9";
}
function tkApplyMode() {
  $$("[data-mode]", tkDlg).forEach(el => { el.hidden = el.dataset.mode !== tkMode(); });
  tkUpdateNext();
}
$$('input[name="tk-type"]', tkDlg).forEach(r => r.addEventListener("change", tkApplyType));
$$('input[name="tk-mode"]', tkDlg).forEach(r => r.addEventListener("change", tkApplyMode));
$("#tk-wired").addEventListener("change", () => tkUpdateNext());
tkDlg.addEventListener("input", () => tkUpdateNext());

function openTkWizard() {
  tk = { step: 1, prepared: false };
  $("#tk-c-conn").className = "";
  $("#tk-c-read").className = "";
  $("#tk-prepare").disabled = false;
  $("#tk-wired").checked = false;
  $("#tk-msg").textContent = "";
  tkApplyType();
  tkApplyMode();
  tkShow(1);
  tkDlg.showModal();
}

function tkShow(n) {
  tk.step = n;
  $$(".wiz-step", tkDlg).forEach(s => { s.hidden = Number(s.dataset.step) !== n; });
  $$(".steps li", tkDlg).forEach(li => {
    const s = Number(li.dataset.step);
    li.className = s < n ? "done" : s === n ? "current" : "";
  });
  $("#tk-back").hidden = n === 1 || n === 5;
  $("#tk-cancel").hidden = n === 5;
  $("#tk-next").textContent = { 4: t("js.save_gw"), 5: t("js.close") }[n] || t("js.next");
  tkUpdateNext();
}

function tkLearned() {
  return image.telefonbuch.filter(e => e.gefangen);
}

function tkFillStep2() {
  const learned = tkLearned();
  const c = image.konfiguration;
  if (!$("#tk-group").value && c.masterumleitungsnummer) $("#tk-group").value = c.masterumleitungsnummer;
  $("#tk-entries tbody").innerHTML = learned.map(e => `<tr data-index="${e.index}">
      <td>${e.index}</td><td>${esc(e.bezeichnung) || "–"}</td><td>${e.tuerstation || "–"}</td>
      <td><input data-nr inputmode="tel" maxlength="24" pattern="[0-9*#PFf]{1,24}" value="${esc(e.nummer_v1)}"
        aria-label="${t("js.number_for", { n: e.index })}"></td></tr>`).join("") ||
    `<tr><td colspan="4" class="hint">${t("js.no_learned")}</td></tr>`;
  $("#tk-learned").innerHTML = learned.length
    ? t("js.n_learned", { n: learned.length })
    : `<span class="warn">${t("js.none_learned_warn")}</span>`;
  $("[value=einzeln]", tkDlg).disabled = !learned.length;
  if (!learned.length) $("[value=alle]", tkDlg).checked = true;
  tkApplyMode();
}

function tkFillStep3() {
  const c = image.konfiguration;
  $("#tk-ring").value = String(Number(c.externe_rufzeit) || 30);
  $("#tk-talk").value = String(Number(c.tuergespraechszeit) || 60);
  $("#tk-pin").value = c.pin;
}

function tkValid(sel) {
  return $$(`${sel} input`, tkDlg).filter(el => !el.closest("[hidden]")).every(el => el.checkValidity());
}

function tkUpdateNext() {
  if (!tk) return;
  const next = $("#tk-next");
  const ok = {
    1: tk.prepared && $("#tk-wired").checked,
    2: tkMode() === "alle" ? $("#tk-group").checkValidity() && !!$("#tk-group").value
                           : tkValid('[data-mode="einzeln"]'),
    3: tkValid('[data-step="3"]') && [Number($("#tk-ring").value), Number($("#tk-talk").value)].every(v => v >= 1 && v <= 120),
  }[tk.step];
  next.disabled = ok === false;
  $("#tk-pin-warn").hidden = $("#tk-pin").value !== "0000";
}

/** Target configuration (based on the loaded state). */
function tkTargetConfig() {
  const c = { ...image.konfiguration };
  c.anschlussart = "nebenstelle";
  c.externe_rufzeit = String(Number($("#tk-ring").value)).padStart(3, "0");
  c.tuergespraechszeit = String(Number($("#tk-talk").value)).padStart(3, "0");
  c.pin = $("#tk-pin").value;
  if (tkMode() === "alle") {
    c.masterumleitung = "sofort";
    c.masterumleitungsnummer = $("#tk-group").value;
    c.master_anrufbeantworter = false;
  } else {
    c.masterumleitung = "aus";
    c.variante = 1;
  }
  return c;
}

function tkEntryNumbers() {
  if (tkMode() !== "einzeln") return [];
  return $$("#tk-entries tr[data-index]").map(tr => ({ index: Number(tr.dataset.index), nr: $("[data-nr]", tr).value }));
}

const CFG_KEYS = ["anschlussart", "externe_rufzeit", "tuergespraechszeit", "pin", "masterumleitung",
  "masterumleitungsnummer", "master_anrufbeantworter", "variante"];

/** Configuration value for display (internal values like "sofort" -> label). */
function cfgValue(k, v) {
  if (k === "pin") return "••••";
  const key = `js.val.${v}`;
  return key in I18N ? t(key) : String(v ?? "");
}

function tkFillSummary() {
  const old = image.konfiguration, neu = tkTargetConfig();
  const items = CFG_KEYS.filter(k => String(old[k]) !== String(neu[k])).map(k =>
    `<li>${t("js.lbl." + k)}: <span class="old">${esc(cfgValue(k, old[k])) || "–"}</span> → ` +
    `<strong>${esc(k === "pin" ? neu[k] : cfgValue(k, neu[k]))}</strong></li>`);
  for (const { index, nr } of tkEntryNumbers()) {
    const e = image.telefonbuch[index - 1];
    if (e.nummer_v1 !== nr) items.push(`<li>${t("js.entry_number_change", { entry: esc(entryLabel(e)) })} <span class="old">${esc(e.nummer_v1) || "–"}</span> → <strong>${esc(nr)}</strong></li>`);
  }
  $("#tk-summary").innerHTML = items.join("") || `<li>${t("js.no_changes")}</li>`;
  const warns = [];
  if (!tkLearned().length) warns.push(t("js.warn_unlearned"));
  if (neu.pin === "0000") warns.push(t("js.warn_pin"));
  $("#tk-warn").hidden = !warns.length;
  $("#tk-warn").innerHTML = warns.map(esc).join("<br>");
}

$("#tk-prepare").addEventListener("click", () => guarded(async () => {
  $("#tk-prepare").disabled = true;
  try {
    if (status?.log_active) await setLog(false);
    $("#tk-c-conn").className = "busy";
    let job = await runJob("/api/gateway/version");
    if (job.error) { $("#tk-c-conn").className = "fail"; throw new Error(job.error); }
    $("#tk-c-conn").className = "ok";
    $("#tk-c-read").className = "busy";
    job = await runJob("/api/gateway/read");
    if (job.error) { $("#tk-c-read").className = "fail"; throw new Error(job.error); }
    $("#tk-c-read").className = "ok";
    render(await api("GET", "/api/image"));
    tk.prepared = true;
  } finally {
    $("#tk-prepare").disabled = tk.prepared;
    tkUpdateNext();
  }
}));

$("#tk-back").addEventListener("click", () => tkShow(tk.step - 1));
$("#tk-cancel").addEventListener("click", () => tkDlg.close());
tkDlg.addEventListener("close", () => { tk = null; });

$("#tk-next").addEventListener("click", () => guarded(async () => {
  if (tk.step === 1) { tkFillStep2(); tkShow(2); return; }
  if (tk.step === 2) { tkFillStep3(); tkShow(3); return; }
  if (tk.step === 3) { tkFillSummary(); tkShow(4); return; }
  if (tk.step === 5) { tkDlg.close(); return; }
  // step 4: save
  $("#tk-next").disabled = true;
  $("#tk-msg").textContent = t("js.saving");
  try {
    render(await api("PUT", "/api/config", tkTargetConfig()));
    const numbers = tkEntryNumbers();
    for (const { index, nr } of numbers) await putEntry(index, { nummer_v1: nr });
    const job = await runJob("/api/gateway/write", { part: numbers.length ? "alles" : "konfiguration" });
    render(await api("GET", "/api/image"));
    $("#tk-result").textContent = job.error
      ? t("js.save_failed", { err: job.error })
      : t("js.tk_saved");
    $("#tk-result").className = job.error ? "warn" : "";
    const own = $("#tk-own").value;
    $("#tk-test-own").hidden = !own;
    if (own) $("#tk-test-own").innerHTML = t("js.tk_own", { own: esc(own) });
    tkShow(5);
  } finally {
    $("#tk-msg").textContent = "";
    if (tk) tkUpdateNext();
  }
}));

// ------------------------------------ PBX connection test

const ttDlg = $("#tt");
let tt1 = null;  // {orig, target}
let tt2 = null;  // {startedLog, ring, dial, timer}

function ttResult(id, ok, html) {
  const el = $(id);
  el.hidden = false;
  el.className = `result ${ok === true ? "ok" : ok === false ? "bad" : ""}`;
  el.innerHTML = html;
}

function openTtest() {
  tt1 = null;
  $("#tt1-start-box").hidden = false;
  $("#tt1-run").hidden = true;
  $("#tt1-result").hidden = true;
  ttReset2();
  $("#tt-msg").textContent = "";
  ttDlg.showModal();
}

// ---- test 1: PBX -> gateway (switch the variant by phone, then read back)

$("#tt1-start").addEventListener("click", () => guarded(async () => {
  $("#tt1-result").hidden = true;
  $("#tt1-start").disabled = true;
  try {
    if (status?.log_active) await setLog(false);
    $("#tt-msg").textContent = t("js.loading_state");
    const job = await runJob("/api/gateway/read");
    if (job.error) throw new Error(job.error);
    render(await api("GET", "/api/image"));
    const c = image.konfiguration;
    if (c.anschlussart !== "nebenstelle") {
      ttResult("#tt1-result", false, t("js.tt1_amt"));
      return;
    }
    tt1 = { orig: c.variante, target: c.variante === 1 ? 2 : 1 };
    $("#tt1-code").textContent = `* 3 * ${tt1.target} #`;
    const own = $("#tk-own").value;
    $("#tt1-own").textContent = own ? ` (${own})` : "";
    $("#tt1-start-box").hidden = true;
    $("#tt1-run").hidden = false;
  } finally {
    $("#tt1-start").disabled = false;
    $("#tt-msg").textContent = "";
  }
}));

$("#tt1-cancel").addEventListener("click", () => {
  tt1 = null;
  $("#tt1-run").hidden = true;
  $("#tt1-start-box").hidden = false;
});

$("#tt1-check").addEventListener("click", () => guarded(async () => {
  $("#tt1-check").disabled = true;
  try {
    $("#tt-msg").textContent = t("js.reading_gw");
    let job = await runJob("/api/gateway/read");
    if (job.error) throw new Error(job.error);
    render(await api("GET", "/api/image"));
    if (image.konfiguration.variante !== tt1.target) {
      ttResult("#tt1-result", false, t("js.tt1_fail", { v: image.konfiguration.variante }));
      return;
    }
    // success – switch the variant back
    $("#tt-msg").textContent = t("js.restoring");
    render(await api("PUT", "/api/config", { ...image.konfiguration, variante: tt1.orig }));
    job = await runJob("/api/gateway/write", { part: "konfiguration" });
    render(await api("GET", "/api/image"));
    ttResult("#tt1-result", true, t("js.tt1_ok") + (job.error
      ? t("js.tt1_restore_fail", { err: esc(job.error), v: tt1.orig })
      : t("js.tt1_restored", { v: tt1.orig })));
    $("#tt1-run").hidden = true;
    $("#tt1-start-box").hidden = false;
    tt1 = null;
  } finally {
    $("#tt1-check").disabled = false;
    $("#tt-msg").textContent = "";
  }
}));

// ---- test 2: gateway -> PBX (trigger a door call, wait for "T: DIAL" in the log)

function ttReset2() {
  if (tt2?.timer) clearTimeout(tt2.timer);
  $("#tt2-steps").hidden = true;
  $$("#tt2-steps li").forEach(li => { li.className = ""; });
  $("#tt2-c-ring").textContent = t("js.tt2_ring");
  $("#tt2-c-known").textContent = t("js.tt2_known");
  $("#tt2-c-dial").textContent = t("js.tt2_dial");
  $("#tt2-ask").hidden = true;
  $("#tt2-result").hidden = true;
  $("#tt2-start").hidden = false;
  $("#tt2-stop").hidden = true;
}

async function ttEnd2(ok, html) {
  if (!tt2) return;
  clearTimeout(tt2.timer);
  const startedLog = tt2.startedLog;
  tt2 = null;
  $("#tt2-ask").hidden = true;
  $("#tt2-start").hidden = false;
  $("#tt2-stop").hidden = true;
  if (html) ttResult("#tt2-result", ok, html);
  if (startedLog) await setLog(false).catch(() => {});
}

function ttArm(ms, html) {
  clearTimeout(tt2.timer);
  tt2.timer = setTimeout(() => guarded(() => ttEnd2(false, html)), ms);
}

$("#tt2-start").addEventListener("click", () => guarded(async () => {
  ttReset2();
  if (!image.telefonbuch.some(e => e.gefangen)) {
    ttResult("#tt2-result", false, t("js.tt2_unlearned"));
    return;
  }
  const startedLog = !status?.log_active;
  if (startedLog) await setLog(true);
  tt2 = { startedLog, ring: null, dial: null, timer: null };
  $("#tt2-steps").hidden = false;
  $("#tt2-c-ring").className = "busy";
  $("#tt2-start").hidden = true;
  $("#tt2-stop").hidden = false;
  ttArm(90000, t("js.tt2_noring"));
}));

$("#tt2-stop").addEventListener("click", () => guarded(() => ttEnd2(null, t("js.tt2_aborted"))));

function ttOnLine(l) {
  if (!tt2) return;
  if (l.tuerruf && !tt2.ring) {
    tt2.ring = l.tuerruf;
    $("#tt2-c-ring").className = "ok";
    $("#tt2-c-ring").textContent = t("js.tt2_rang", { code: l.tuerruf.slice(0, 14) });
    const e = entryForCode(l.tuerruf);
    if (!e) {
      $("#tt2-c-known").className = "fail";
      guarded(() => ttEnd2(false, t("js.tt2_notlearned")));
      return;
    }
    $("#tt2-c-known").className = "ok";
    $("#tt2-c-known").textContent = t("js.tt2_isknown", { entry: entryLabel(e) });
    $("#tt2-c-dial").className = "busy";
    ttArm(20000, t("js.tt2_nodial"));
  } else if (l.typ === "T" && tt2.ring && !tt2.dial) {
    if (l.roh.includes("LOCAL")) {
      $("#tt2-c-dial").className = "fail";
      guarded(() => ttEnd2(false, t("js.tt2_local")));
      return;
    }
    const idx = parseInt(l.roh.slice(9, 11), 16);
    const nr = l.roh.includes(" - ") ? l.roh.split(" - ")[1].trim() : "?";
    tt2.dial = nr;
    clearTimeout(tt2.timer);
    $("#tt2-c-dial").className = "ok";
    $("#tt2-c-dial").textContent = t("js.tt2_dials", { nr, what: idx ? t("js.entry_n", { n: idx }) : t("js.master") });
    $("#tt2-ask").hidden = false;
  }
}

$("#tt2-yes").addEventListener("click", () => guarded(() => ttEnd2(true, t("js.tt2_ok"))));
$("#tt2-no").addEventListener("click", () => guarded(() => ttEnd2(false,
  t("js.tt2_no", { nr: esc(tt2?.dial ?? "") }))));

$("#tt-close").addEventListener("click", () => ttDlg.close());
ttDlg.addEventListener("close", () => guarded(() => ttEnd2(null)));

// ---------------------------------------------- assign door call from the log

const asDlg = $("#as-dlg");
function openAssign(code) {
  $("#as-code").textContent = code.slice(0, 14);
  asDlg.dataset.code = code;
  const sel = $("#as-index");
  sel.innerHTML = "";
  for (const e of image.telefonbuch) {
    sel.append(new Option(`${entryLabel(e)}${e.gefangen ? t("js.taken") : ""}`, e.index));
  }
  const free = image.telefonbuch.find(e => !e.gefangen);
  if (free) sel.value = free.index;
  asDlg.showModal();
}
asDlg.addEventListener("close", () => {
  if (asDlg.returnValue !== "ok") return;
  const f = $("#as-form").elements;
  guarded(async () => {
    await putEntry(Number(f.index.value), { tastercode: asDlg.dataset.code, tuerstation: f.tuerstation.value });
    setStatus(t("js.assigned"));
  });
});

// ---------------------------------------------------------------- log

const TYP = { S: t("js.typ.S"), E: t("js.typ.E"), T: t("js.typ.T") };

function logVisible(l) {
  const f = $("#log-filter").value;
  if (f === "alle") return true;
  if (f === "tuerruf") return !!l.tuerruf;
  return l.typ === f;
}

function logRow(l) {
  let book = "";
  if (l.tuerruf) {
    const e = entryForCode(l.tuerruf);
    book = e ? `<span class="tag on">${esc(entryLabel(e))}</span>`
             : `<button data-assign="${l.tuerruf}">${t("js.assign")}</button>`;
  }
  const typ = l.typ ? `<span class="tag typ-${l.typ}">${TYP[l.typ]}</span>` : "";
  return `<tr class="${l.typ ? "" : "msg"}"><td class="mono">${esc(l.zeit.slice(11))}</td><td>${typ}</td>` +
    `<td class="mono raw">${esc(l.roh)}</td><td>${esc(l.text)}</td><td>${book}</td></tr>`;
}

function renderLog() {
  $("#log tbody").innerHTML = logLines.filter(logVisible).map(logRow).join("");
  $("#log").classList.toggle("hide-raw", !$("#log-raw").checked);
  if ($("#log-scroll").checked) $("#log-wrap").scrollTop = $("#log-wrap").scrollHeight;
}
$("#log-filter").addEventListener("change", renderLog);
$("#log-raw").addEventListener("change", renderLog);
$("#log tbody").addEventListener("click", e => {
  const b = e.target.closest("[data-assign]");
  if (b) openAssign(b.dataset.assign);
});

let lastGatewayLine = 0;  // time of the last line from the gateway (for the idle hint)
$("#btn-log-ping").addEventListener("click", () => guarded(async () => {
  await api("POST", "/api/log/ping");
  setStatus(t("js.ping_sent"));
}));

$("#btn-log").addEventListener("click", () => guarded(async () => {
  await api("POST", status?.log_active ? "/api/log/stop" : "/api/log/start");
}));

async function pollLog() {
  const { lines, next } = await api("GET", `/api/log?since=${logNext}`);
  if (next < logNext) { logLines = []; logNext = 0; renderLog(); return; }
  logNext = next;
  if (!lines.length) return;
  logLines.push(...lines);
  if (logLines.length > 5000) logLines = logLines.slice(-5000);
  for (const l of lines) {
    if (l.roh) lastGatewayLine = Date.now();
    if (l.tuerruf) { onCaptured(l.tuerruf); wizOnTuerruf(l.tuerruf); }
    ttOnLine(l);
  }
  const visible = lines.filter(logVisible);
  if (visible.length) {
    $("#log tbody").insertAdjacentHTML("beforeend", visible.map(logRow).join(""));
    if ($("#log-scroll").checked) $("#log-wrap").scrollTop = $("#log-wrap").scrollHeight;
  }
}

// --------------------------------------------------------- phone codes

// [action key, code (key or literal), note key, undocumented]
const CODES = [
  ["js.code.unlock", "R * 0 * PIN #", "js.code.unlock.n", false],
  ["js.code.number", "js.code.number.c", "js.code.number.n", false],
  ["js.code.button", "js.code.button.c", "js.code.button.n", false],
  ["js.code.passive", "js.code.passive.c", "js.code.passive.n", true],
  ["js.code.type", "* 3 * K #", "js.code.type.n", false],
  ["js.code.local", "* 4 * ZZZ #", "js.code.secs3", false],
  ["js.code.external", "* 5 * ZZZ #", "js.code.secs", false],
  ["js.code.talk", "* 6 * ZZZ #", "js.code.secs", false],
  ["js.code.listen", "* 8 * K #", "js.code.onoff", true],
  ["js.code.pin", "js.code.pin.c", "js.code.pin.n", false],
  ["js.code.master_nr", "js.code.master_nr.c", "js.code.master_nr.n", false],
  ["js.code.master_ab", "js.code.master_ab.c", "js.code.master_ab.n", true],
  ["js.code.master", "R * 2 * K #", "js.code.master.n", false],
  ["js.code.variant", "R * 3 * K #", "js.code.variant.n", false],
  ["js.code.actuator", "js.code.actuator.c", "js.code.actuator.n", false],
  ["js.code.door", "# 0", "js.code.door.n", false],
  ["js.code.door2", "js.code.door2.c", "js.code.door2.n", false],
  ["js.code.reset", "R * 9 * 19 28 37 46 55 #", "js.code.reset.n", false],
];
$("#codes tbody").innerHTML = CODES.map(([what, code, note, undoc]) =>
  `<tr><td>${esc(t(what))} ${undoc ? `<span class="tag undoc">${esc(t("js.undoc"))}</span>` : ""}</td>` +
  `<td class="mono">${esc(t(code))}</td><td>${esc(t(note))}</td></tr>`).join("");

// ------------------------------------------------------------ Rendering

function render(img) {
  image = img;
  fillConfig(img.konfiguration);
  renderPhonebook();
  checkConfigConflict();
  renderLog();  // update phonebook assignments in the log
  $("#src-hint").textContent = img.loaded ? t("js.src_loaded") : t("js.src_default");
}

function renderVersion(v) {
  const badge = $("#gw-badge");
  if (!v) {
    badge.textContent = connFailed ? t("js.no_connection") : t("js.not_checked");
    badge.className = connFailed ? "badge bad" : "badge";
    badge.title = "";
    return;
  }
  $("#fw-koppler").textContent = v.bootloader_only ? t("js.bl_only") : (v.koppler || v.text);
  $("#fw-pic").textContent = v.pic || t("js.not_present");
  let state = t("js.fw_ok"), cls = "badge ok";
  if (v.bootloader_only) { state = t("js.fw_bl"); cls = "badge bad"; }
  else if (!v.has_bustreiber) { state = t("js.fw_nobt"); cls = "badge warn"; }
  $("#fw-state").textContent = state;
  badge.className = cls;
  badge.textContent = v.bootloader_only ? t("js.bootloader") : `TK-Gateway ${v.koppler || "?"}${v.pic ? " · PIC " + v.pic : ""}`;
  badge.title = v.text;
}

// --------------------------------------------------------------- actions

function download(url) {
  const a = document.createElement("a");
  a.href = url;
  document.body.append(a);
  a.click();
  a.remove();
}

async function upload(kind) {
  const input = $(kind === "bustreiber" ? "#bt-file" : "#fw-file");
  if (!input.files.length) throw new Error(t("js.select_file"));
  if (!confirm(t(kind === "bustreiber" ? "js.confirm_bt" : "js.confirm_fw", { file: input.files[0].name }))) return;
  const fd = new FormData();
  fd.append("datei", input.files[0]);
  fd.append("art", kind);
  await api("POST", "/api/gateway/firmware", fd);
}

const actions = {
  "read": () => api("POST", "/api/gateway/read"),
  "write-config": async () => { await pushConfig(); await api("POST", "/api/gateway/write", { part: "konfiguration" }); },
  "write-phonebook": () => api("POST", "/api/gateway/write", { part: "telefonbuch" }),
  "defaults": async () => {
    if (!confirm(t("js.confirm_defaults"))) return;
    render(await api("POST", "/api/config/werkseinstellungen"));
    setStatus(t("js.defaults_loaded"));
  },
  "pb-clear": async () => {
    if (!confirm(t("js.confirm_pb_clear"))) return;
    render(await api("DELETE", "/api/phonebook"));
    setStatus(t("js.pb_cleared"));
  },
  "import": () => $("#import-file").click(),
  "export-gtk": () => download("/api/export/gtk"),
  "export-gtb": () => download("/api/export/gtb"),
  "export-json": () => download("/api/export/json"),
  "export-bin": () => download("/api/export/bin"),
  "version": () => api("POST", "/api/gateway/version"),
  "bootloader-reset": async () => {
    if (!confirm(t("js.confirm_bl"))) return;
    await api("POST", "/api/gateway/bootloader-reset");
  },
  "wizard": () => openWizard(),
  "tk-wizard": () => openTkWizard(),
  "tk-test": () => openTtest(),
  "tk-test-from-wizard": () => { tkDlg.close(); openTtest(); },
  "wizard-from-tt": () => { ttDlg.close(); openWizard(); },
  "wizard-from-rt": async () => { rtDlg.close(); await endCapture(); openWizard(); },
  "fw-upload": () => upload("firmware"),
  "bt-upload": () => upload("bustreiber"),
  "log-download": () => download("/api/log/download"),
  "log-clear": async () => { await api("DELETE", "/api/log"); logLines = []; logNext = 0; renderLog(); },
};
document.addEventListener("click", e => {
  const b = e.target.closest("[data-action]");
  if (b) guarded(actions[b.dataset.action]);
});

$("#import-file").addEventListener("change", e => guarded(async () => {
  const fd = new FormData();
  fd.append("datei", e.target.files[0]);
  render(await api("POST", "/api/import", fd));
  setStatus(t("js.file_loaded", { file: e.target.files[0].name }));
  e.target.value = "";
}));

// ---------------------------------------------------------------- Status

// call buttons assigned in the working copy but not yet written to the gateway
function renderUnsaved(list) {
  const params = { n: list.length, list: list.join(", ") };
  for (const box of $$("[data-unsaved]")) {
    if ("onlyUnsaved" in box.dataset) box.hidden = !list.length;
    $(".unsaved-line", box).hidden = !list.length;
    $(".unsaved-count", box).textContent = t(list.length === 1 ? "js.unsaved.one" : "js.unsaved", params) +
      (status.log_active && box.closest("#tab-loggen") ? ` ${t("js.unsaved_log")}` : "");
  }
}

async function pollStatus() {
  status = await api("GET", "/api/status");
  const job = status.job;
  const busy = job.busy || status.log_active;
  $$(".dev, [data-learn]").forEach(b => { b.disabled = busy; });
  $("#btn-log").textContent = status.log_active ? t("js.stop") : t("js.start");
  $("#btn-log-ping").disabled = !status.log_active;
  if (!status.log_active) lastGatewayLine = 0;
  else if (!lastGatewayLine) lastGatewayLine = Date.now();
  $("#log-idle").hidden = !status.log_active || Date.now() - lastGatewayLine < 10000;
  $("#btn-log").disabled = job.busy;
  renderVersion(status.version);
  renderUnsaved(status.unsaved_buttons || []);

  if (job.busy) {
    const pct = job.total ? Math.round(100 * job.done / job.total) : 0;
    $("#bar").style.width = `${pct}%`;
    setStatus(job.total ? `${job.message} ${pct} %` : job.message);
  } else if (job.finished_at && job.finished_at !== lastJobFinished) {
    lastJobFinished = job.finished_at;
    $("#bar").style.width = job.error ? "0" : "100%";
    setStatus(job.error ? `${job.message}: ${job.error}` : job.message, !!job.error);
    if (job.kind === "version") {
      connFailed = !!job.error;
      renderVersion(status.version);
    }
    render(await api("GET", "/api/image"));
  } else if (status.log_active && !capture) {
    setStatus(t("js.logging"));
  }
}

async function tick() {
  try { await pollStatus(); await pollLog(); } catch (e) { setStatus(t("js.server_lost", { err: e.message }), true); }
  setTimeout(tick, 500);
}

guarded(async () => {
  await loadPorts();
  render(await api("GET", "/api/image"));
  status = await api("GET", "/api/status");
  lastJobFinished = status.job.finished_at;
  renderVersion(status.version);
  tick();
});
