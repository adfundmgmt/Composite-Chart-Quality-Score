/* ============================================================
   CCQS — modern fintech terminal (build-less, vanilla JS)
   ============================================================ */
(function () {
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];
  const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const isDark = () => document.documentElement.dataset.theme === "dark";
  const MONO_FONT = "Geist Mono, ui-monospace, SFMono-Regular, Menlo, monospace"; // canvas libs can't read CSS vars

  const f1 = (v) => (v == null ? "–" : Number(v).toFixed(1));
  const sgn = (v, d = 2) => (v == null ? "–" : (v >= 0 ? "+" : "") + Number(v).toFixed(d));
  const pct0 = (v) => (v == null ? "–" : Math.round(v) + "%");
  let _toastT; function showToast(msg) { const t = $("#toast"); if (!t) return; t.textContent = msg; t.classList.add("show"); clearTimeout(_toastT); _toastT = setTimeout(() => t.classList.remove("show"), 2400); }
  const histCache = {};
  async function loadHist(tk) { if (histCache[tk]) return histCache[tk]; try { const r = await fetch("data/history/" + tk + ".json", { cache: "no-cache" }); const j = r.ok ? await r.json() : []; histCache[tk] = j; return j; } catch (e) { return []; } }

  const GRADE = { S: "--g-s", A: "--g-a", B: "--g-b", C: "--g-c", D: "--g-d", E: "--g-f", F: "--g-f" };
  const gradeColor = (g) => "var(" + (GRADE[(g || "")[0]] || "--g-c") + ")";
  const GRANK = { S: 6, A: 5, B: 4, C: 3, D: 2, E: 1, F: 0 };
  const gradeRank = (g) => (GRANK[(g || "")[0]] != null ? GRANK[(g || "")[0]] : 3);
  const gradeHex = (g) => cssVar(GRADE[(g || "")[0]] || "--g-c");
  // Leadership tier — color ONLY the meaningful extremes; the ~480 middling names stay neutral grey.
  const TIER = { ELITE_LEADER: "--g-s", STRONG_LEADER: "--pos", ESTABLISHED_LEADER: "--g-a", EMERGING_LEADER: "--pos", STRONG_PERFORMER: "--muted", NEUTRAL: "--muted", UNCLASSIFIED: "--faint", DETERIORATING: "--g-d", WEAK_PERFORMER: "--neg", WEAK_LAGGARD: "--neg" };
  const tierColor = (k) => "var(" + (TIER[k] || "--muted") + ")";
  // Price state — green = trending, red = breaking down, orange = parabolic/exhausted; pauses stay neutral.
  const STATE = { TRENDING: "--pos", EXHAUSTION: "--g-d", PULLBACK: "--muted", CONSOLIDATING: "--muted", INDETERMINATE: "--faint", DETERIORATING: "--neg" };
  const stateColor = (k) => "var(" + (STATE[k] || "--muted") + ")";
  // GICS sector colors (sector-ETF aligned) for the per-ticker sector dot
  const SECTOR_VAR = { "Information Technology": "--sec-it", "Health Care": "--sec-hc", "Financials": "--sec-fin", "Consumer Discretionary": "--sec-cd", "Communication Services": "--sec-comm", "Industrials": "--sec-ind", "Consumer Staples": "--sec-cs", "Energy": "--sec-en", "Utilities": "--sec-ut", "Materials": "--sec-mat", "Real Estate": "--sec-re", "Other": "--sec-other" };
  const secColor = (s) => "var(" + (SECTOR_VAR[s] || "--sec-other") + ")"; // themeable — light variants pass contrast on cream
  // Diverging weak→strong ramp through a neutral slate midpoint (no muddy yellow/brown).
  function heatRamp(t, dark) {
    const lo = dark ? [178, 66, 60] : [184, 58, 50], mid = dark ? [72, 80, 90] : [126, 134, 144], hi = dark ? [46, 150, 100] : [28, 128, 82];
    const a = t < 0.5 ? lo : mid, b = t < 0.5 ? mid : hi, k = t < 0.5 ? t / 0.5 : (t - 0.5) / 0.5;
    return [0, 1, 2].map((i) => Math.round(a[i] + (b[i] - a[i]) * k));
  }
  function pill(c, text, ft, fv, fl) {
    const lbl = (fl || text || "").replace(/"/g, "");
    const d = ft ? ` data-ft="${ft}" data-fv="${fv}" data-fl="${lbl}" title="Filter Leaders by ${lbl}"` : "";
    const neutral = c.includes("--muted") || c.includes("--faint"); // IBKR: labels are NEUTRAL text — green/red reserved for change (deltas), not categories
    return `<span class="pill-plain${neutral ? "" : " is-sig"}${ft ? " pill-f" : ""}"${d} style="color:${neutral ? "var(--muted)" : "var(--text)"}">${text ?? "–"}</span>`;
  }
  // Auto-scaled to the row's own range (+padding) so the SHAPE of the recent
  // CCQS trend is always visible — direction colored by net change.
  function sparkline(vals) {
    if (!vals || vals.length < 2) return "";
    const w = 70, h = 18, p = 3;
    let mn = Math.min(...vals), mx = Math.max(...vals), rng = mx - mn;
    if (rng < 0.5) rng = 0.5;
    const pad = rng * 0.22, lo = mn - pad, span = rng + 2 * pad;
    const y = (v) => (p + (1 - (v - lo) / span) * (h - 2 * p)).toFixed(1);
    const pts = vals.map((v, i) => `${(p + (i / (vals.length - 1)) * (w - 2 * p)).toFixed(1)},${y(v)}`).join(" ");
    const c = vals[vals.length - 1] >= vals[0] ? "var(--pos)" : "var(--neg)"; // green up / red down — conventional trend coloring
    const b = y(vals[0]); // D4: faint baseline at the starting level so slope reads against it
    return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><line x1="${p}" y1="${b}" x2="${w - p}" y2="${b}" stroke="var(--border2)" stroke-width=".5" stroke-dasharray="2 2"/><polyline points="${pts}" fill="none" stroke="${c}" stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round"/></svg>`;
  }
  function shortenTheme(name) {
    if (!name) return ""; name = String(name).replace(/ and /g, " & ");
    if (name.length <= 20) return name;
    const words = name.split(/\s+/); let out = "";
    for (const w of words) { if ((out ? out + " " + w : w).length > 20) break; out = out ? out + " " + w : w; }
    return (out || name.slice(0, 19)).replace(/\s+(&|of|the|for|in|on)$/i, "");
  }

  // state
  let DATA = null, DETAIL = null, gridApi = null, themesApi = null, heat = null;
  let trajChart = null, curHist = [], curPeriod = "1Y", curTicker = null;
  let activeGrade = "All", activeFilters = [], numFilters = [], themesInited = false;
  let compareSet = [], cmpChart = null;
  const CMP_TOKENS = ["--g-b", "--g-a", "--accent3", "--text"]; // V1: no amber (chrome-only); distinct data hues

  async function boot() {
    try { DATA = await fetch("data/core.json", { cache: "no-cache" }).then((r) => r.json()); }
    catch (e) { $("#loading").innerHTML = '<div style="text-align:center"><div>Could not load the CCQS feed.</div><a class="tool-btn" href="" style="display:inline-block;margin-top:12px;text-decoration:none">Retry</a></div>'; return; }
    initTheme();
    renderMeta(); renderStatusBar(); renderSectorLegend(); renderStatband(); renderGrid(); renderMovers(); renderOOS(); renderMethod();
    wireCmdline(); wireSearch(); wireNav(); wireViews(); wireCompare(); wireSplitter();
    $("#gradeLegend").innerHTML = [["S", "Elite"], ["A", "Strong"], ["B", "Solid"], ["C", "Neutral"], ["D", "Weak"], ["F", "Broken"]].map(([g, l]) => `<span class="gl"><i style="background:var(${GRADE[g] || "--g-c"})"></i>${g} <small>${l}</small></span>`).join("");
    ["#leaderChips", "#cmdMeta", "#leadersCount"].forEach((s) => { const el = $(s); if (el) el.setAttribute("aria-live", "polite"); });
    setTimeout(() => $("#loading").classList.add("hide"), 150);
  }

  function renderMeta() {
    $("#snapDate").textContent = DATA.snapshot;
    $("#cmdMeta").innerHTML = `<b>${DATA.snapshot}</b> · ${DATA.nScored.toLocaleString()} SCORED · LIVE`;
    $("#leadersCount").textContent = DATA.nScored.toLocaleString() + " names";
    $("#themesCount").textContent = DATA.themes.length + " themes";
  }

  function renderSectorLegend() {
    const el = $("#sectorLegend"); if (!el) return;
    const order = [["Information Technology", "Tech"], ["Financials", "Financials"], ["Health Care", "Health"], ["Consumer Discretionary", "Cons Disc"], ["Industrials", "Industrials"], ["Energy", "Energy"], ["Communication Services", "Comm"], ["Consumer Staples", "Staples"], ["Utilities", "Utilities"], ["Materials", "Materials"], ["Real Estate", "Real Estate"], ["Other", "Other"]];
    el.innerHTML = `<span class="sl-label">SECTORS</span>` + order.map(([full, abbr]) => `<span class="sl-item" data-ft="sec" data-fv="${full}" data-fl="${full}" title="Filter Leaders by ${full}"><i class="sec-dot" style="background:${secColor(full)}"></i>${abbr}</span>`).join("");
    el.addEventListener("click", (e) => { const it = e.target.closest("[data-ft]"); if (it) addFilter(it.dataset.ft, it.dataset.fv, it.dataset.fl); });
  }

  function renderStatusBar() {
    const f = $("#statusBar"); if (!f) return; const n = DATA.nScored.toLocaleString();
    f.innerHTML = `<span class="st-live"><i class="st-dot"></i>LIVE</span><span class="st-sep">·</span>SNAPSHOT <b>${DATA.snapshot}</b><span class="st-sep">·</span><b id="stCount">${n}</b> / ${n} names<span class="st-sep">·</span><b>${DATA.themes.length}</b> themes<span class="st-grow"></span><span class="st-keys"><b>⌘K</b> jump · <b>↵</b> inspect · <b>⎋</b> clear</span><span class="st-sep">·</span><span class="st-brand">CCQS ENGINE</span>`;
  }

  function renderStatband() {
    const s = DATA.stocks, n = s.length;
    const avg = s.reduce((a, x) => a + (x.ccqs || 0), 0) / n;
    const sorted = s.map((x) => x.ccqs || 0).sort((a, b) => a - b);
    const med = sorted[Math.floor(n / 2)];
    const gs = s.filter((x) => (x.grade || "")[0] === "S").length;
    const ga = s.filter((x) => (x.grade || "")[0] === "A").length;
    const adv = s.filter((x) => x.d1 > 0).length, dec = s.filter((x) => x.d1 < 0).length;
    const items = [
      ["Universe", n.toLocaleString(), ""],
      ["Avg CCQS", avg.toFixed(1), ""],
      ["Median", med.toFixed(1), ""],
      ["Grade S", gs, ""],
      ["Grade A", ga, ""],
      ["S/A Leaders", `${gs + ga}<small> ${(((gs + ga) / n) * 100).toFixed(0)}%</small>`, ""],
      ["Advancing", `${((adv / n) * 100).toFixed(0)}%<small> ${adv}</small>`, "pos"],
      ["Declining", `${((dec / n) * 100).toFixed(0)}%<small> ${dec}</small>`, "neg"],
      ["Themes", DATA.themes.length, ""],
    ];
    $("#statband").innerHTML = items.map(([l, v, c]) => `<div class="stat"><span class="stat-l">${l}</span><span class="stat-v ${c}">${v}</span></div>`).join("");
  }

  // ---- LEADERS GRID ------------------------------------------------------
  function ccqsRenderer(p) { return `<span class="ccqs-num">${f1(p.value)}</span>`; }
  function gradeRenderer(p) { const c = gradeColor(p.value); return `<span class="gchip" style="color:${c};background:color-mix(in srgb,${c} 18%,transparent)">${p.value || "–"}</span>`; } // full-spectrum grade chip
  function deltaRenderer(p) { if (p.value == null) return `<span class="delta" style="color:var(--faint)">–</span>`; const up = p.value >= 0; return `<span class="delta"><span class="da" style="color:${up ? "var(--pos)" : "var(--neg)"}">${up ? "▲" : "▼"}</span> ${sgn(p.value)}</span>`; } // neutral number, tiny colored arrow

  function renderGrid() {
    const cols = [
      { field: "t", headerName: "Ticker", pinned: "left", width: 102, cellClass: "cell-ticker", cellRenderer: (p) => `<span class="sec-dot" style="background:${secColor(p.data.sec)}" title="${p.data.sec || "—"}"></span>${p.data.t}` }, // grade-bar dropped — sector dot carries the only hue
      { field: "ccqs", headerName: "CCQS", width: 116, type: "rightAligned", cellRenderer: ccqsRenderer, sort: "desc", headerTooltip: "Composite Chart Quality Score, 0–100, graded S–F by daily cross-sectional quantile." },
      { field: "grade", headerName: "Grade", width: 74, cellRenderer: gradeRenderer },
      { headerName: "Trend 24d", width: 92, sortable: false, headerTooltip: "CCQS trend over the last 24 sessions (~5 weeks); auto-scaled per row to show shape.", cellRenderer: (p) => sparkline(p.data.spark), cellClass: "spark-cell" },
      { field: "theme", headerName: "Theme", width: 250, tooltipField: "theme", valueFormatter: (p) => (p.value || "").replace(/ and /g, " & "), cellStyle: { color: "var(--text)" } },
      { field: "tier", headerName: "Leadership", width: 150, headerTooltip: "Leadership tier from the relative-strength classifier (click a pill to filter).", cellRenderer: (p) => pill(tierColor(p.data.tierKey), p.value, "tier", p.data.tierKey, p.value) },
      { field: "state", headerName: "State", width: 144, headerTooltip: "Primary price-structure state (click a pill to filter).", cellRenderer: (p) => pill(stateColor(p.data.stateKey), p.value, "state", p.data.stateKey, p.value) },
      { field: "setup", headerName: "Setup", width: 124, tooltipField: "setup", cellStyle: { color: "var(--text)" } },
      { field: "d1", headerName: "Δ 1D", width: 88, type: "rightAligned", cellRenderer: deltaRenderer },
      { field: "d5", headerName: "Δ 5D", width: 88, type: "rightAligned", cellRenderer: deltaRenderer },
      { field: "d21", headerName: "Δ 21D", width: 92, type: "rightAligned", cellRenderer: deltaRenderer },
      { field: "rs", headerName: "RS", width: 70, type: "rightAligned", headerTooltip: "Relative Strength rating vs SPY (0–100 percentile).", valueFormatter: (p) => (p.value == null ? "–" : Math.round(p.value)), cellStyle: { color: "var(--text)" } },
    ];
    gridApi = agGrid.createGrid($("#grid"), {
      columnDefs: cols, rowData: DATA.stocks,
      defaultColDef: { sortable: true, resizable: true, suppressHeaderMenuButton: true },
      rowHeight: 26, headerHeight: 26, animateRows: false, enableBrowserTooltips: true, getRowId: (p) => p.data.t,
      overlayNoRowsTemplate: '<span class="grid-empty">No names match the current filters — clear to reset.</span>',
      onModelUpdated: () => { if (!gridApi) return; const n = gridApi.getDisplayedRowCount(); $("#leadersCount").textContent = n.toLocaleString() + " of " + DATA.stocks.length.toLocaleString() + " names"; const sc = $("#stCount"); if (sc) sc.textContent = n.toLocaleString(); if (n === 0) gridApi.showNoRowsOverlay(); else gridApi.hideOverlay(); },
      onCellKeyDown: (e) => { if (!(e.event && e.event.key === "Enter" && e.data)) return; const col = e.column && e.column.getColId && e.column.getColId(); if (col === "tier") addFilter("tier", e.data.tierKey, e.data.tier); else if (col === "state") addFilter("state", e.data.stateKey, e.data.state); else inspect(e.data.t); },
      rowSelection: "single", suppressCellFocus: false,
      onCellFocused: (e) => { if (!gridApi || e.rowIndex == null) return; const node = gridApi.getDisplayedRowAtIndex(e.rowIndex); if (node && node.data) { selRow(node); inspectSoon(node.data.t); } }, // linked inspector
      isExternalFilterPresent: () => activeGrade !== "All" || activeFilters.length > 0 || numFilters.length > 0,
      doesExternalFilterPass: filterPass,
    });
    $("#grid").addEventListener("click", (e) => {
      const pe = e.target.closest("[data-ft]");
      if (pe) { addFilter(pe.dataset.ft, pe.dataset.fv, pe.dataset.fl); return; } // pill filter
      const row = e.target.closest(".ag-row"); const id = row && row.getAttribute("row-id");
      if (id) { selRow(gridApi.getRowNode(id)); inspectSoon(id); } // single-click selects + inspects
    });
    gridApi.applyColumnState({ state: [{ colId: "ccqs", sort: "desc" }] });
    setTimeout(() => { if (!gridApi) return; const node = gridApi.getDisplayedRowAtIndex(0); if (node && node.data) { selRow(node); inspect(node.data.t); } }, 100); // auto-inspect top name

    $("#gradeSeg").innerHTML = ["All", "S", "A", "B"].map((g) => `<button data-g="${g}" class="${g === "All" ? "on" : ""}">${g}</button>`).join("");
    $$("#gradeSeg button").forEach((b) => b.addEventListener("click", () => { activeGrade = b.dataset.g; $$("#gradeSeg button").forEach((x) => x.classList.toggle("on", x === b)); gridApi.onFilterChanged(); }));
    $("#exportBtn").addEventListener("click", () => { gridApi.exportDataAsCsv({ fileName: `ccqs_leaders_${DATA.snapshot}.csv`, processCellCallback: (p) => (typeof p.value === "object" ? "" : p.value) }); showToast("Exported " + gridApi.getDisplayedRowCount() + " rows to CSV"); });
  }

  function filterPass(node) {
    if (activeGrade !== "All" && !(node.data.grade || "").startsWith(activeGrade)) return false;
    for (const nf of numFilters) { if (!numPass(node.data[nf.field], nf.op, nf.val)) return false; }
    const byType = {};
    activeFilters.forEach((f) => { (byType[f.type] = byType[f.type] || []).push(f.val); });
    for (const type in byType) {
      const field = type === "theme" ? "theme" : type === "tier" ? "tierKey" : type === "sec" ? "sec" : "stateKey";
      if (!byType[type].includes(node.data[field])) return false;
    }
    return true;
  }

  // ---- NUMERIC SCREEN (command-line expressions: ccqs>=80, rs>70) --------
  const NUM_RE = /^(ccqs|rs|d1|d5|d21|conf|ir)(>=|<=|>|<|==|=)(-?\d+\.?\d*)$/i;
  const OP_SYM = { ">=": "≥", "<=": "≤", ">": ">", "<": "<", "=": "=" };
  function numPass(a, op, b) { if (a == null) return false; switch (op) { case ">=": return a >= b; case "<=": return a <= b; case ">": return a > b; case "<": return a < b; default: return a === b; } }
  function parseCmdline(raw) {
    const nums = [], text = [];
    (raw || "").trim().split(/\s+/).forEach((tok) => { if (!tok) return; const m = tok.match(NUM_RE); if (m) nums.push({ field: m[1].toLowerCase(), op: m[2] === "==" ? "=" : m[2], val: parseFloat(m[3]) }); else text.push(tok); });
    return { nums, text: text.join(" ") };
  }
  function applyCmdline(raw) { if (!gridApi) return; const p = parseCmdline(raw); numFilters = p.nums; gridApi.setGridOption("quickFilterText", p.text); renderChips(); gridApi.onFilterChanged(); try { gridApi.ensureIndexVisible(0, "top"); } catch (e) {} }
  function removeNumFilter(i) { numFilters.splice(i, 1); const text = parseCmdline($("#cmdline").value).text; const expr = numFilters.map((f) => `${f.field}${f.op}${f.val}`).join(" "); $("#cmdline").value = (expr + " " + text).trim(); gridApi.setGridOption("quickFilterText", text); renderChips(); gridApi.onFilterChanged(); }

  // ---- CROSS-FILTER CHIPS ------------------------------------------------
  function addFilter(type, val, label) {
    if (!activeFilters.some((f) => f.type === type && f.val === val)) activeFilters.push({ type, val, label });
    renderChips(); gridApi.onFilterChanged(); try { gridApi.ensureIndexVisible(0, "top"); } catch (e) {}
  }
  function removeFilter(type, val) { activeFilters = activeFilters.filter((f) => !(f.type === type && f.val === val)); renderChips(); gridApi.onFilterChanged(); }
  function clearFilters() { activeFilters = []; numFilters = []; $("#cmdline").value = ""; gridApi.setGridOption("quickFilterText", ""); renderChips(); gridApi.onFilterChanged(); }
  function renderChips() {
    const el = $("#leaderChips");
    if (!activeFilters.length && !numFilters.length) { el.classList.remove("show"); el.innerHTML = ""; return; }
    el.classList.add("show");
    const numC = numFilters.map((f, i) => `<span class="chip-f chip-num">${f.field} ${OP_SYM[f.op]} ${f.val}<span class="chip-x" data-num="${i}">✕</span></span>`).join("");
    const catC = activeFilters.map((f) => `<span class="chip-f">${f.type}: ${f.label}<span class="chip-x" data-t="${f.type}" data-v="${f.val}">✕</span></span>`).join("");
    el.innerHTML = numC + catC + `<span class="chips-clear" id="chipsClear">clear all</span>`;
    $$("#leaderChips .chip-x[data-t]").forEach((x) => x.addEventListener("click", () => removeFilter(x.dataset.t, x.dataset.v)));
    $$("#leaderChips .chip-x[data-num]").forEach((x) => x.addEventListener("click", () => removeNumFilter(+x.dataset.num)));
    $("#chipsClear").addEventListener("click", clearFilters);
  }

  // ---- THEMES VIEW (heatmap + table) -------------------------------------
  // ---- THEME CLASS / MOMENTUM (raw enums -> clean labelled badges) -------
  const prettyEnum = (s) => (s ? String(s).toLowerCase().replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) : "–");
  const THEME_CLASS = { ELITE_THEME: ["Elite", "--g-s"], STRONG_THEME: ["Strong", "--g-a"], EMERGING_THEME: ["Emerging", "--pos"], NARROW_LEADERSHIP: ["Narrow", "--muted"], STABLE: ["Stable", "--muted"], MIXED: ["Mixed", "--faint"], WEAKENING: ["Weakening", "--g-d"], BROKEN_THEME: ["Broken", "--g-f"] };
  const THEME_MOM = { STRONG_ACCELERATING: ["Strong Accel", "↑", "--pos"], MODERATE_ACCELERATING: ["Accelerating", "↑", "--g-a"], STABLE: ["Stable", "→", "--muted"], DECELERATING: ["Decelerating", "↓", "--g-d"], WEAKENING: ["Weakening", "↓", "--g-f"] };
  function themeClassRenderer(p) { const m = THEME_CLASS[p.value]; if (!m) return prettyEnum(p.value); return `<span style="color:var(${m[1]});font-weight:600">${m[0]}</span>`; }
  function themeMomRenderer(p) { const m = THEME_MOM[p.value]; if (!m) return prettyEnum(p.value); const c = "var(" + m[2] + ")"; return `<span class="mom" style="color:${c}"><b>${m[1]}</b> ${m[0]}</span>`; }

  function initThemes() {
    if (themesInited) { if (heat) heat.resize(); return; }
    themesInited = true;
    heat = echarts.init($("#heatmap"), null, { renderer: "canvas" });
    drawHeatmap();
    heat.on("click", (p) => { if (p.name) { addFilter("theme", p.name, p.name); showView("leaders"); } });

    const cols = [
      { field: "name", headerName: "Theme", pinned: "left", width: 220, cellClass: "cell-ticker", cellStyle: { color: "var(--text)" } },
      { field: "ccqs", headerName: "CCQS", width: 110, type: "rightAligned", cellRenderer: ccqsRenderer, sort: "desc" },
      { field: "class", headerName: "Class", width: 124, cellRenderer: themeClassRenderer, headerTooltip: "Theme quality classification." },
      { field: "momentum", headerName: "Momentum", width: 150, cellRenderer: themeMomRenderer, headerTooltip: "Theme momentum trend." },
      { field: "pct50", headerName: "% > 50D", width: 96, type: "rightAligned", valueFormatter: (p) => pct0(p.value) },
      { field: "pct200", headerName: "% > 200D", width: 100, type: "rightAligned", valueFormatter: (p) => pct0(p.value) },
      { field: "breadth", headerName: "Breadth", width: 100, type: "rightAligned", valueFormatter: (p) => (p.value == null ? "–" : (+p.value).toFixed(1)) },
      { field: "rsComposite", headerName: "RS Comp", width: 100, type: "rightAligned", valueFormatter: (p) => (p.value == null ? "–" : (+p.value).toFixed(1)) },
      { field: "health", headerName: "Health", width: 96, type: "rightAligned", valueFormatter: (p) => (p.value == null ? "–" : (+p.value).toFixed(1)) },
      { field: "n", headerName: "N", width: 70, type: "rightAligned", cellStyle: { color: "var(--muted)" } },
      { field: "top", headerName: "Top Member", width: 120, cellStyle: { color: "var(--text)" } },
    ];
    themesApi = agGrid.createGrid($("#themesGrid"), {
      columnDefs: cols, rowData: DATA.themes,
      defaultColDef: { sortable: true, resizable: true, suppressHeaderMenuButton: true },
      rowHeight: 26, headerHeight: 26, getRowId: (p) => p.data.name,
    });
    themesApi.applyColumnState({ state: [{ colId: "ccqs", sort: "desc" }] });
    $("#themesGrid").addEventListener("click", (e) => { const row = e.target.closest(".ag-row"); const id = row && row.getAttribute("row-id"); if (id) { addFilter("theme", id, id); showView("leaders"); } });
    $("#themeSearch").addEventListener("input", (e) => themesApi.setGridOption("quickFilterText", e.target.value));
  }
  function drawHeatmap() {
    if (!heat) return;
    const themes = DATA.themes.filter((t) => t.n > 0 && t.ccqs != null);
    const vals = themes.map((t) => t.ccqs); const dmin = Math.min(...vals), dmax = Math.max(...vals);
    const dk = isDark();
    const relLum = (r, g, b) => { const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    const top = themes.slice().sort((a, b) => (b.n - a.n) || (b.ccqs - a.ccqs)).slice(0, 40); // breadth, CCQS tiebreak (D3)
    const data = top.map((t) => {
      const tt = Math.max(0, Math.min(1, (t.ccqs - dmin) / ((dmax - dmin) || 1)));
      const [r, g, b] = heatRamp(tt, dk);
      const useDark = relLum(r, g, b) > 0.179;                 // WCAG-optimal label color per tile
      return { name: t.name, value: t.n, ccqs: t.ccqs, top: t.top,
        itemStyle: { color: `rgb(${r},${g},${b})` },
        label: { color: useDark ? "#0c0f12" : "#f4f6f8", textBorderColor: useDark ? "rgba(255,255,255,.5)" : "rgba(0,0,0,.45)" } };
    });
    heat.setOption({
      tooltip: { backgroundColor: cssVar("--surface2"), borderColor: cssVar("--border"), textStyle: { color: cssVar("--text"), fontFamily: MONO_FONT, fontSize: 11 }, formatter: (p) => `<b>${p.name}</b><br/>CCQS ${p.data.ccqs?.toFixed(1)} · ${p.value} names<br/>Top: ${p.data.top || "–"}` },
      series: [{ type: "treemap", roam: false, nodeClick: false, breadcrumb: { show: false }, width: "100%", height: "100%", top: 0, left: 0, right: 0, bottom: 0, itemStyle: { borderColor: cssVar("--bg"), borderWidth: 1, gapWidth: 1 }, label: { show: true, textBorderWidth: 2, fontFamily: MONO_FONT, fontWeight: 600, fontSize: 10, lineHeight: 13, overflow: "truncate", formatter: (p) => `${shortenTheme(p.name)}\n${p.data.ccqs?.toFixed(1)}` }, emphasis: { itemStyle: { borderColor: cssVar("--accent"), borderWidth: 2 } }, data }],
    });
  }

  // ---- MOVERS / OOS / METHOD ---------------------------------------------
  function moverRow(tk, meta, val, cls) { return `<div class="mv-row" role="button" tabindex="0" data-tk="${tk}"><span class="mv-tk">${tk}</span><span class="mv-meta">${meta}</span><span class="mv-val ${cls}">${val}</span></div>`; }
  function renderMovers() {
    const w = DATA.whatChanged;
    $("#mvRisers").innerHTML = w.risers.map((r) => moverRow(r.t, r.tier, sgn(r.dccqs), r.dccqs >= 0 ? "pos" : "neg")).join("");
    $("#mvDecliners").innerHTML = w.decliners.map((r) => moverRow(r.t, r.from, sgn(r.dccqs), "neg")).join("");
    $("#mvMoves").innerHTML = w.moves.map((r) => moverRow(r.t, r.move, sgn(r.dccqs), r.dccqs >= 0 ? "pos" : "neg")).join("");
    $$(".mv-row").forEach((r) => { r.addEventListener("click", () => inspect(r.dataset.tk)); r.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); inspect(r.dataset.tk); } }); });
  }
  function renderOOS() {
    $("#oos").innerHTML = (DATA.oos || []).map((o) => { const sig = Math.abs(o.t) >= 2 ? "var(--pos)" : Math.abs(o.t) >= 1.5 ? "var(--g-s)" : "var(--muted)"; return `<div class="oos-card"><div class="oos-h">${o.horizon}</div><div class="oos-ic" style="color:${sig}">${sgn(o.ic, 3)}</div><div class="oos-t">t = ${sgn(o.t, 2)} · hit ${pct0((o.hit || 0) * 100)}</div></div>`; }).join("");
  }
  function renderMethod() {
    $("#method").innerHTML = `<b>CCQS</b> is a per-ticker composite of 10 standardized components — relative strength vs SPY, RS leadership, RS-line behaviour, trend slope, chart structure, multi-timeframe alignment, extension, residual momentum, oscillator momentum, and volume pattern. Each is z-scored cross-sectionally per date, combined with state-conditional weights, Bayesian-averaged across six states, and mapped to 0–100 via the standard-normal CDF, winsorized at the 1st/99th percentiles, and graded by per-date quantile cuts (top 8% → S). <b>Out-of-sample IC</b> is the Spearman rank correlation between today's CCQS and forward returns on data the model never saw; |t| > 2.0 indicates the signal is distinguishable from noise.`;
  }

  // ---- DETAIL DRAWER -----------------------------------------------------
  let _inspT; function inspectSoon(t) { clearTimeout(_inspT); _inspT = setTimeout(() => inspect(t), 80); } // debounce keyboard row-walking
  function selRow(n) { if (gridApi && n) { gridApi.deselectAll(); n.setSelected(true); } } // single clean highlight
  async function inspect(tk) {
    const s = DATA.stocks.find((x) => x.t === tk); if (!s) return;
    $("#dTicker").textContent = tk; $("#dScore").textContent = f1(s.ccqs);
    $("#dChips").innerHTML = [`<span class="pill-plain pill-f" data-ft="sec" data-fv="${s.sec}" data-fl="${s.sec}" title="Filter Leaders by ${s.sec}"><span class="sec-dot" style="background:${secColor(s.sec)}"></span>${s.sec}</span>`, `<span class="gchip" style="color:${gradeColor(s.grade)};background:color-mix(in srgb,${gradeColor(s.grade)} 18%,transparent)">Grade ${s.grade}</span>`, pill(tierColor(s.tierKey), s.tier), pill(stateColor(s.stateKey), s.state), pill("var(--muted)", s.theme, "theme", s.theme, s.theme)].join("");
    syncCmpAdd();
    curTicker = tk;
    if (trajChart) { trajChart.dispose(); trajChart = null; }
    $("#trajChart").innerHTML = '<div class="chart-empty">Loading…</div>';
    if (!DETAIL) {
      try { const r = await fetch("data/detail.json", { cache: "no-cache" }); if (!r.ok) throw 0; DETAIL = await r.json(); }
      catch (e) { /* leave DETAIL null so the next open retries */ $("#dComponents").innerHTML = '<div class="comp-name">Detail feed unavailable.</div>'; $("#dMetrics").innerHTML = ""; }
    }
    renderDetailTables(DETAIL ? DETAIL[tk] : null);
    curHist = await loadHist(tk);
    renderPeriods(); drawTraj();
  }
  function renderDetailTables(d) {
    if (!d) { $("#dComponents").innerHTML = '<div class="comp-name">—</div>'; $("#dMetrics").innerHTML = ""; return; }
    const maxC = Math.max(...d.components.map((c) => Math.abs(c.contrib || 0)), 0.001);
    $("#dComponents").innerHTML = d.components.map((c) => { const pos = (c.contrib || 0) >= 0, col = pos ? "var(--pos)" : "var(--neg)"; return `<div class="comp-row"><span class="comp-name">${c.c}</span><span class="comp-val" style="color:${col}">${sgn(c.contrib, 3)}</span><span class="comp-bar"><i style="width:${(Math.abs(c.contrib || 0) / maxC) * 100}%;background:${col}"></i></span></div>`; }).join("");
    $("#dMetrics").innerHTML = d.metrics.map((m) => `<div class="metric-row"><span class="mk">${m.m}</span><span class="mv">${m.v}</span></div>`).join("");
  }
  function renderPeriods() {
    $("#dPeriods").innerHTML = ["1M", "3M", "6M", "1Y", "ALL"].map((p) => `<button data-p="${p}" class="${p === curPeriod ? "on" : ""}">${p}</button>`).join("");
    $$("#dPeriods button").forEach((b) => b.addEventListener("click", () => { curPeriod = b.dataset.p; $$("#dPeriods button").forEach((x) => x.classList.toggle("on", x === b)); drawTraj(); }));
  }
  function slicePeriod(h) { const m = { "1M": 21, "3M": 63, "6M": 126, "1Y": 252, ALL: 1e9 }[curPeriod] || 252; return h.slice(Math.max(0, h.length - m)); }
  // Grade REGIMES (not buy/sell markers) — the settled grade at each point,
  // debounced so a band must hold >=K days to count (daily CCQS flickers across
  // quantile boundaries — that's noise). Contiguous runs become colored zones.
  function settledSeries(h) {
    const K = 5, out = new Array(h.length).fill(null);
    let band = null, count = 0, settled = null;
    for (let j = 0; j < h.length; j++) {
      const b = (h[j].g || "")[0];
      if (b) { if (b === band) count++; else { band = b; count = 1; } if (count >= K) settled = b; }
      out[j] = settled;
    }
    return out; // D7: leading unsettled head stays null -> no zone (honest "indeterminate")
  }
  function gradeRegimes(h) {
    const ss = settledSeries(h), reg = []; let cur = null, start = 0;
    for (let j = 0; j < h.length; j++) { if (ss[j] !== cur) { if (cur != null) reg.push({ grade: cur, start: h[start].d, end: h[j].d, n: j - start }); cur = ss[j]; start = j; } }
    if (cur != null && h.length) reg.push({ grade: cur, start: h[start].d, end: h[h.length - 1].d, n: h.length - start });
    return reg;
  }
  function hexToRgba(hex, a) {
    hex = (hex || "").replace("#", "");
    if (hex.length === 3) hex = hex.split("").map((c) => c + c).join("");
    const n = parseInt(hex, 16) || 0;
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  }
  // C1 fix: drive zone color from the live CSS grade token so it themes correctly.
  function zoneColor(g) { return hexToRgba(cssVar(GRADE[(g || "")[0]] || "--g-c"), 0.18); }
  function drawTraj() {
    const el = $("#trajChart");
    const h = slicePeriod(curHist).filter((p) => p.v != null);
    if (!h.length) { if (trajChart) { trajChart.dispose(); trajChart = null; } el.innerHTML = '<div class="chart-empty">No price history for this name.</div>'; return; }
    if (el.firstElementChild && el.firstElementChild.classList && el.firstElementChild.classList.contains("chart-empty")) el.innerHTML = "";
    if (!trajChart) trajChart = echarts.init(el, null, { renderer: "canvas" });
    const regimes = gradeRegimes(h);
    const ss = settledSeries(h); const settledByDate = {}; h.forEach((p, i) => (settledByDate[p.d] = ss[i]));
    const gByDate = {}; h.forEach((p) => (gByDate[p.d] = p.g));
    // Dynamic y-axis: fit the visible timeframe's CCQS range (+padding) so moves read on every period.
    const yv = h.map((p) => p.v); let ylo = Math.min(...yv), yhi = Math.max(...yv);
    if (yhi - ylo < 3) { const ymid = (yhi + ylo) / 2; ylo = ymid - 2; yhi = ymid + 2; }
    const ypad = Math.max(1.5, (yhi - ylo) * 0.16);
    const ymin = Math.max(0, Math.floor((ylo - ypad) / 2) * 2);
    const ymax = Math.min(100, Math.ceil((yhi + ypad) / 2) * 2);
    const yint = Math.max(2, Math.ceil((ymax - ymin) / 4 / 2) * 2);
    trajChart.setOption({
      animation: false,
      grid: { left: 34, right: 12, top: 10, bottom: 22 },
      tooltip: {
        trigger: "axis", backgroundColor: cssVar("--surface2"), borderColor: cssVar("--border"),
        textStyle: { color: cssVar("--text"), fontFamily: MONO_FONT, fontSize: 11 },
        axisPointer: { lineStyle: { color: cssVar("--faint"), width: 1 } },
        formatter: (ps) => { const p = ps[0], d = p.data[0], sg = settledByDate[d], rg = gByDate[d]; const extra = rg && sg && rg[0] !== sg ? ` <span style="opacity:.55">(today ${rg})</span>` : ""; return `${d}<br/>CCQS <b>${(+p.data[1]).toFixed(1)}</b> · Grade ${sg || "–"}${extra}`; },
      },
      xAxis: { type: "time", axisLine: { lineStyle: { color: cssVar("--border") } }, axisTick: { show: false }, axisLabel: { color: cssVar("--faint"), fontFamily: MONO_FONT, fontSize: 10 }, splitLine: { show: false } },
      yAxis: { type: "value", min: ymin, max: ymax, interval: yint, scale: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: cssVar("--faint"), fontFamily: MONO_FONT, fontSize: 10, formatter: (v) => v.toFixed(0) }, splitLine: { lineStyle: { color: cssVar("--border") } } },
      series: [{
        type: "line", showSymbol: false, smooth: false, z: 5,
        data: h.map((p) => [p.d, p.v]),
        lineStyle: { color: cssVar("--text"), width: 2.25, shadowColor: cssVar("--bg"), shadowBlur: 2 },
        emphasis: { disabled: true },
        markArea: { silent: true, z: 1, label: { show: true, position: "insideTop", distance: 3, color: cssVar("--faint"), fontFamily: MONO_FONT, fontWeight: 600, fontSize: 9 }, data: regimes.map((r) => [{ name: r.grade, xAxis: r.start, itemStyle: { color: zoneColor(r.grade) }, label: { show: r.n >= 12 } }, { xAxis: r.end }]) }, // D5: label only wide regimes
      }],
    }, true);
    trajChart.resize();
  }
  // A3/C4 — modal focus management: move focus in, trap Tab, restore on close.
  let _lastFocus = null;
  function _focusables(box) { return [...box.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select,textarea,[tabindex]:not([tabindex="-1"])')].filter((el) => el.offsetParent !== null); }
  function _openModal(outer, boxSel, focusSel) {
    _lastFocus = document.activeElement;
    outer.classList.add("open"); outer.setAttribute("aria-hidden", "false");
    const box = outer.querySelector(boxSel);
    setTimeout(() => { const t = (focusSel && box.querySelector(focusSel)) || _focusables(box)[0] || box; t && t.focus && t.focus(); }, 40);
    box._trap = (e) => { if (e.key !== "Tab") return; const f = _focusables(box); if (!f.length) return; const first = f[0], last = f[f.length - 1]; if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); } else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); } };
    box.addEventListener("keydown", box._trap);
  }
  function _closeModal(outer, boxSel) {
    outer.classList.remove("open"); outer.setAttribute("aria-hidden", "true");
    const box = outer.querySelector(boxSel); if (box && box._trap) { box.removeEventListener("keydown", box._trap); box._trap = null; }
    if (_lastFocus && _lastFocus.focus) { _lastFocus.focus(); _lastFocus = null; }
  }
  function wireSplitter() {
    const sp = $("#splitter"), insp = $("#inspector"); if (!sp || !insp) return;
    let sx, sw, drag = false;
    const move = (e) => { if (!drag) return; const w = Math.max(330, Math.min(660, sw + (sx - e.clientX))); insp.style.width = w + "px"; };
    const up = () => { if (!drag) return; drag = false; document.body.style.userSelect = ""; document.body.style.cursor = ""; if (trajChart) trajChart.resize(); };
    sp.addEventListener("mousedown", (e) => { drag = true; sx = e.clientX; sw = insp.offsetWidth; document.body.style.userSelect = "none"; document.body.style.cursor = "col-resize"; e.preventDefault(); });
    document.addEventListener("mousemove", move); document.addEventListener("mouseup", up);
  }

  // ---- THEME TOGGLE ------------------------------------------------------
  function initTheme() {
    setTheme(localStorage.getItem("ccqs-theme") || "dark");
    $("#themeToggle").addEventListener("click", () => setTheme(isDark() ? "light" : "dark"));
  }
  function setTheme(mode) {
    document.documentElement.dataset.theme = mode;
    localStorage.setItem("ccqs-theme", mode);
    $(".tt-label").textContent = mode === "dark" ? "Dark" : "Light";
    if (heat) drawHeatmap();
    if (trajChart) { trajChart.dispose(); trajChart = null; if (curTicker) drawTraj(); }
  }

  // ---- COMMAND LINE + ⌘K -------------------------------------------------
  function wireCmdline() {
    $("#cmdline").addEventListener("input", (e) => { showView("leaders"); applyCmdline(e.target.value); });
    $("#cmdline").addEventListener("keydown", (e) => { if (e.key === "Enter") { const node = gridApi.getDisplayedRowAtIndex(0); if (node) inspect(node.data.t); } else if (e.key === "Escape" && e.target.value) { e.stopPropagation(); e.target.value = ""; applyCmdline(""); } });
  }
  const cmdkOpen = () => $("#cmdk").classList.contains("open");
  function wireSearch() {
    document.addEventListener("keydown", (e) => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openCmdk(); } if (e.key === "Escape") { closeCmdk(); closeCompare(); } });
    $("#cmdkScrim").addEventListener("click", closeCmdk);
    $("#cmdkInput").addEventListener("input", (e) => renderCmdk(e.target.value));
    let sel = 0;
    $("#cmdkInput").addEventListener("keydown", (e) => {
      const items = $$(".cmdk-item");
      if (e.key === "ArrowDown") { sel = Math.min(sel + 1, items.length - 1); items.forEach((it, i) => it.classList.toggle("sel", i === sel)); e.preventDefault(); }
      else if (e.key === "ArrowUp") { sel = Math.max(sel - 1, 0); items.forEach((it, i) => it.classList.toggle("sel", i === sel)); e.preventDefault(); }
      else if (e.key === "Enter" && items[sel]) { inspect(items[sel].dataset.tk); closeCmdk(); }
    });
    window._sel0 = () => (sel = 0);
  }
  function openCmdk() { $("#cmdkInput").value = ""; renderCmdk(""); _openModal($("#cmdk"), ".cmdk-box", "#cmdkInput"); }
  function closeCmdk() { _closeModal($("#cmdk"), ".cmdk-box"); }
  function renderCmdk(q) {
    window._sel0 && window._sel0(); q = (q || "").toUpperCase();
    const hits = DATA.stocks.filter((s) => s.t.includes(q) || (s.theme || "").toUpperCase().includes(q)).slice(0, 40);
    $("#cmdkList").innerHTML = hits.map((s, i) => `<div class="cmdk-item ${i === 0 ? "sel" : ""}" data-tk="${s.t}"><span class="cmdk-tk">${s.t}</span><span class="cmdk-meta">${s.theme || ""} · ${f1(s.ccqs)} · ${s.grade || ""}</span></div>`).join("");
    $$(".cmdk-item").forEach((it) => it.addEventListener("click", () => { inspect(it.dataset.tk); closeCmdk(); }));
  }

  // ---- VIEW ROUTER -------------------------------------------------------
  function showView(name) {
    $$(".view").forEach((v) => v.classList.toggle("active", v.id === "view-" + name));
    $$(".nav-item").forEach((n) => { const on = n.dataset.view === name; n.classList.toggle("active", on); n.setAttribute("aria-current", on ? "page" : "false"); });
    if (name === "themes") initThemes();
  }
  function wireNav() {
    $$(".nav-item").forEach((n) => {
      n.addEventListener("click", () => showView(n.dataset.view));
      n.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); showView(n.dataset.view); } });
    });
  }

  // ---- SAVED VIEWS -------------------------------------------------------
  function loadViews() { try { return JSON.parse(localStorage.getItem("ccqs-views") || "{}"); } catch (e) { return {}; } }
  function renderViewSel() { $("#viewSel").innerHTML = `<option value="">Views…</option>` + Object.keys(loadViews()).map((n) => `<option value="${n}">${n}</option>`).join(""); }
  function saveView() {
    const name = prompt("Save current layout + filters as:"); if (!name) return;
    const v = loadViews();
    v[name] = { col: gridApi.getColumnState(), grade: activeGrade, filters: activeFilters, q: $("#cmdline").value };
    localStorage.setItem("ccqs-views", JSON.stringify(v)); renderViewSel(); $("#viewSel").value = name; showToast("View “" + name + "” saved");
  }
  function applyView(name) {
    const v = loadViews()[name]; if (!v) return;
    gridApi.applyColumnState({ state: v.col, applyOrder: true });
    activeGrade = v.grade || "All";
    $$("#gradeSeg button").forEach((b) => b.classList.toggle("on", b.dataset.g === activeGrade));
    activeFilters = (v.filters || []).slice(); renderChips();
    $("#cmdline").value = v.q || ""; applyCmdline(v.q || "");
    gridApi.onFilterChanged(); try { gridApi.ensureIndexVisible(0, "top"); } catch (e) {}
  }
  function wireViews() { renderViewSel(); $("#saveViewBtn").addEventListener("click", saveView); $("#viewSel").addEventListener("change", (e) => { if (e.target.value) applyView(e.target.value); }); }

  // ---- COMPARE BASKET ----------------------------------------------------
  function syncCmpAdd() { const b = $("#cmpAdd"); if (!b) return; const inb = compareSet.includes($("#dTicker").textContent); b.classList.toggle("in", inb); b.textContent = inb ? "✓ IN BASKET" : "＋ COMPARE"; }
  function addCompare(tk) { if (compareSet.includes(tk)) { removeCompare(tk); return; } if (compareSet.length >= 4) return; compareSet.push(tk); renderTray(); syncCmpAdd(); }
  function removeCompare(tk) { compareSet = compareSet.filter((x) => x !== tk); renderTray(); syncCmpAdd(); if ($("#cmp").classList.contains("open")) openCompare(); }
  function renderTray() {
    const tray = $("#cmpTray");
    if (!compareSet.length) { tray.classList.remove("show"); tray.innerHTML = ""; return; }
    tray.classList.add("show");
    tray.innerHTML = compareSet.map((tk) => `<span class="ct-tk">${tk}<span class="ct-x" data-tk="${tk}">✕</span></span>`).join("") + `<button class="ct-open" id="ctOpen" ${compareSet.length < 2 ? "disabled" : ""}>Compare ▸</button>`;
    $$("#cmpTray .ct-x").forEach((x) => x.addEventListener("click", () => removeCompare(x.dataset.tk)));
    const o = $("#ctOpen"); if (o) o.addEventListener("click", openCompare);
  }
  async function openCompare() {
    if (compareSet.length < 2) return;
    _openModal($("#cmp"), ".cmp-box", "#cmpClose");
    $("#cmpLegend").innerHTML = compareSet.map((tk, i) => `<span class="lg"><i style="background:var(${CMP_TOKENS[i]})"></i>${tk}</span>`).join("");
    renderCompareTable();
    if (cmpChart) { try { cmpChart.remove(); } catch (e) {} cmpChart = null; }
    $("#cmpChart").innerHTML = "";
    cmpChart = LightweightCharts.createChart($("#cmpChart"), { height: 300, autoSize: true, layout: { background: { type: "solid", color: "transparent" }, textColor: cssVar("--muted"), fontFamily: MONO_FONT, fontSize: 10 }, grid: { vertLines: { color: cssVar("--border") }, horzLines: { color: cssVar("--border") } }, rightPriceScale: { borderColor: cssVar("--border") }, timeScale: { borderColor: cssVar("--border") } });
    for (let i = 0; i < compareSet.length; i++) {
      const h = await loadHist(compareSet[i]);
      const ser = cmpChart.addLineSeries({ color: cssVar(CMP_TOKENS[i]), lineWidth: 2, priceLineVisible: false, lastValueVisible: false });
      ser.setData(h.slice(-252).filter((p) => p.v != null).map((p) => ({ time: p.d, value: p.v })));
    }
    cmpChart.timeScale().fitContent();
  }
  function closeCompare() { _closeModal($("#cmp"), ".cmp-box"); }
  function renderCompareTable() {
    const cols = ["CCQS", "Grade", "Leadership", "State", "Δ 1D", "Δ 5D", "Δ 21D", "RS"];
    const body = compareSet.map((tk) => { const s = DATA.stocks.find((x) => x.t === tk) || {}; return `<tr><td class="tk">${tk}</td><td>${f1(s.ccqs)}</td><td>${s.grade || "–"}</td><td>${s.tier || "–"}</td><td>${s.state || "–"}</td><td class="${s.d1 >= 0 ? "pos" : "neg"}">${sgn(s.d1)}</td><td class="${s.d5 >= 0 ? "pos" : "neg"}">${sgn(s.d5)}</td><td class="${s.d21 >= 0 ? "pos" : "neg"}">${sgn(s.d21)}</td><td>${s.rs != null ? s.rs : "–"}</td></tr>`; }).join("");
    $("#cmpTable").innerHTML = `<table style="width:100%;border-collapse:collapse"><tr><th>Ticker</th>${cols.map((c) => `<th>${c}</th>`).join("")}</tr>${body}</table>`;
  }
  function wireCompare() {
    $("#cmpAdd").addEventListener("click", () => addCompare($("#dTicker").textContent));
    $("#cmpScrim").addEventListener("click", closeCompare); $("#cmpClose").addEventListener("click", closeCompare);
    // U11 reverse-nav: clicking the drawer's theme chip filters Leaders to that theme.
    $("#dChips").addEventListener("click", (e) => { const pe = e.target.closest("[data-ft]"); if (pe) { addFilter(pe.dataset.ft, pe.dataset.fv, pe.dataset.fl); showView("leaders"); } });
  }

  boot();
})();
