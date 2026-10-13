const ui = {
  pageRoot: document.querySelector("#page-root"),
  main: document.querySelector("#main-content"),
  globalError: document.querySelector("#global-error"),
  globalErrorMessage: document.querySelector("#global-error-message"),
  retryButton: document.querySelector("#retry-button"),
  refreshButton: document.querySelector("#refresh-button"),
  syncState: document.querySelector("#sync-state"),
  routeAnnouncer: document.querySelector("#route-announcer"),
  breadcrumbs: document.querySelector("#breadcrumbs"),
  sidebar: document.querySelector("#sidebar"),
  sidebarScrim: document.querySelector("#sidebar-scrim"),
  mobileMenu: document.querySelector("#mobile-menu"),
  mobileNavClose: document.querySelector("#mobile-nav-close"),
  approvalCount: document.querySelector("#approval-count"),
  incidentCount: document.querySelector("#incident-nav-count"),
  environmentButton: document.querySelector("#environment-button"),
  environmentDialog: document.querySelector("#environment-dialog"),
  environmentList: document.querySelector("#environment-list"),
  resetButton: document.querySelector("#reset-workspace-button"),
  resetConfirmation: document.querySelector("#reset-confirmation"),
  cancelResetButton: document.querySelector("#cancel-reset-button"),
  confirmResetButton: document.querySelector("#confirm-reset-button"),
  decisionDialog: document.querySelector("#decision-dialog"),
  decisionSummary: document.querySelector("#decision-summary"),
  decisionError: document.querySelector("#decision-error"),
  decisionActor: document.querySelector("#decision-actor"),
  decisionJustification: document.querySelector("#decision-justification"),
  simulationAcknowledgement: document.querySelector("#simulation-acknowledgement"),
  networkMapDialog: document.querySelector("#network-map-dialog"),
  networkMapDialogBody: document.querySelector("#network-map-dialog-body"),
  toast: document.querySelector("#toast"),
};

const savedUiState = (() => {
  try {
    return JSON.parse(window.localStorage.getItem("nsra.ui.v2") || "{}");
  } catch {
    return {};
  }
})();

const state = {
  loaded: false,
  busy: false,
  status: null,
  overview: null,
  network: null,
  portfolio: [],
  inventory: [],
  shipments: [],
  drafts: [],
  audit: [],
  integrations: [],
  basemap: null,
  analysis: null,
  selectedDraft: null,
  portfolioQuery: "",
  portfolioSeverity: "ALL",
  approvalStatus: "ALL",
  auditQuery: "",
  networkMode: "INBOUND",
  selectedNodeId: null,
  networkZoom: 1,
  networkPanX: 0,
  networkPanY: 0,
  inventoryRange: savedUiState.inventoryRange || "ALL",
  selectedScenarioId: null,
  incidentView: savedUiState.incidentView || "summary",
  globalFilters: {
    facility: savedUiState.globalFilters?.facility || "ALL",
    material: savedUiState.globalFilters?.material || "ALL",
    severity: savedUiState.globalFilters?.severity || "ALL",
  },
  tables: {
    portfolio: { sortKey: "exposure", direction: "desc", page: 1, pageSize: 3 },
    routes: { sortKey: "status", direction: "asc", page: 1, pageSize: 5, query: "", filter: "ALL" },
    scenarios: { sortKey: "total", direction: "asc", page: 1, pageSize: 5, filter: "ALL" },
    audit: { sortKey: "timestamp", direction: "desc", page: 1, pageSize: 8 },
  },
};

const iconPaths = {
  refresh: '<path d="M20 6v5h-5M4 18v-5h5M18.5 9A7 7 0 0 0 6.2 6.5L4 11m16 2-2.2 4.5A7 7 0 0 1 5.5 15"/>',
  arrow: '<path d="M5 12h14m-5-5 5 5-5 5"/>',
  analyze: '<path d="M4 19V9m6 10V5m6 14v-7m4 7H2"/>',
  package: '<path d="m4 7 8-4 8 4-8 4zM4 7v10l8 4 8-4V7M12 11v10"/>',
  shield: '<path d="M9 12.8 11.2 15 16 9.5M12 3l8 3v5c0 5-3.4 8.3-8 10-4.6-1.7-8-5-8-10V6z"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  route: '<circle cx="5" cy="17" r="2"/><circle cx="19" cy="7" r="2"/><path d="M7 17c7 0 3-10 10-10"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  alert: '<path d="M12 8v5m0 3h.01M10.3 3.9 2.7 17a2 2 0 0 0 1.7 3h15.2a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  minus: '<path d="M5 12h14"/>',
  reset: '<path d="M4 9V4h5M20 15v5h-5M5.5 6.5A8 8 0 0 1 19 9m-.5 8.5A8 8 0 0 1 5 15"/>',
  expand: '<path d="M8 3H3v5M16 3h5v5M8 21H3v-5m18 0v5h-5"/>',
  download: '<path d="M12 3v12m0 0 5-5m-5 5-5-5M4 20h16"/>',
  filter: '<path d="M4 5h16l-6 7v5l-4 2v-7z"/>',
  chevron: '<path d="m8 10 4 4 4-4"/>',
};

function icon(name, className = "") {
  return `<svg class="${className}" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">${iconPaths[name] || iconPaths.alert}</svg>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatNumber(value, maximumFractionDigits = 1) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits }).format(Number(value || 0));
}

function formatCurrency(value, compact = false) {
  const amount = Number(value || 0);
  if (compact) {
    return `IDR ${new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(amount)}`;
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatDateTime(value, options = {}) {
  if (!value) return "Not projected";
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Makassar",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    ...options,
  }).format(new Date(value));
}

function formatDay(value) {
  return formatDateTime(value, { weekday: "short", day: "2-digit", month: "short", hour: undefined, minute: undefined });
}

function sentenceCase(value) {
  return String(value || "").replaceAll("_", " ").toLowerCase().replace(/^\w/, (match) => match.toUpperCase());
}

function saveUiPreferences() {
  try {
    window.localStorage.setItem("nsra.ui.v2", JSON.stringify({
      inventoryRange: state.inventoryRange,
      incidentView: state.incidentView,
      globalFilters: state.globalFilters,
    }));
  } catch {
    // Local storage is an enhancement; the operational workspace remains usable without it.
  }
}

function compareValues(left, right) {
  if (left == null && right == null) return 0;
  if (left == null) return 1;
  if (right == null) return -1;
  if (typeof left === "number" || typeof right === "number") return Number(left) - Number(right);
  return String(left).localeCompare(String(right), "en", { numeric: true, sensitivity: "base" });
}

function sortRows(rows, tableName, accessors) {
  const config = state.tables[tableName];
  const accessor = accessors[config.sortKey] || Object.values(accessors)[0];
  const direction = config.direction === "desc" ? -1 : 1;
  return [...rows].sort((left, right) => compareValues(accessor(left), accessor(right)) * direction);
}

function paginateRows(rows, tableName) {
  const config = state.tables[tableName];
  const pages = Math.max(1, Math.ceil(rows.length / config.pageSize));
  config.page = Math.min(Math.max(1, config.page), pages);
  const start = (config.page - 1) * config.pageSize;
  return { rows: rows.slice(start, start + config.pageSize), pages, start };
}

function sortableHeader(label, tableName, key) {
  const config = state.tables[tableName];
  const active = config.sortKey === key;
  const ariaSort = active ? (config.direction === "asc" ? "ascending" : "descending") : "none";
  return `<th scope="col" aria-sort="${ariaSort}"><button class="sort-button" type="button" data-sort-table="${tableName}" data-sort-key="${key}">${escapeHtml(label)}<span aria-hidden="true">${active ? (config.direction === "asc" ? "↑" : "↓") : "↕"}</span></button></th>`;
}

function tableFooter(tableName, total, pages, label) {
  const config = state.tables[tableName];
  const start = total ? (config.page - 1) * config.pageSize + 1 : 0;
  const end = Math.min(total, config.page * config.pageSize);
  return `<div class="table-footer">
    <span>${start}–${end} of ${total} ${escapeHtml(label)}</span>
    <label>Rows <select data-page-size="${tableName}" aria-label="Rows per page for ${escapeHtml(label)}">${[3, 5, 8, 10].map((size) => `<option value="${size}"${config.pageSize === size ? " selected" : ""}>${size}</option>`).join("")}</select></label>
    <div class="pagination" aria-label="${escapeHtml(label)} pagination"><button class="icon-button" type="button" data-page-table="${tableName}" data-page-delta="-1" aria-label="Previous page" ${config.page <= 1 ? "disabled" : ""}>←</button><span>Page ${config.page} of ${pages}</span><button class="icon-button" type="button" data-page-table="${tableName}" data-page-delta="1" aria-label="Next page" ${config.page >= pages ? "disabled" : ""}>→</button></div>
  </div>`;
}

function csvCell(value) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

function downloadCsv(filename, columns, rows) {
  const csv = [columns.map((column) => csvCell(column.label)).join(","), ...rows.map((row) => columns.map((column) => csvCell(column.value(row))).join(","))].join("\r\n");
  const url = URL.createObjectURL(new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function severityBadge(severity) {
  const level = String(severity || "INFO").toLowerCase();
  return `<span class="status-badge status-${escapeHtml(level)}"><span aria-hidden="true"></span>${escapeHtml(sentenceCase(severity))}</span>`;
}

function stateBadge(status) {
  const normalized = String(status || "UNKNOWN").toLowerCase().replaceAll("_", "-");
  return `<span class="state-badge state-${escapeHtml(normalized)}">${escapeHtml(sentenceCase(status))}</span>`;
}

function api(path, options = {}) {
  return fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  }).then(async (response) => {
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(payload.message || `Request failed with status ${response.status}`);
      error.payload = payload;
      throw error;
    }
    return payload;
  });
}

function setBusy(busy, message = "Updating") {
  state.busy = busy;
  ui.pageRoot.setAttribute("aria-busy", String(busy));
  ui.refreshButton.disabled = busy;
  ui.refreshButton.classList.toggle("is-spinning", busy);
  if (busy) {
    ui.syncState.querySelector("span:last-child").textContent = message;
  }
}

function showToast(message, isError = false) {
  ui.toast.textContent = message;
  ui.toast.classList.toggle("is-error", isError);
  ui.toast.hidden = false;
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => { ui.toast.hidden = true; }, 4200);
}

function showError(error) {
  ui.globalErrorMessage.textContent = error.message || "Unknown application error.";
  ui.globalError.hidden = false;
  ui.syncState.classList.add("is-offline");
  ui.syncState.querySelector("span:last-child").textContent = "Attention required";
}

function clearError() {
  ui.globalError.hidden = true;
  ui.syncState.classList.remove("is-offline");
}

function parseRoute(pathname = window.location.pathname) {
  const clean = pathname.replace(/\/+$/, "") || "/";
  if (clean === "/" || clean === "/overview") return { name: "overview" };
  if (clean === "/network") return { name: "network" };
  if (clean === "/incidents") return { name: "incidents" };
  if (clean === "/approvals") return { name: "approvals" };
  if (clean === "/audit") return { name: "audit" };
  if (clean === "/integrations") return { name: "integrations" };
  const incident = clean.match(/^\/incidents\/([^/]+)$/);
  if (incident) return { name: "incident", id: decodeURIComponent(incident[1]) };
  const scenario = clean.match(/^\/scenarios\/([^/]+)$/);
  if (scenario) return { name: "scenario", id: decodeURIComponent(scenario[1]) };
  return { name: "overview" };
}

function activeNavRoute(route) {
  if (route.name === "incident" || route.name === "scenario") return "incidents";
  return route.name;
}

function breadcrumbItems(route) {
  const overview = { label: "Overview", href: "/overview" };
  const incident = route.name === "incident"
    ? findPortfolioItem(route.id)
    : route.name === "scenario" && state.analysis?.analysis_id === route.id
      ? findPortfolioItem(state.analysis.incident_id)
      : null;
  const incidentLabel = incident?.incident_id || route.id || "Incident";
  const itemsByRoute = {
    overview: [{ label: "Executive overview" }],
    network: [overview, { label: "Supply network" }],
    incidents: [overview, { label: "Incident portfolio" }],
    incident: [
      overview,
      { label: "Incident portfolio", href: "/incidents" },
      { label: incidentLabel, title: incident?.title || incidentLabel },
    ],
    scenario: [
      overview,
      { label: "Incident portfolio", href: "/incidents" },
      ...(incident ? [{ label: incident.incident_id, href: `/incidents/${encodeURIComponent(incident.incident_id)}`, title: incident.title }] : []),
      { label: "Scenario analysis" },
    ],
    approvals: [overview, { label: "Approval inbox" }],
    audit: [overview, { label: "Audit explorer" }],
    integrations: [overview, { label: "Integration health" }],
  };
  return itemsByRoute[route.name] || itemsByRoute.overview;
}

function updateChrome(route) {
  const items = breadcrumbItems(route);
  ui.breadcrumbs.innerHTML = items.map((item, index) => {
    const label = escapeHtml(item.label);
    const title = item.title ? ` title="${escapeHtml(item.title)}"` : "";
    const content = item.href
      ? `<a href="${item.href}" data-link${title}>${label}</a>`
      : `<span aria-current="page"${title}>${label}</span>`;
    if (!index) return content;
    return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>${content}`;
  }).join("");
  document.querySelectorAll(".nav-item").forEach((item) => {
    const active = item.dataset.route === activeNavRoute(route);
    item.classList.toggle("is-active", active);
    if (active) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  });
}

function navigate(href, { replace = false } = {}) {
  if (replace) window.history.replaceState({}, "", href);
  else window.history.pushState({}, "", href);
  closeMobileNav();
  renderRoute({ focus: true });
}

function pageHeading({ eyebrow, title, description, actions = "", summary = "", backHref = "", backLabel = "" }) {
  return `
    <section class="page-heading" aria-labelledby="page-title">
      <div class="page-heading-copy">
        ${backHref ? `<a class="context-back-link" href="${backHref}" data-link>${icon("arrow")}<span>${escapeHtml(backLabel || "Back")}</span></a>` : ""}
        <p class="eyebrow">${escapeHtml(eyebrow)}</p>
        <h1 id="page-title" tabindex="-1">${escapeHtml(title)}</h1>
        <p>${escapeHtml(description)}</p>
      </div>
      ${actions || summary ? `<div class="page-heading-actions">${summary}${actions}</div>` : ""}
    </section>`;
}

function panelHeader(title, description = "", aside = "") {
  return `<div class="panel-header">
    <div><h2>${escapeHtml(title)}</h2>${description ? `<p>${escapeHtml(description)}</p>` : ""}</div>
    ${aside}
  </div>`;
}

function emptyState(title, copy, action = "") {
  return `<div class="empty-state">
    <span class="empty-state-icon">${icon("package")}</span>
    <h2>${escapeHtml(title)}</h2>
    <p>${escapeHtml(copy)}</p>
    ${action}
  </div>`;
}

function kpiStrip(items) {
  return `<section class="kpi-strip" aria-label="Operational summary">
    ${items.map((item) => `<div class="kpi-item">
      <span>${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(item.value)}</strong>
      <small class="${escapeHtml(item.tone || "")}">${escapeHtml(item.detail || "")}</small>
    </div>`).join("")}
  </section>`;
}

function linePath(points, x, y) {
  return points.map((point, index) => `${index ? "L" : "M"} ${x(point).toFixed(2)} ${y(point).toFixed(2)}`).join(" ");
}

function renderExposureTrend(points) {
  if (!points.length) return emptyState("No trend data", "Historical exposure points are not available.");
  const width = 820;
  const height = 270;
  const margin = { top: 24, right: 24, bottom: 40, left: 62 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const max = Math.max(...points.map((item) => Number(item.exposure_idr)), 1);
  const x = (_, index) => margin.left + (index / Math.max(points.length - 1, 1)) * innerWidth;
  const y = (item) => margin.top + innerHeight - (Number(item.exposure_idr) / max) * innerHeight;
  const path = linePath(points, (item) => x(item, points.indexOf(item)), y);
  const area = `${path} L ${margin.left + innerWidth} ${margin.top + innerHeight} L ${margin.left} ${margin.top + innerHeight} Z`;
  const ticks = [0, 0.5, 1];
  return `<div class="chart-shell exposure-chart-shell">
    <div class="chart-summary"><strong>${formatCurrency(points.at(-1).exposure_idr, true)}</strong><span>current modeled baseline exposure</span></div>
    <svg class="chart-svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-labelledby="exposure-chart-title exposure-chart-desc">
      <title id="exposure-chart-title">Network downtime exposure trend</title>
      <desc id="exposure-chart-desc">Exposure rises from ${formatCurrency(points[0].exposure_idr, true)} to ${formatCurrency(points.at(-1).exposure_idr, true)} across seven operational snapshots.</desc>
      ${ticks.map((tick) => {
        const tickY = margin.top + innerHeight - tick * innerHeight;
        return `<line class="chart-gridline" x1="${margin.left}" y1="${tickY}" x2="${margin.left + innerWidth}" y2="${tickY}"/>
          <text class="chart-axis-label" x="${margin.left - 10}" y="${tickY + 4}" text-anchor="end">${escapeHtml(formatCurrency(max * tick, true).replace("IDR ", ""))}</text>`;
      }).join("")}
      <path class="chart-area" d="${area}"/>
      <path class="chart-line chart-line-primary" d="${path}"/>
      ${points.map((point, index) => `<g class="chart-point" tabindex="0" role="listitem">
        <title>${formatDay(point.observed_at)}: ${formatCurrency(point.exposure_idr)}</title>
        <circle cx="${x(point, index)}" cy="${y(point)}" r="4"/>
      </g>`).join("")}
      ${points.map((point, index) => `<text class="chart-axis-label" x="${x(point, index)}" y="${height - 12}" text-anchor="middle">${escapeHtml(new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", timeZone: "Asia/Makassar" }).format(new Date(point.observed_at)))}</text>`).join("")}
    </svg>
  </div>`;
}

function renderApprovalTrend(points) {
  if (!points.length) return "";
  const max = Math.max(...points.map((point) => Number(point.pending_approvals) + Number(point.approved_actions)), 1);
  return `<div class="approval-trend" role="img" aria-label="Pending and approved response activity over seven days">
    ${points.map((point) => {
      const pendingHeight = Math.max(3, (Number(point.pending_approvals) / max) * 108);
      const approvedHeight = Math.max(3, (Number(point.approved_actions) / max) * 108);
      return `<div class="approval-day">
        <div class="approval-bars">
          <span class="bar-pending" style="height:${pendingHeight}px" title="${point.pending_approvals} pending"></span>
          <span class="bar-approved" style="height:${approvedHeight}px" title="${point.approved_actions} approved"></span>
        </div>
        <small>${escapeHtml(new Intl.DateTimeFormat("en-GB", { weekday: "short", timeZone: "Asia/Makassar" }).format(new Date(point.observed_at)))}</small>
      </div>`;
    }).join("")}
  </div>
  <div class="chart-legend"><span><i class="legend-swatch pending"></i>Pending</span><span><i class="legend-swatch approved"></i>Approved cumulative</span></div>`;
}

function renderRiskMatrix(matrix) {
  const populated = new Map(matrix.cells.map((cell) => [`${cell.facility_id}::${cell.material_id}`, cell]));
  const abbreviate = (name) => name.split(" ").map((part) => part[0]).join("").slice(0, 4).toUpperCase();
  return `<div class="heatmap-wrap">
    <table class="risk-heatmap">
      <caption class="sr-only">Facility and material risk matrix. Every populated cell includes a textual risk label and hours of cover.</caption>
      <thead><tr><th scope="col">Facility</th>${matrix.materials.map((material) => `<th scope="col"><span title="${escapeHtml(material.name)}">${escapeHtml(abbreviate(material.name))}</span></th>`).join("")}</tr></thead>
      <tbody>
        ${matrix.facilities.map((facility) => `<tr>
          <th scope="row"><strong>${escapeHtml(facility.facility_name)}</strong><small>${escapeHtml(facility.facility_id)}</small></th>
          ${matrix.materials.map((material) => {
            const cell = populated.get(`${facility.facility_id}::${material.material_id}`);
            if (!cell) return '<td class="risk-none"><span aria-label="Not stocked">—</span></td>';
            const cover = cell.hours_of_cover == null ? "N/A" : `${formatNumber(cell.hours_of_cover, 0)}h`;
            return `<td class="risk-cell risk-${cell.risk}" tabindex="0"><strong>${escapeHtml(sentenceCase(cell.risk))}</strong><small>${escapeHtml(cover)}</small></td>`;
          }).join("")}
        </tr>`).join("")}
      </tbody>
    </table>
    <div class="heatmap-legend" aria-label="Risk scale">
      <span><i class="risk-key stable"></i>Stable</span><span><i class="risk-key watch"></i>Watch</span><span><i class="risk-key high"></i>High</span><span><i class="risk-key critical"></i>Critical</span>
    </div>
  </div>`;
}

function projectLocation(node, width = 920, height = 400) {
  const x = 42 + ((Number(node.longitude) - 95) / 46) * (width - 84);
  const y = 24 + ((6 - Number(node.latitude)) / 17) * (height - 58);
  return { x, y };
}

function routeCurve(source, destination) {
  const middleX = (source.x + destination.x) / 2;
  const middleY = Math.min(source.y, destination.y) - Math.max(18, Math.abs(destination.x - source.x) * 0.08);
  return `M ${source.x.toFixed(1)} ${source.y.toFixed(1)} Q ${middleX.toFixed(1)} ${middleY.toFixed(1)} ${destination.x.toFixed(1)} ${destination.y.toFixed(1)}`;
}

function renderIndonesiaOutline(width, height) {
  const polygons = state.basemap?.geometry?.coordinates || [];
  return polygons.map((polygon) => {
    const path = polygon.map((ring) => ring.map((coordinate, index) => {
      const point = projectLocation({ longitude: coordinate[0], latitude: coordinate[1] }, width, height);
      return `${index ? "L" : "M"} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`;
    }).join(" ") + " Z").join(" ");
    return `<path d="${path}"/>`;
  }).join("");
}

function routeMidpoint(source, destination) {
  const control = {
    x: (source.x + destination.x) / 2,
    y: Math.min(source.y, destination.y) - Math.max(18, Math.abs(destination.x - source.x) * 0.08),
  };
  return {
    x: 0.25 * source.x + 0.5 * control.x + 0.25 * destination.x,
    y: 0.25 * source.y + 0.5 * control.y + 0.25 * destination.y,
  };
}

function layoutNetworkNodes(nodes, width, height) {
  const groups = new Map();
  nodes.forEach((node) => {
    const key = node.city || node.location_id;
    const group = groups.get(key) || [];
    group.push(node);
    groups.set(key, group);
  });
  const positionPatterns = {
    1: [[0, 0]],
    2: [[-9, 6], [9, -6]],
    3: [[-12, 8], [0, -10], [12, 8]],
    4: [[-13, 8], [-5, -10], [7, -10], [15, 8]],
    5: [[-16, 8], [-8, -10], [4, -13], [15, -5], [13, 11]],
  };
  const typeOrder = { PORT: 0, FACTORY: 1, WAREHOUSE: 2, SUPPLIER: 3 };
  const positions = new Map();
  const labels = [];
  groups.forEach((members, city) => {
    const ordered = [...members].sort((a, b) => (typeOrder[a.location_type] ?? 9) - (typeOrder[b.location_type] ?? 9) || a.location_id.localeCompare(b.location_id));
    const projected = ordered.map((node) => projectLocation(node, width, height));
    const center = {
      x: projected.reduce((total, point) => total + point.x, 0) / projected.length,
      y: projected.reduce((total, point) => total + point.y, 0) / projected.length,
    };
    const offsets = positionPatterns[Math.min(ordered.length, 5)] || ordered.map((_, index) => {
      const angle = (Math.PI * 2 * index) / ordered.length - Math.PI / 2;
      return [Math.cos(angle) * 17, Math.sin(angle) * 17];
    });
    ordered.forEach((node, index) => {
      positions.set(node.location_id, { x: center.x + offsets[index][0], y: center.y + offsets[index][1] });
    });
    if (ordered.some((node) => node.location_type !== "SUPPLIER")) {
      const groupPoints = ordered.map((node) => positions.get(node.location_id));
      labels.push({
        city,
        x: Math.min(width - 58, Math.max(...groupPoints.map((point) => point.x)) + 10),
        y: Math.max(14, Math.min(...groupPoints.map((point) => point.y)) - 8),
      });
    }
  });
  return { positions, labels };
}

function networkTransform(width, height) {
  const zoom = state.networkZoom;
  const x = ((1 - zoom) * width) / 2 + state.networkPanX;
  const y = ((1 - zoom) * height) / 2 + state.networkPanY;
  return `translate(${x.toFixed(1)} ${y.toFixed(1)}) scale(${zoom.toFixed(2)})`;
}

function renderNetworkMap(network, compact = false, fullscreen = false) {
  const width = 920;
  const height = compact ? 330 : 420;
  const mapId = fullscreen ? "fullscreen" : compact ? "compact" : "page";
  const allNodes = network.nodes || [];
  const nodeMap = new Map(allNodes.map((node) => [node.location_id, node]));
  const showAlternatives = state.networkMode === "ALL" && !compact;
  const routes = (network.routes || []).filter((route) => {
    const modeMatch = showAlternatives || route.route_type === "INBOUND_SHIPMENT";
    const materialMatch = state.globalFilters.material === "ALL" || route.material_id === state.globalFilters.material;
    const facilityMatch = state.globalFilters.facility === "ALL" || route.source_id === state.globalFilters.facility || route.destination_id === state.globalFilters.facility;
    return modeMatch && materialMatch && facilityMatch;
  });
  const connected = new Set(routes.flatMap((route) => [route.source_id, route.destination_id]));
  const nodes = allNodes.filter((node) => node.location_type !== "SUPPLIER" || connected.has(node.location_id));
  const nodeLayout = layoutNetworkNodes(nodes, width, height);
  const shapes = {
    PORT: (x, y) => `<path d="M ${x - 6} ${y - 5} h12 v8 h-12zM ${x} ${y - 9}v4M ${x - 9} ${y + 5}c3 3 6 3 9 0 3 3 6 3 9 0"/>`,
    FACTORY: (x, y) => `<path d="M ${x - 7} ${y + 7}v-12l5 3v-5l5 3v-4h4v15z"/>`,
    WAREHOUSE: (x, y) => `<path d="m ${x - 8} ${y - 2} 8-6 8 6v9h-16zM ${x - 3} ${y + 7}v-5h6v5"/>`,
    SUPPLIER: (x, y) => `<circle cx="${x}" cy="${y}" r="5"/><path d="M ${x - 8} ${y + 8}h16"/>`,
  };
  return `<div class="network-map-shell ${fullscreen ? "is-fullscreen" : ""}">
    ${compact ? "" : `<div class="map-toolbar" role="group" aria-label="Map view controls">
      <button class="icon-button" type="button" data-map-zoom="-0.25" aria-label="Zoom map out" title="Zoom out">${icon("minus")}</button>
      <output data-map-zoom-output aria-live="polite" aria-label="Map zoom level">${Math.round(state.networkZoom * 100)}%</output>
      <button class="icon-button" type="button" data-map-zoom="0.25" aria-label="Zoom map in" title="Zoom in">${icon("plus")}</button>
      <button class="icon-button" type="button" data-map-reset aria-label="Reset map view" title="Reset view">${icon("reset")}</button>
      ${fullscreen ? "" : `<button class="icon-button" type="button" data-map-fullscreen aria-label="Open full-screen network map" title="Full screen">${icon("expand")}</button>`}
    </div>`}
    <div class="network-map-stage">
      <svg class="network-map" data-network-map viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" tabindex="0" aria-labelledby="network-map-title-${mapId} network-map-desc-${mapId}">
        <title id="network-map-title-${mapId}">Indonesian supply network</title>
        <desc id="network-map-desc-${mapId}">${network.summary.facilities} factories, ${network.summary.warehouses} warehouses, ${network.summary.ports} ports, and ${network.summary.active_routes} active inbound routes. Use the visible zoom controls or keyboard plus, minus, and arrow keys. A route table follows the map.</desc>
        <g data-network-viewport transform="${networkTransform(width, height)}">
          <g class="island-silhouettes" fill-rule="evenodd" aria-hidden="true">${renderIndonesiaOutline(width, height)}</g>
          <g class="network-routes">
        ${routes.map((route) => {
          const sourceNode = nodeMap.get(route.source_id);
          const destinationNode = nodeMap.get(route.destination_id);
          if (!sourceNode || !destinationNode) return "";
          const source = nodeLayout.positions.get(sourceNode.location_id);
          const destination = nodeLayout.positions.get(destinationNode.location_id);
          return `<path class="network-route route-${escapeHtml(route.status)} ${route.route_type === "MITIGATION_OPTION" ? "route-alternative" : ""}" d="${routeCurve(source, destination)}"><title>${escapeHtml(route.label)}; ${escapeHtml(sentenceCase(route.status))}</title></path>`;
        }).join("")}
          </g>
          <g class="shipment-markers" aria-label="Shipments associated with active routes">
            ${routes.filter((route) => route.route_type === "INBOUND_SHIPMENT").map((route) => {
              const sourceNode = nodeMap.get(route.source_id);
              const destinationNode = nodeMap.get(route.destination_id);
              if (!sourceNode || !destinationNode) return "";
              const point = routeMidpoint(nodeLayout.positions.get(sourceNode.location_id), nodeLayout.positions.get(destinationNode.location_id));
              return `<g class="shipment-marker marker-${escapeHtml(route.status)}" transform="translate(${point.x.toFixed(1)} ${point.y.toFixed(1)})">
                <title>${escapeHtml(route.label)}. Shipment marker denotes the associated route, not a live AIS position.</title>
                <circle r="9"/><path d="M-5 1h10l-2 4h-6zM-2 1v-5h4v5M-5 7c2 1.5 4 1.5 6 0 2 1.5 4 1.5 6 0"/>
              </g>`;
            }).join("")}
          </g>
          <g class="network-nodes" role="list">
        ${nodes.map((node) => {
          const point = nodeLayout.positions.get(node.location_id);
          const selected = state.selectedNodeId === node.location_id;
          return `<g class="map-node node-${node.location_type.toLowerCase()} node-${node.status} ${selected ? "is-selected" : ""}" data-network-node="${escapeHtml(node.location_id)}" tabindex="0" role="button" aria-label="${escapeHtml(node.name)}, ${escapeHtml(sentenceCase(node.location_type))}, status ${escapeHtml(sentenceCase(node.status))}">
            <title>${escapeHtml(node.name)} · ${escapeHtml(node.city)} · ${escapeHtml(sentenceCase(node.status))}</title>
            <circle class="node-hit-area" cx="${point.x}" cy="${point.y}" r="15"/>
            <g class="node-shape">${shapes[node.location_type](point.x, point.y)}</g>
          </g>`;
        }).join("")}
          </g>
          <g class="map-city-labels" aria-hidden="true">
            ${nodeLayout.labels.map((label) => `<text x="${label.x.toFixed(1)}" y="${label.y.toFixed(1)}">${escapeHtml(label.city)}</text>`).join("")}
          </g>
        </g>
      </svg>
    </div>
    <div class="map-legend" aria-label="Map legend">
      <span><i class="node-key factory"></i>Factory</span><span><i class="node-key warehouse"></i>Warehouse</span><span><i class="node-key port"></i>Port</span>
      <span><i class="route-key stable"></i>On time</span><span><i class="route-key delayed"></i>Delayed</span><span><i class="route-key critical"></i>Critical</span><span><i class="ship-key"></i>Associated shipment</span>
    </div>
    <div class="map-provenance"><span>Basemap: Natural Earth 1:50m · public domain</span><span>Route geometry is modeled; shipment markers are not live AIS positions.</span></div>
  </div>`;
}

function renderRouteTable(network) {
  const config = state.tables.routes;
  const query = config.query.trim().toLowerCase();
  const filtered = (network.routes || []).filter((route) => {
    const modeMatch = state.networkMode === "ALL" || route.route_type === "INBOUND_SHIPMENT";
    const statusMatch = config.filter === "ALL" || route.status === config.filter;
    const materialMatch = state.globalFilters.material === "ALL" || route.material_id === state.globalFilters.material;
    const facilityMatch = state.globalFilters.facility === "ALL" || route.source_id === state.globalFilters.facility || route.destination_id === state.globalFilters.facility;
    const haystack = [route.route_id, route.label, route.material_id, route.source_id, route.destination_id].join(" ").toLowerCase();
    return modeMatch && statusMatch && materialMatch && facilityMatch && (!query || haystack.includes(query));
  });
  const nodes = new Map(network.nodes.map((node) => [node.location_id, node]));
  const sorted = sortRows(filtered, "routes", {
    route: (route) => route.label,
    type: (route) => route.route_type,
    material: (route) => route.material_id,
    delay: (route) => Number(route.delay_hours),
    status: (route) => route.status,
    exposure: (route) => Number(route.exposure_idr),
  });
  const page = paginateRows(sorted, "routes");
  return `<div class="table-actions">
      <label class="search-field" for="route-search">${icon("search")}<span class="sr-only">Search routes</span><input id="route-search" type="search" value="${escapeHtml(config.query)}" placeholder="Search route or material" autocomplete="off"></label>
      <label class="select-field">Status<select data-route-status aria-label="Filter routes by status"><option value="ALL">All statuses</option>${["STABLE", "DELAYED", "CRITICAL", "AVAILABLE"].map((status) => `<option value="${status}"${config.filter === status ? " selected" : ""}>${sentenceCase(status)}</option>`).join("")}</select></label>
      <button class="button button-secondary" type="button" data-export-table="routes">${icon("download")}Export CSV</button>
    </div>
    <div class="table-wrap">
    <table class="data-table route-table">
      <thead><tr>${sortableHeader("Route", "routes", "route")}${sortableHeader("Type", "routes", "type")}${sortableHeader("Material", "routes", "material")}${sortableHeader("Lead / delay", "routes", "delay")}${sortableHeader("Status", "routes", "status")}${sortableHeader("Modeled value", "routes", "exposure")}</tr></thead>
      <tbody>${page.rows.map((route) => `<tr>
        <td><strong>${escapeHtml(nodes.get(route.source_id)?.city || route.source_id)} → ${escapeHtml(nodes.get(route.destination_id)?.city || route.destination_id)}</strong><small>${escapeHtml(route.route_id)}</small></td>
        <td>${escapeHtml(route.route_type === "INBOUND_SHIPMENT" ? "Inbound shipment" : "Response option")}</td>
        <td class="mono">${escapeHtml(route.material_id)}</td>
        <td>${formatNumber(route.delay_hours, 0)}h</td>
        <td>${stateBadge(route.status)}</td>
        <td>${formatCurrency(route.exposure_idr, true)}</td>
      </tr>`).join("")}</tbody>
    </table>
  </div>${tableFooter("routes", sorted.length, page.pages, "routes")}`;
}

function projectionHour(simulation, timestamp) {
  if (!timestamp) return null;
  return Math.max(0, (new Date(timestamp) - new Date(simulation.start_at)) / 3600000);
}

function projectionArrivalEvents(baseline, response, recommended) {
  const events = new Map();
  const addEvent = (hour, label, quantity, unit) => {
    const key = String(hour);
    const current = events.get(key) || { hour, labels: new Set(), quantity: 0, unit };
    current.labels.add(label);
    current.quantity += Number(quantity);
    events.set(key, current);
  };
  (baseline.inventory_by_time || []).filter((point) => Number(point.arrival_quantity) > 0).forEach((point) => {
    addEvent(Math.max(0, Number(point.hour) - 1), "Original delayed inbound", point.arrival_quantity, point.unit);
  });
  const allocationQuantityByProjectionPoint = new Map();
  (recommended.allocations || []).forEach((allocation) => {
    const arrivalHour = projectionHour(response, allocation.arrival_at);
    if (arrivalHour == null) return;
    const normalizedHour = Math.max(0, Math.round(arrivalHour));
    addEvent(normalizedHour, allocation.source_name, allocation.quantity, allocation.unit);
    allocationQuantityByProjectionPoint.set(normalizedHour + 1, (allocationQuantityByProjectionPoint.get(normalizedHour + 1) || 0) + Number(allocation.quantity));
  });
  (response.inventory_by_time || []).filter((point) => Number(point.arrival_quantity) > 0).forEach((point) => {
    const allocationQuantity = allocationQuantityByProjectionPoint.get(Number(point.hour)) || 0;
    const originalQuantity = Math.max(0, Number(point.arrival_quantity) - allocationQuantity);
    if (originalQuantity > 0.001 && !events.has(String(Math.max(0, Number(point.hour) - 1)))) {
      addEvent(Math.max(0, Number(point.hour) - 1), "Original delayed inbound", originalQuantity, point.unit);
    }
  });
  return [...events.values()]
    .map((event) => ({ ...event, labels: [...event.labels] }))
    .sort((a, b) => a.hour - b.hour);
}

function separateEndLabels(entries, top, bottom, minimumGap = 25) {
  const sorted = entries.map((entry) => ({ ...entry, labelY: Math.max(top, Math.min(bottom, entry.y)) })).sort((a, b) => a.labelY - b.labelY);
  if (sorted.length === 2 && sorted[1].labelY - sorted[0].labelY < minimumGap) {
    const midpoint = (sorted[0].labelY + sorted[1].labelY) / 2;
    sorted[0].labelY = Math.max(top, Math.min(bottom - minimumGap, midpoint - minimumGap / 2));
    sorted[1].labelY = sorted[0].labelY + minimumGap;
  }
  return new Map(sorted.map((entry) => [entry.id, entry]));
}

function renderInventoryProjection(analysis, recommended) {
  const baseline = analysis.baseline.simulation;
  const response = recommended.simulation;
  const fullBaselinePoints = baseline.inventory_by_time || [];
  const fullResponsePoints = response.inventory_by_time || [];
  const fullHorizon = Math.max(baseline.horizon_hours, response.horizon_hours, 1);
  const requestedHorizon = state.inventoryRange === "ALL" ? fullHorizon : Number(state.inventoryRange);
  const horizon = Math.min(fullHorizon, requestedHorizon);
  const baselinePoints = fullBaselinePoints.filter((point) => Number(point.hour) <= horizon);
  const responsePoints = fullResponsePoints.filter((point) => Number(point.hour) <= horizon);
  if (!baselinePoints.length || !responsePoints.length) {
    return emptyState("Projection unavailable", "Run a new analysis to generate hourly inventory points.");
  }
  const width = 1120;
  const height = 430;
  const margin = { top: 48, right: 172, bottom: 64, left: 82 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const observedMax = Math.max(
    baseline.safety_stock,
    ...baselinePoints.map((point) => Number(point.quantity)),
    ...responsePoints.map((point) => Number(point.quantity)),
    1,
  );
  const maxQuantity = observedMax * 1.12;
  const x = (hour) => margin.left + (Number(hour) / horizon) * innerWidth;
  const y = (quantity) => margin.top + innerHeight - (Number(quantity) / maxQuantity) * innerHeight;
  const baselinePath = linePath(baselinePoints, (point) => x(point.hour), (point) => y(point.quantity));
  const responsePath = linePath(responsePoints, (point) => x(point.hour), (point) => y(point.quantity));
  const safetyY = y(baseline.safety_stock);
  const stockoutStart = projectionHour(baseline, baseline.stockout_at);
  const recovery = projectionHour(baseline, baseline.recovery_at) ?? horizon;
  const stockoutWidth = stockoutStart == null ? 0 : Math.max(0, x(Math.min(recovery, horizon)) - x(stockoutStart));
  const events = projectionArrivalEvents(baseline, response, recommended).filter((event) => event.hour <= horizon);
  const plotEnd = margin.left + innerWidth;
  const plotBottom = margin.top + innerHeight;
  const endLabels = separateEndLabels([
    { id: "baseline", y: y(baselinePoints.at(-1).quantity), value: baselinePoints.at(-1).quantity },
    { id: "recommended", y: y(responsePoints.at(-1).quantity), value: responsePoints.at(-1).quantity },
  ], margin.top + 13, plotBottom - 13);
  const yTicks = [0, 0.5, 1];
  const xTicks = [...new Set([0, Math.round(horizon / 4), Math.round(horizon / 2), Math.round(horizon * 0.75), horizon])];
  const pointByHour = new Map(responsePoints.map((point) => [Number(point.hour), point]));
  const eventByHour = new Map(events.map((event) => [Math.round(event.hour), event]));
  const hitWidth = Math.max(5, innerWidth / Math.max(1, baselinePoints.length));
  return `<div class="chart-shell inventory-chart-shell" data-inventory-chart>
    <div class="chart-command-bar">
      <div class="chart-data-note"><span>${icon("check")}</span><strong>Deterministic projection</strong><span>${Math.max(baselinePoints.length, responsePoints.length)} hourly points · ${horizon}h view</span></div>
      <div class="chart-actions"><div class="segmented-filter compact chart-range" aria-label="Inventory chart horizon">${[["24", "24h"], ["72", "72h"], ["ALL", "Full"]].map(([value, label]) => `<button type="button" data-inventory-range="${value}" class="${state.inventoryRange === value ? "is-selected" : ""}" aria-pressed="${state.inventoryRange === value}">${label}</button>`).join("")}</div><button class="button button-secondary button-compact" type="button" data-export-table="inventory">${icon("download")}Export CSV</button></div>
    </div>
    <p class="chart-mobile-hint">Scroll the chart horizontally to inspect the complete time horizon.</p>
    <div class="chart-viewport" tabindex="0" aria-label="Scrollable inventory projection chart">
    <svg class="chart-svg inventory-chart" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-labelledby="inventory-chart-title inventory-chart-desc">
      <title id="inventory-chart-title">Hourly baseline and recommended inventory projection</title>
      <desc id="inventory-chart-desc">Baseline downtime is ${baseline.downtime_hours.toFixed(1)} hours. Recommended response downtime is ${response.downtime_hours.toFixed(1)} hours. The safety stock threshold is ${formatNumber(baseline.safety_stock)} ${escapeHtml(baseline.unit)}.</desc>
      <defs><clipPath id="inventory-plot-clip"><rect x="${margin.left}" y="${margin.top}" width="${innerWidth}" height="${innerHeight}"/></clipPath></defs>
      ${stockoutStart == null ? "" : `<rect class="stockout-window" x="${x(stockoutStart)}" y="${margin.top}" width="${stockoutWidth}" height="${innerHeight}"/>`}
      ${yTicks.map((tick) => {
        const tickY = margin.top + innerHeight - tick * innerHeight;
        return `<line class="chart-gridline" x1="${margin.left}" y1="${tickY}" x2="${margin.left + innerWidth}" y2="${tickY}"/><text class="chart-axis-label" x="${margin.left - 10}" y="${tickY + 4}" text-anchor="end">${formatNumber(maxQuantity * tick, 0)}</text>`;
      }).join("")}
      ${xTicks.map((tick) => `<text class="chart-axis-label" x="${x(tick)}" y="${height - 26}" text-anchor="middle">+${tick}h</text>`).join("")}
      <text class="chart-axis-title" x="${margin.left + innerWidth / 2}" y="${height - 5}" text-anchor="middle">Hours from incident detection</text>
      <text class="chart-axis-title" transform="translate(17 ${margin.top + innerHeight / 2}) rotate(-90)" text-anchor="middle">Inventory (${escapeHtml(baseline.unit)})</text>
      <g clip-path="url(#inventory-plot-clip)">
        ${events.map((event) => `<line class="inventory-event-line" x1="${x(event.hour)}" y1="${margin.top}" x2="${x(event.hour)}" y2="${plotBottom}"/>`).join("")}
      </g>
      <line class="safety-line" x1="${margin.left}" y1="${safetyY}" x2="${margin.left + innerWidth}" y2="${safetyY}"/>
      <text class="safety-label" x="${margin.left + 7}" y="${Math.max(margin.top + 12, safetyY - 7)}">Safety stock · ${formatNumber(baseline.safety_stock)} ${escapeHtml(baseline.unit)}</text>
      <g clip-path="url(#inventory-plot-clip)"><path class="chart-line chart-line-baseline" d="${baselinePath}"/><path class="chart-line chart-line-recommended" d="${responsePath}"/></g>
      <g class="inventory-hit-layer" aria-label="Hourly inventory points">${baselinePoints.map((point) => {
        const hour = Number(point.hour);
        const responsePoint = pointByHour.get(hour) || point;
        const event = eventByHour.get(hour);
        const label = `Hour ${hour}. Baseline ${formatNumber(point.quantity)} ${baseline.unit}. Recommended ${formatNumber(responsePoint.quantity)} ${baseline.unit}${event ? `. Arrival ${formatNumber(event.quantity)} ${event.unit} from ${event.labels.join(" and ")}` : ""}.`;
        return `<rect x="${x(hour) - hitWidth / 2}" y="${margin.top}" width="${hitWidth}" height="${innerHeight}" tabindex="0" role="button" aria-label="${escapeHtml(label)}" data-inventory-hit data-hour="${hour}" data-baseline="${Number(point.quantity)}" data-recommended="${Number(responsePoint.quantity)}" data-unit="${escapeHtml(baseline.unit)}" data-event="${escapeHtml(event ? `${event.labels.join(" / ")} · +${formatNumber(event.quantity)} ${event.unit}` : "")}"/>`;
      }).join("")}</g>
      ${events.map((event, index) => `<g class="inventory-event-marker"><circle cx="${x(event.hour)}" cy="${margin.top + 11}" r="9"/><text x="${x(event.hour)}" y="${margin.top + 14}" text-anchor="middle">${index + 1}</text></g>`).join("")}
      ${["baseline", "recommended"].map((id) => {
        const label = endLabels.get(id);
        const sourceY = label.y;
        const className = id === "baseline" ? "label-baseline" : "label-recommended";
        const name = id === "baseline" ? "Baseline" : "Recommended";
        return `<path class="end-label-connector ${className}" d="M ${plotEnd} ${sourceY.toFixed(1)} L ${plotEnd + 10} ${sourceY.toFixed(1)} L ${plotEnd + 18} ${label.labelY.toFixed(1)}"/><text class="direct-label ${className}" x="${plotEnd + 23}" y="${(label.labelY - 2).toFixed(1)}"><tspan>${name}</tspan><tspan class="direct-label-value" x="${plotEnd + 23}" dy="12">${formatNumber(label.value, 0)} ${escapeHtml(baseline.unit)}</tspan></text>`;
      }).join("")}
    </svg><div class="chart-tooltip" data-inventory-tooltip role="status" hidden></div></div>
    <div class="chart-legend"><span><i class="line-key baseline"></i>Baseline, dashed</span><span><i class="line-key recommended"></i>Recommended, solid</span><span><i class="band-key"></i>Baseline shortage interval</span></div>
    ${events.length ? `<ol class="projection-events" aria-label="Modeled inventory arrivals">${events.map((event, index) => `<li><span>${index + 1}</span><div><strong>+${formatNumber(event.hour, 0)}h · ${escapeHtml(event.labels.join(" / "))}</strong><small>Modeled arrival +${formatNumber(event.quantity, 0)} ${escapeHtml(event.unit)}</small></div></li>`).join("")}</ol>` : ""}
    <dl class="projection-summary">
      <div><dt>Safety breach</dt><dd>${escapeHtml(formatDateTime(baseline.safety_breach_at))}</dd></div>
      <div><dt>Baseline stockout</dt><dd>${escapeHtml(formatDateTime(baseline.stockout_at))}</dd></div>
      <div><dt>Recommended path</dt><dd>${response.stockout_at ? `Recovers ${escapeHtml(formatDateTime(response.recovery_at))}` : "No stockout"}</dd></div>
      <div><dt>Downtime avoided</dt><dd>${formatNumber(Math.max(0, baseline.downtime_hours - response.downtime_hours))}h</dd></div>
    </dl>
  </div>`;
}

function renderScenarioFrontier(analysis) {
  const scenarios = [analysis.baseline, ...analysis.scenarios];
  const recommendedId = analysis.recommended_scenario_id;
  if (!state.selectedScenarioId || !scenarios.some((scenario) => scenario.scenario_id === state.selectedScenarioId)) state.selectedScenarioId = recommendedId;
  const selected = scenarios.find((scenario) => scenario.scenario_id === state.selectedScenarioId) || scenarios[0];
  const selectedIndex = scenarios.findIndex((scenario) => scenario.scenario_id === selected.scenario_id);
  const width = 760;
  const height = 420;
  const margin = { top: 42, right: 36, bottom: 66, left: 78 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const maxCost = Math.max(...scenarios.map((item) => Number(item.cost_breakdown.logistics_and_purchase_idr)), 1);
  const maxDowntime = Math.max(...scenarios.map((item) => Number(item.simulation.downtime_hours)), 1);
  const x = (value) => margin.left + (Number(value) / maxCost) * innerWidth;
  const y = (value) => margin.top + innerHeight - (Number(value) / maxDowntime) * innerHeight;
  const selectedRisks = [...(selected.risks || []), ...(selected.rejected_reasons || [])];
  return `<div class="frontier-workspace" id="scenario-frontier-body">
    <div class="chart-shell frontier-chart-shell">
    <div class="chart-data-note"><span>${icon("check")}</span><strong>Bounded comparison</strong><span>Select or focus a point to inspect its assumptions</span></div>
    <div class="chart-viewport" tabindex="0" aria-label="Scrollable response scenario frontier">
    <svg class="chart-svg frontier-chart" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-labelledby="frontier-title frontier-desc">
      <title id="frontier-title">Response cost versus production downtime frontier</title>
      <desc id="frontier-desc">${scenarios.length} scenarios. The recommended scenario is marked with a diamond and direct label.</desc>
      ${[0, 0.5, 1].map((tick) => {
        const tickX = margin.left + tick * innerWidth;
        const tickY = margin.top + innerHeight - tick * innerHeight;
        return `<line class="chart-gridline" x1="${tickX}" y1="${margin.top}" x2="${tickX}" y2="${margin.top + innerHeight}"/><line class="chart-gridline" x1="${margin.left}" y1="${tickY}" x2="${margin.left + innerWidth}" y2="${tickY}"/><text class="chart-axis-label" x="${tickX}" y="${height - 26}" text-anchor="middle">${escapeHtml(formatCurrency(maxCost * tick, true).replace("IDR ", ""))}</text><text class="chart-axis-label" x="${margin.left - 10}" y="${tickY + 4}" text-anchor="end">${formatNumber(maxDowntime * tick)}h</text>`;
      }).join("")}
      <text class="chart-axis-title" x="${margin.left + innerWidth / 2}" y="${height - 4}" text-anchor="middle">Response cost (IDR)</text>
      <text class="chart-axis-title" transform="translate(16 ${margin.top + innerHeight / 2}) rotate(-90)" text-anchor="middle">Modeled downtime (hours)</text>
      ${scenarios.map((scenario, index) => {
        const cx = x(scenario.cost_breakdown.logistics_and_purchase_idr);
        const cy = y(scenario.simulation.downtime_hours);
        const recommended = scenario.scenario_id === recommendedId;
        const shape = recommended
          ? `<path class="frontier-point recommended" d="M ${cx} ${cy - 8} L ${cx + 8} ${cy} L ${cx} ${cy + 8} L ${cx - 8} ${cy} Z"/>`
          : scenario.feasible
            ? `<circle class="frontier-point feasible" cx="${cx}" cy="${cy}" r="6"/>`
            : `<g class="frontier-point infeasible"><path d="M ${cx - 5} ${cy - 5} l10 10M ${cx + 5} ${cy - 5} l-10 10"/></g>`;
        const labelOnLeft = cx > width - 150;
        const labelX = labelOnLeft ? cx - 12 : cx + 12;
        const labelY = Math.max(margin.top + 12, Math.min(margin.top + innerHeight - 8, cy - 10));
        const pointLabel = `S${index + 1}, ${scenario.name}. ${formatCurrency(scenario.cost_breakdown.logistics_and_purchase_idr)} response cost, ${formatNumber(scenario.simulation.downtime_hours)} hours downtime, ${scenario.feasible ? "feasible" : "constraint failed"}.`;
        return `<g class="frontier-point-target ${selected.scenario_id === scenario.scenario_id ? "is-selected" : ""}" tabindex="0" role="button" aria-pressed="${selected.scenario_id === scenario.scenario_id}" aria-label="${escapeHtml(pointLabel)}" data-scenario-point="${escapeHtml(scenario.scenario_id)}" data-scenario-index="S${index + 1}" data-scenario-name="${escapeHtml(scenario.name)}" data-scenario-cost="${escapeHtml(formatCurrency(scenario.cost_breakdown.logistics_and_purchase_idr))}" data-scenario-downtime="${formatNumber(scenario.simulation.downtime_hours)}h" data-scenario-status="${scenario.feasible ? "Feasible" : "Constraint failed"}"><circle class="frontier-hit-area" cx="${cx}" cy="${cy}" r="18"/><title>${escapeHtml(pointLabel)}</title>${shape}${recommended ? `<text class="direct-label" x="${labelX}" y="${labelY}" text-anchor="${labelOnLeft ? "end" : "start"}">Recommended</text>` : ""}</g>`;
      }).join("")}
    </svg>
    <div class="chart-tooltip" data-frontier-tooltip role="status" hidden></div></div>
    <div class="chart-legend"><span><i class="shape-key diamond"></i>Recommended</span><span><i class="shape-key circle"></i>Feasible</span><span><i class="shape-key cross">×</i>Constraint failed</span></div>
    </div>
    <aside class="scenario-detail-panel" aria-live="polite" aria-label="Selected scenario details">
      <div class="scenario-detail-heading"><span class="scenario-index">S${selectedIndex + 1}</span><div><span class="eyebrow">Selected scenario</span><h3>${escapeHtml(selected.name)}</h3></div>${selected.scenario_id === recommendedId ? '<span class="recommended-label">Recommended</span>' : ""}</div>
      <dl class="scenario-detail-metrics"><div><dt>Response cost</dt><dd>${formatCurrency(selected.cost_breakdown.logistics_and_purchase_idr, true)}</dd></div><div><dt>Downtime</dt><dd>${formatNumber(selected.simulation.downtime_hours)}h</dd></div><div><dt>Total impact</dt><dd>${formatCurrency(selected.cost_breakdown.total_idr, true)}</dd></div><div><dt>Feasibility</dt><dd>${selected.feasible ? stateBadge("FEASIBLE") : stateBadge("CONSTRAINT_FAILED")}</dd></div></dl>
      <div class="scenario-detail-section"><h4>Mitigation composition</h4>${selected.allocations?.length ? selected.allocations.map((allocation) => `<div class="scenario-allocation"><span>${escapeHtml(allocation.source_name)}</span><strong>${formatNumber(allocation.quantity)} ${escapeHtml(allocation.unit)}</strong></div>`).join("") : '<p class="muted-copy">No alternative allocation; waits for the original inbound flow.</p>'}</div>
      <div class="scenario-detail-section"><h4>${selected.feasible ? "Decision evidence" : "Constraint findings"}</h4><ul class="compact-evidence">${(selected.feasible ? selected.constraints_passed || [] : selectedRisks).slice(0, 4).map((item) => `<li>${icon(selected.feasible ? "check" : "alert")}<span>${escapeHtml(item)}</span></li>`).join("") || "<li>No additional findings recorded.</li>"}</ul></div>
    </aside>
  </div>`;
}

function renderAllocationComposition(scenario) {
  const allocations = scenario.allocations || [];
  if (!allocations.length) return emptyState("No mitigation allocation", "The selected scenario waits for the original inbound shipment.");
  const total = allocations.reduce((sum, item) => sum + Number(item.quantity), 0);
  const palette = ["allocation-blue", "allocation-teal", "allocation-amber", "allocation-slate"];
  return `<div class="allocation-composition">
    <div class="composition-bar" role="img" aria-label="${allocations.map((item) => `${item.source_name} ${formatNumber(item.quantity)} ${item.unit}`).join(", ")}">
      ${allocations.map((item, index) => `<span class="${palette[index % palette.length]}" style="width:${(Number(item.quantity) / total) * 100}%" title="${escapeHtml(item.source_name)}"></span>`).join("")}
    </div>
    <div class="allocation-list">
      ${allocations.map((item, index) => `<div class="allocation-item">
        <span class="allocation-marker ${palette[index % palette.length]}"></span>
        <div><strong>${escapeHtml(item.source_name)}</strong><small>${escapeHtml(sentenceCase(item.option_type))} · arrives ${escapeHtml(formatDateTime(item.arrival_at))}</small></div>
        <div class="allocation-quantity"><strong>${formatNumber(item.quantity)} ${escapeHtml(item.unit)}</strong><small>${formatNumber((Number(item.quantity) / total) * 100, 0)}% · ${formatNumber(item.reliability * 100, 0)}% reliability</small></div>
      </div>`).join("")}
    </div>
  </div>`;
}

function renderImpactChain(item, analysis, recommended) {
  const nodes = [
    { label: "Incident", value: item.event_type, meta: `+${item.delay_hours}h disruption` },
    { label: "Inbound", value: item.shipment_id, meta: item.route },
    { label: "Material", value: analysis.affected_material.name, meta: `${formatNumber(analysis.hours_of_cover)}h cover` },
    { label: "Production", value: analysis.facility.name, meta: `${formatNumber(analysis.baseline.simulation.downtime_hours)}h baseline outage` },
    { label: "Response", value: recommended.name, meta: `${formatNumber(recommended.simulation.downtime_hours)}h residual downtime` },
  ];
  return `<ol class="impact-chain" aria-label="Incident to production impact chain">
    ${nodes.map((node, index) => `<li>
      <span class="chain-step">${index + 1}</span>
      <div><small>${escapeHtml(node.label)}</small><strong>${escapeHtml(node.value)}</strong><span>${escapeHtml(node.meta)}</span></div>
      ${index < nodes.length - 1 ? `<span class="chain-arrow" aria-hidden="true">${icon("arrow")}</span>` : ""}
    </li>`).join("")}
  </ol>`;
}

function globallyFilteredPortfolio() {
  return state.portfolio.filter((item) => {
    const facilityMatch = state.globalFilters.facility === "ALL" || item.facility_id === state.globalFilters.facility;
    const materialMatch = state.globalFilters.material === "ALL" || item.material_id === state.globalFilters.material;
    const severityMatch = state.globalFilters.severity === "ALL" || item.severity === state.globalFilters.severity;
    return facilityMatch && materialMatch && severityMatch;
  });
}

function renderGlobalFilters() {
  const facilities = [...new Map(state.portfolio.map((item) => [item.facility_id, { id: item.facility_id, name: item.facility_name }])).values()];
  const materials = [...new Map(state.portfolio.map((item) => [item.material_id, { id: item.material_id, name: item.material_name }])).values()];
  const active = Object.values(state.globalFilters).some((value) => value !== "ALL");
  return `<section class="global-filter-bar" aria-label="Global operational filters">
    <div class="global-filter-label">${icon("filter")}<div><strong>Operational scope</strong><span>Applied across portfolio and network views</span></div></div>
    <label>Facility<select data-global-filter="facility"><option value="ALL">All facilities</option>${facilities.map((facility) => `<option value="${escapeHtml(facility.id)}"${state.globalFilters.facility === facility.id ? " selected" : ""}>${escapeHtml(facility.name)}</option>`).join("")}</select></label>
    <label>Material<select data-global-filter="material"><option value="ALL">All materials</option>${materials.map((material) => `<option value="${escapeHtml(material.id)}"${state.globalFilters.material === material.id ? " selected" : ""}>${escapeHtml(material.name)}</option>`).join("")}</select></label>
    <label>Severity<select data-global-filter="severity"><option value="ALL">All severities</option>${["CRITICAL", "HIGH", "INFO"].map((severity) => `<option value="${severity}"${state.globalFilters.severity === severity ? " selected" : ""}>${sentenceCase(severity)}</option>`).join("")}</select></label>
    <button class="button button-secondary button-compact" type="button" data-clear-global-filters ${active ? "" : "disabled"}>Clear filters</button>
  </section>`;
}

function filteredRiskMatrix(matrix) {
  const facilities = state.globalFilters.facility === "ALL" ? matrix.facilities : matrix.facilities.filter((facility) => facility.facility_id === state.globalFilters.facility);
  const materials = state.globalFilters.material === "ALL" ? matrix.materials : matrix.materials.filter((material) => material.material_id === state.globalFilters.material);
  const facilityIds = new Set(facilities.map((item) => item.facility_id));
  const materialIds = new Set(materials.map((item) => item.material_id));
  return { facilities, materials, cells: matrix.cells.filter((cell) => facilityIds.has(cell.facility_id) && materialIds.has(cell.material_id)) };
}

function renderOperationalBriefing(overview, scopedItems) {
  const previous = overview.trend.at(-2);
  const current = overview.trend.at(-1);
  const exposureDelta = previous && current ? Number(current.exposure_idr) - Number(previous.exposure_idr) : 0;
  const exposureDirection = exposureDelta > 0 ? "increased" : exposureDelta < 0 ? "decreased" : "is unchanged";
  const top = scopedItems[0];
  const pending = state.drafts.filter((draft) => draft.status === "PENDING_APPROVAL" && scopedItems.some((item) => item.incident_id === draft.incident_id)).length;
  return `<section class="operational-briefing" aria-labelledby="operational-briefing-title">
    <div class="briefing-heading"><div><p class="eyebrow">Since previous snapshot</p><h2 id="operational-briefing-title">What changed</h2></div><span>${escapeHtml(formatDateTime(current?.observed_at || overview.generated_at))} WITA</span></div>
    <div class="briefing-items">
      <article class="briefing-item ${exposureDelta > 0 ? "is-critical" : "is-positive"}"><span>${icon(exposureDelta > 0 ? "alert" : "check")}</span><div><strong>Exposure ${exposureDirection}</strong><p>${exposureDelta === 0 ? "No change in modeled baseline exposure." : `${exposureDelta > 0 ? "+" : "−"}${formatCurrency(Math.abs(exposureDelta), true)} versus the previous modeled snapshot.`}</p></div></article>
      <article class="briefing-item"><span>${icon("route")}</span><div><strong>${top ? top.title : "No incidents in scope"}</strong><p>${top ? `${top.facility_name} · ${formatNumber(top.hours_of_cover)}h inventory cover · ${formatCurrency(top.baseline_exposure_idr, true)} exposure.` : "Adjust the global filters to widen the operational scope."}</p></div></article>
      <article class="briefing-item ${pending ? "is-warning" : "is-positive"}"><span>${icon(pending ? "clock" : "check")}</span><div><strong>${pending} approval${pending === 1 ? "" : "s"} pending</strong><p>${pending ? "Human authorization is required before any response package can progress." : "No approval package in the current scope requires action."}</p></div></article>
    </div>
    <p class="briefing-provenance">Derived from persisted operational snapshots and current local approval records.</p>
  </section>`;
}

function renderOverviewPage() {
  const overview = state.overview;
  const scopedItems = globallyFilteredPortfolio();
  const activeItems = scopedItems.filter((item) => item.active);
  const activeFilters = Object.values(state.globalFilters).some((value) => value !== "ALL");
  const kpis = activeFilters ? {
    active_incidents: activeItems.length,
    critical_incidents: activeItems.filter((item) => item.severity === "CRITICAL").length,
    at_risk_facilities: new Set(activeItems.map((item) => item.facility_id)).size,
    delayed_routes: activeItems.filter((item) => Number(item.delay_hours) > 0).length,
    baseline_exposure_idr: activeItems.reduce((sum, item) => sum + Number(item.baseline_exposure_idr), 0),
    pending_approvals: state.drafts.filter((draft) => draft.status === "PENDING_APPROVAL" && activeItems.some((item) => item.incident_id === draft.incident_id)).length,
  } : overview.kpis;
  const priorityRows = scopedItems.slice(0, 4).map((item) => `<a class="priority-row" href="/incidents/${encodeURIComponent(item.incident_id)}" data-link>
    <span class="severity-rail severity-${item.severity.toLowerCase()}" aria-hidden="true"></span>
    <div><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.facility_name)} · ${escapeHtml(item.material_name)}</small></div>
    <div class="priority-impact"><strong>${formatCurrency(item.baseline_exposure_idr, true)}</strong><small>${formatNumber(item.baseline_downtime_hours)}h exposure</small></div>
    ${icon("arrow")}
  </a>`).join("");
  ui.pageRoot.innerHTML = `
    ${pageHeading({
      eyebrow: "Network command",
      title: "Executive overview",
      description: "A portfolio-level view of disruption exposure, response readiness, and material risk across the Indonesian supply network.",
      summary: `<span class="snapshot-time">Snapshot · ${escapeHtml(formatDateTime(overview.generated_at))} WITA</span>`,
    })}
    ${renderGlobalFilters()}
    ${renderOperationalBriefing(overview, scopedItems)}
    ${kpiStrip([
      { label: "Active incidents", value: String(kpis.active_incidents), detail: `${kpis.critical_incidents} critical`, tone: kpis.critical_incidents ? "tone-critical" : "" },
      { label: "At-risk facilities", value: String(kpis.at_risk_facilities), detail: `${kpis.delayed_routes} delayed routes`, tone: "tone-warning" },
      { label: "Baseline exposure", value: formatCurrency(kpis.baseline_exposure_idr, true), detail: "modeled downtime cost" },
      { label: "Pending approvals", value: String(kpis.pending_approvals), detail: kpis.pending_approvals ? "human action required" : "inbox clear", tone: kpis.pending_approvals ? "tone-warning" : "tone-success" },
    ])}
    <div class="dashboard-grid">
      <section class="panel span-8">
        ${panelHeader("Network exposure trend", "Modeled production downtime exposure across the latest seven operational snapshots.", '<span class="section-caption">IDR · baseline</span>')}
        <div class="panel-body">${renderExposureTrend(overview.trend)}</div>
      </section>
      <section class="panel span-4 priority-panel">
        ${panelHeader("Priority incidents", "Highest current operational exposure.", `<a class="text-link" href="/incidents" data-link>View portfolio ${icon("arrow")}</a>`)}
        <div class="priority-list">${priorityRows}</div>
      </section>
      <section class="panel span-8">
        ${panelHeader("Inter-island network exposure", "Current inbound routes, facilities, warehouses, and port dependencies.", `<a class="text-link" href="/network" data-link>Explore network ${icon("arrow")}</a>`)}
        <div class="panel-body panel-body-map">${renderNetworkMap(state.network, true)}</div>
      </section>
      <section class="panel span-4">
        ${panelHeader("Approval activity", "Pending decisions and cumulative approved actions.")}
        <div class="panel-body">
          ${renderApprovalTrend(overview.trend)}
          <div class="approval-summary-grid">
            <div><span>Pending</span><strong>${overview.approval_summary.pending}</strong></div>
            <div><span>Approved</span><strong>${overview.approval_summary.approved}</strong></div>
            <div><span>Awaiting package</span><strong>${overview.approval_summary.not_created}</strong></div>
          </div>
          <a class="button button-secondary button-full" href="/approvals" data-link>Open approval inbox</a>
        </div>
      </section>
      <section class="panel span-12">
        ${panelHeader("Facility-material risk heatmap", "Risk combines incident severity, route delay, and current hours of inventory cover.", '<span class="section-caption">Values show hours of cover</span>')}
        <div class="panel-body">${renderRiskMatrix(filteredRiskMatrix(overview.risk_matrix))}</div>
      </section>
    </div>`;
}

function selectedNetworkNode() {
  return state.network.nodes.find((node) => node.location_id === state.selectedNodeId) || null;
}

function renderNetworkNodeDetail(node) {
  if (!node) {
    return `<div class="network-detail-placeholder"><span>${icon("route")}</span><strong>Select a network node</strong><p>Choose a facility, warehouse, or port on the map to inspect connected routes.</p></div>`;
  }
  const connections = state.network.routes.filter((route) => route.source_id === node.location_id || route.destination_id === node.location_id);
  return `<div class="network-node-detail">
    <div class="detail-title-row"><div><span class="node-type-label">${escapeHtml(sentenceCase(node.location_type))}</span><h3>${escapeHtml(node.name)}</h3><p>${escapeHtml(node.city)} · ${escapeHtml(node.island)}</p></div>${stateBadge(node.status)}</div>
    <dl class="detail-kv"><div><dt>Node ID</dt><dd class="mono">${escapeHtml(node.location_id)}</dd></div><div><dt>Connected paths</dt><dd>${connections.length}</dd></div><div><dt>Coordinates</dt><dd>${formatNumber(node.latitude, 3)}, ${formatNumber(node.longitude, 3)}</dd></div></dl>
    <div class="connected-routes"><h4>Connected routes</h4>${connections.length ? connections.slice(0, 5).map((route) => `<div><span>${escapeHtml(route.label)}</span>${stateBadge(route.status)}</div>`).join("") : "<p>No active route records.</p>"}</div>
  </div>`;
}

function renderNetworkPage() {
  const summary = state.network.summary;
  const modeControl = `<div class="segmented-filter compact" aria-label="Network route view">
    <button type="button" data-network-mode="INBOUND" class="${state.networkMode === "INBOUND" ? "is-selected" : ""}" aria-pressed="${state.networkMode === "INBOUND"}">Inbound network</button>
    <button type="button" data-network-mode="ALL" class="${state.networkMode === "ALL" ? "is-selected" : ""}" aria-pressed="${state.networkMode === "ALL"}">Include response options</button>
  </div>`;
  ui.pageRoot.innerHTML = `
    ${pageHeading({
      eyebrow: "Network intelligence",
      title: "Indonesia supply network",
      description: "Trace operational dependencies across ports, warehouses, factories, inbound shipments, and modeled response routes.",
      actions: modeControl,
    })}
    ${renderGlobalFilters()}
    ${kpiStrip([
      { label: "Factories", value: String(summary.facilities), detail: "production nodes" },
      { label: "Warehouses", value: String(summary.warehouses), detail: "transfer-capable nodes" },
      { label: "Ports", value: String(summary.ports), detail: "inbound gateways" },
      { label: "Disrupted routes", value: String(summary.disrupted_routes), detail: `${summary.active_routes} inbound routes`, tone: summary.disrupted_routes ? "tone-critical" : "tone-success" },
    ])}
    <div class="network-layout">
      <section class="panel network-map-panel">
        ${panelHeader("Operational network map", "Georeferenced facility view with modeled operational routes. Select any node for route context.", '<span class="section-caption">WGS84 reference coordinates</span>')}
        <div class="panel-body panel-body-map">${renderNetworkMap(state.network)}</div>
      </section>
      <aside class="panel network-detail-panel" aria-label="Selected network node">
        ${panelHeader("Node context", "Operational status and route relationships.")}
        <div class="panel-body" id="network-node-detail" data-network-node-detail>${renderNetworkNodeDetail(selectedNetworkNode())}</div>
      </aside>
      <section class="panel network-route-panel">
        ${panelHeader("Route register", "Accessible source of truth for every relationship displayed on the map.", `<span class="section-caption">${state.network.routes.filter((route) => state.networkMode === "ALL" || route.route_type === "INBOUND_SHIPMENT").length} routes</span>`)}
        <div id="route-register-results">${renderRouteTable(state.network)}</div>
      </section>
    </div>`;
}

function filteredPortfolio() {
  const query = state.portfolioQuery.trim().toLowerCase();
  return globallyFilteredPortfolio().filter((item) => {
    const severityMatch = state.portfolioSeverity === "ALL" || item.severity === state.portfolioSeverity;
    const haystack = [item.title, item.incident_id, item.facility_name, item.material_name, item.route].join(" ").toLowerCase();
    return severityMatch && (!query || haystack.includes(query));
  });
}

function portfolioToolbar() {
  return `<div class="portfolio-toolbar">
    <label class="search-field wide" for="portfolio-search">
      ${icon("search")}<span class="sr-only">Search incident portfolio</span>
      <input id="portfolio-search" type="search" value="${escapeHtml(state.portfolioQuery)}" placeholder="Search incident, facility, material, or route" autocomplete="off">
    </label>
    <div class="segmented-filter" aria-label="Filter incident severity">
      ${["ALL", "CRITICAL", "HIGH", "INFO"].map((severity) => `<button type="button" data-portfolio-severity="${severity}" class="${state.portfolioSeverity === severity ? "is-selected" : ""}" aria-pressed="${state.portfolioSeverity === severity}">${severity === "ALL" ? "All" : sentenceCase(severity)}</button>`).join("")}
    </div>
    <button class="button button-secondary" type="button" data-export-table="portfolio">${icon("download")}Export CSV</button>
  </div>`;
}

function renderIncidentPortfolioPage() {
  const items = filteredPortfolio();
  const active = state.portfolio.filter((item) => item.active);
  const exposure = active.reduce((sum, item) => sum + Number(item.baseline_exposure_idr), 0);
  ui.pageRoot.innerHTML = `
    ${pageHeading({
      eyebrow: "Incident operations",
      title: "Incident portfolio",
      description: "Prioritize disruptions across the network, open the evidence chain, and move grounded responses into human approval.",
      summary: `<span class="snapshot-time">${items.length} of ${state.portfolio.length} incidents</span>`,
    })}
    ${renderGlobalFilters()}
    ${kpiStrip([
      { label: "Active disruptions", value: String(active.length), detail: `${active.filter((item) => item.severity === "CRITICAL").length} critical`, tone: "tone-critical" },
      { label: "Portfolio exposure", value: formatCurrency(exposure, true), detail: "baseline downtime cost" },
      { label: "Analyzed", value: String(state.portfolio.filter((item) => item.analysis_available).length), detail: "persisted workspaces" },
      { label: "Approval packages", value: String(state.drafts.length), detail: `${state.drafts.filter((item) => item.status === "PENDING_APPROVAL").length} pending` },
    ])}
    <section class="panel portfolio-panel">
      ${panelHeader("Network incidents", "Joined incident, shipment, inventory, exposure, and approval state.")}
      ${portfolioToolbar()}
      <div id="portfolio-results">${renderPortfolioResults(items)}</div>
    </section>`;
}

function renderPortfolioResults(items) {
  if (!items.length) return emptyState("No matching incidents", "Adjust the search text or severity filter.");
  const sorted = sortRows(items, "portfolio", {
    incident: (item) => item.title,
    facility: (item) => item.facility_name,
    cover: (item) => Number(item.hours_of_cover ?? Number.POSITIVE_INFINITY),
    exposure: (item) => Number(item.baseline_exposure_idr),
    approval: (item) => item.approval_status,
    severity: (item) => ({ CRITICAL: 3, HIGH: 2, INFO: 1 }[item.severity] || 0),
  });
  const page = paginateRows(sorted, "portfolio");
  return `<div class="table-wrap portfolio-table-wrap">
    <table class="data-table portfolio-table">
      <thead><tr>${sortableHeader("Incident", "portfolio", "incident")}${sortableHeader("Facility / material", "portfolio", "facility")}${sortableHeader("Inventory cover", "portfolio", "cover")}${sortableHeader("Downtime exposure", "portfolio", "exposure")}${sortableHeader("Approval", "portfolio", "approval")}<th scope="col"><span class="sr-only">Open</span></th></tr></thead>
      <tbody>${page.rows.map((item) => `<tr>
        <td><div class="incident-cell">${severityBadge(item.severity)}<a href="/incidents/${encodeURIComponent(item.incident_id)}" data-link><strong>${escapeHtml(item.title)}</strong><small class="mono">${escapeHtml(item.incident_id)}</small></a></div></td>
        <td><strong>${escapeHtml(item.facility_name)}</strong><small>${escapeHtml(item.material_name)} · ${escapeHtml(item.route)}</small></td>
        <td><strong>${item.hours_of_cover == null ? "N/A" : `${formatNumber(item.hours_of_cover)}h`}</strong><small>${formatNumber(item.usable_quantity)} ${escapeHtml(state.inventory.find((record) => record.material_id === item.material_id)?.unit || "units")} usable</small></td>
        <td><strong>${formatNumber(item.baseline_downtime_hours)}h</strong><small>${formatCurrency(item.baseline_exposure_idr, true)}</small></td>
        <td>${stateBadge(item.approval_status)}</td>
        <td><a class="row-action" href="/incidents/${encodeURIComponent(item.incident_id)}" data-link aria-label="Open ${escapeHtml(item.title)}">${icon("arrow")}</a></td>
      </tr>`).join("")}</tbody>
    </table>
  </div>${tableFooter("portfolio", sorted.length, page.pages, "incidents")}`;
}

function findPortfolioItem(incidentId) {
  return state.portfolio.find((item) => item.incident_id === incidentId) || null;
}

function findRecommendedScenario(analysis) {
  return [analysis.baseline, ...analysis.scenarios].find((scenario) => scenario.scenario_id === analysis.recommended_scenario_id) || analysis.baseline;
}

function renderIncidentContext(item) {
  return `<section class="incident-context-card">
    <div class="context-header">
      <div>${severityBadge(item.severity)}<span class="mono">${escapeHtml(item.incident_id)}</span></div>
      <span>${escapeHtml(formatDateTime(item.detected_at))} WITA</span>
    </div>
    <div class="context-grid">
      <div><span>Facility</span><strong>${escapeHtml(item.facility_name)}</strong><small class="mono">${escapeHtml(item.facility_id)}</small></div>
      <div><span>Material</span><strong>${escapeHtml(item.material_name)}</strong><small class="mono">${escapeHtml(item.material_id)}</small></div>
      <div><span>Inbound route</span><strong>${escapeHtml(item.origin)} → ${escapeHtml(item.facility_name.replace(" Factory", ""))}</strong><small>${escapeHtml(item.shipment_id)} · +${item.delay_hours}h</small></div>
      <div><span>Current inventory</span><strong>${formatNumber(item.usable_quantity)} kg usable</strong><small>${item.hours_of_cover == null ? "No consumption rate" : `${formatNumber(item.hours_of_cover)} hours of cover`}</small></div>
    </div>
  </section>`;
}

function scenarioTable(analysis) {
  const scenarios = [analysis.baseline, ...analysis.scenarios];
  const config = state.tables.scenarios;
  const filtered = scenarios.filter((scenario) => config.filter === "ALL" || (config.filter === "FEASIBLE" ? scenario.feasible : !scenario.feasible));
  const sorted = sortRows(filtered, "scenarios", {
    scenario: (scenario) => scenario.name,
    response: (scenario) => Number(scenario.cost_breakdown.logistics_and_purchase_idr),
    downtime: (scenario) => Number(scenario.simulation.downtime_hours),
    total: (scenario) => Number(scenario.cost_breakdown.total_idr),
    feasibility: (scenario) => scenario.feasible ? 1 : 0,
  });
  const page = paginateRows(sorted, "scenarios");
  return `<div class="table-actions">
      <label class="select-field">Feasibility<select data-scenario-filter aria-label="Filter scenarios by feasibility"><option value="ALL">All scenarios</option><option value="FEASIBLE"${config.filter === "FEASIBLE" ? " selected" : ""}>Feasible</option><option value="FAILED"${config.filter === "FAILED" ? " selected" : ""}>Constraint failed</option></select></label>
      <button class="button button-secondary" type="button" data-export-table="scenarios">${icon("download")}Export CSV</button>
    </div><div class="table-wrap scenario-table-wrap">
    <table class="data-table scenario-table">
      <thead><tr>${sortableHeader("Scenario", "scenarios", "scenario")}${sortableHeader("Response cost", "scenarios", "response")}${sortableHeader("Downtime", "scenarios", "downtime")}${sortableHeader("Total modeled impact", "scenarios", "total")}${sortableHeader("Feasibility", "scenarios", "feasibility")}</tr></thead>
      <tbody>${page.rows.map((scenario) => {
        const recommended = scenario.scenario_id === analysis.recommended_scenario_id;
        return `<tr class="${recommended ? "is-recommended" : ""}">
          <td data-label="Scenario"><div class="scenario-name"><strong>${escapeHtml(scenario.name)}</strong><small>${escapeHtml(scenario.scenario_id)}</small>${recommended ? '<span class="recommended-label">Recommended</span>' : ""}</div></td>
          <td data-label="Response cost">${formatCurrency(scenario.cost_breakdown.logistics_and_purchase_idr, true)}</td>
          <td data-label="Downtime"><strong>${formatNumber(scenario.simulation.downtime_hours)}h</strong></td>
          <td data-label="Total impact">${formatCurrency(scenario.cost_breakdown.total_idr, true)}</td>
          <td data-label="Feasibility">${scenario.feasible ? stateBadge("FEASIBLE") : stateBadge("CONSTRAINT_FAILED")}</td>
        </tr>`;
      }).join("")}</tbody>
    </table>
  </div>${tableFooter("scenarios", sorted.length, page.pages, "scenarios")}`;
}

function renderEvidencePanel(analysis, recommended) {
  const constraints = recommended.constraints_passed || [];
  const risks = [...(recommended.risks || []), ...(recommended.rejected_reasons || [])];
  return `<div class="evidence-grid">
    <div><h3>Constraints passed</h3><ul class="evidence-list pass">${constraints.slice(0, 6).map((item) => `<li>${icon("check")}<span>${escapeHtml(item)}</span></li>`).join("")}</ul></div>
    <div><h3>Residual risks</h3>${risks.length ? `<ul class="evidence-list risk">${risks.slice(0, 6).map((item) => `<li>${icon("alert")}<span>${escapeHtml(item)}</span></li>`).join("")}</ul>` : '<p class="muted-copy">No residual risks are recorded for the recommended scenario.</p>'}</div>
  </div>`;
}

function renderResponseGovernance(item, analysis, recommended, incidentDrafts) {
  if (!recommended.allocations.length) {
    return `<div class="governance-card no-action"><div>${icon("alert")}<div><strong>No transaction package available</strong><p>The selected response has no draftable allocation. Review damage-limitation scenarios or upstream capacity.</p></div></div></div>`;
  }
  const current = incidentDrafts.find((draft) => draft.scenario_id === recommended.scenario_id) || incidentDrafts[0];
  const action = !current
    ? `<button class="button button-primary" type="button" data-create-draft>${icon("package")}Create response package</button>`
    : current.status === "PENDING_APPROVAL"
      ? `<button class="button button-primary" type="button" data-review-draft="${escapeHtml(current.draft_id)}">${icon("shield")}Review decision</button>`
      : `<a class="button button-secondary" href="/approvals" data-link>Open approval record</a>`;
  return `<div class="governance-card">
    <div class="governance-copy">
      <span class="governance-icon">${icon("shield")}</span>
      <div><span class="eyebrow">Controlled execution</span><h3>${current ? `Response package ${escapeHtml(current.draft_id)}` : "Response package not yet created"}</h3>
      <p>${current ? `Current status: ${sentenceCase(current.status)}. External ERP posting remains disabled.` : "Create a reviewable package from the grounded recommendation. A different authorized operator must make the decision."}</p></div>
    </div>
    <div class="governance-action">${current ? stateBadge(current.status) : stateBadge("NOT_CREATED")}${action}</div>
  </div>`;
}

function renderIncidentAudit(records) {
  if (!records.length) return '<p class="muted-copy">No audit records are associated with this incident.</p>';
  return `<div class="audit-timeline">${[...records].reverse().map((record) => `<div class="audit-row">
    <span class="audit-marker" aria-hidden="true"></span>
    <time class="audit-time" datetime="${escapeHtml(record.timestamp)}">${escapeHtml(formatDateTime(record.timestamp))}</time>
    <div class="audit-copy"><strong>${escapeHtml(sentenceCase(record.action))}</strong><span>${escapeHtml(record.summary)}</span></div>
    <span class="audit-actor">${escapeHtml(record.actor)}</span>
  </div>`).join("")}</div>`;
}

function renderNoAnalysis(item) {
  const sapConfigured = Boolean(state.status?.sap_ai?.configured);
  const liveAiEnabled = Boolean(state.status?.sap_ai?.live_requests_enabled);
  const liveAiAvailable = sapConfigured && liveAiEnabled;
  return `<section class="analysis-empty">
    <div class="analysis-empty-visual" aria-hidden="true">
      <span></span><span></span><span></span><span></span>
    </div>
    <div><p class="eyebrow">Decision model</p><h2>Build the response model</h2><p>Run the deterministic engine to project hourly inventory, quantify stockout exposure, compare bounded mitigation options, and generate a traceable recommendation.</p>
      <ul><li>Hourly baseline and response inventory</li><li>Cost versus downtime scenario frontier</li><li>Mitigation allocations and approval policy</li></ul>
      <label class="analysis-mode-option ${liveAiAvailable ? "" : "is-disabled"}">
        <input id="live-ai-toggle" type="checkbox" ${liveAiAvailable ? "checked" : "disabled"}>
        <span><strong>Ground the explanation with SAP AI Core</strong><small>${liveAiAvailable ? "The deterministic engine remains the source of every numerical result." : sapConfigured ? "SAP AI Core is live-verified, but public inference is disabled by runtime policy." : "SAP AI Core is not configured; deterministic fallback will be used."}</small></span>
      </label>
      <button class="button button-primary" type="button" data-run-analysis>${icon("analyze")}Run risk analysis</button>
    </div>
  </section>`;
}

function renderWorkspaceSectionNav(item, standalone) {
  if (standalone) return "";
  const links = [["summary", "Summary"], ["inventory", "Inventory"], ["scenarios", "Scenarios"], ["governance", "Governance"], ["audit", "Audit"]];
  return `<nav class="section-nav workspace-tabs" aria-label="Incident workspace sections">${links.map(([view, label]) => `<a href="/incidents/${encodeURIComponent(item.incident_id)}?view=${view}" data-incident-view="${view}" class="${state.incidentView === view ? "is-active" : ""}"${state.incidentView === view ? ' aria-current="page"' : ""}>${label}</a>`).join("")}</nav>`;
}

function renderAnalysisSections(item, analysis, incidentDrafts, incidentAudit, standalone = false) {
  const recommended = findRecommendedScenario(analysis);
  const avoided = Math.max(0, analysis.baseline.simulation.downtime_hours - recommended.simulation.downtime_hours);
  const scenarioLink = standalone ? "" : `<a class="button button-secondary" href="/scenarios/${encodeURIComponent(analysis.analysis_id)}" data-link>Open scenario view</a>`;
  const summaryView = `<section class="recommendation-banner" id="incident-summary">
      <div class="recommendation-mark">${icon(recommended.feasible ? "check" : "alert")}</div>
      <div><span class="eyebrow">${recommended.feasible ? "Recommended response" : "Damage limitation response"} · ${analysis.mode === "live_ai" ? "Live SAP AI Core" : analysis.mode === "fallback" ? "AI fallback" : "Deterministic"}</span><h2>${escapeHtml(recommended.name)}</h2><p>${escapeHtml(analysis.recommendation_rationale)}</p></div>
      <div class="recommendation-cost"><span>Total modeled impact</span><strong>${formatCurrency(recommended.cost_breakdown.total_idr, true)}</strong><small>${formatCurrency(recommended.cost_breakdown.logistics_and_purchase_idr, true)} response cost</small></div>
    </section>
    ${kpiStrip([
      { label: "Baseline downtime", value: `${formatNumber(analysis.baseline.simulation.downtime_hours)}h`, detail: formatCurrency(analysis.baseline.cost_breakdown.estimated_downtime_idr, true), tone: analysis.baseline.simulation.downtime_hours ? "tone-critical" : "tone-success" },
      { label: "Recommended downtime", value: `${formatNumber(recommended.simulation.downtime_hours)}h`, detail: `${formatNumber(avoided)}h avoided`, tone: recommended.simulation.downtime_hours ? "tone-warning" : "tone-success" },
      { label: "Stockout", value: analysis.stockout_at ? formatDateTime(analysis.stockout_at) : "Prevented", detail: `${formatNumber(analysis.hours_of_cover)}h starting cover` },
      { label: "Decision state", value: incidentDrafts[0] ? sentenceCase(incidentDrafts[0].status) : "Not packaged", detail: analysis.requires_approval ? "manager approval required" : "standard review" },
    ])}
    <section class="panel content-panel" id="impact-chain">${panelHeader("Incident-to-production impact chain", "Trace the operational cause, affected flow, production exposure, and selected response.")}<div class="panel-body">${renderImpactChain(item, analysis, recommended)}</div></section>`;
  const inventoryView = `<div class="analysis-grid"><section class="panel span-12" id="inventory-projection">${panelHeader("Hourly inventory projection", "Baseline versus recommended response, including safety-stock threshold and stockout window.", '<span class="section-caption">Interactive hourly model</span>')}<div class="panel-body">${renderInventoryProjection(analysis, recommended)}</div></section><section class="panel span-12" id="allocation-composition">${panelHeader("Mitigation allocation", "Quantity, source, arrival timing, and modeled reliability.")}<div class="panel-body">${renderAllocationComposition(recommended)}</div></section></div>`;
  const scenariosView = `<div class="analysis-grid"><section class="panel span-12" id="scenario-frontier">${panelHeader("Cost versus downtime frontier", "Select a scenario point to inspect cost, downtime, allocation, and evidence.", scenarioLink)}<div class="panel-body">${renderScenarioFrontier(analysis)}</div></section><section class="panel span-12" id="decision-evidence">${panelHeader("Recommended decision evidence", "Constraints and residual risks for the recommended response.")}<div class="panel-body">${renderEvidencePanel(analysis, recommended)}</div></section><section class="panel span-12" id="scenario-comparison">${panelHeader("Scenario comparison", "Sortable, filterable values behind the frontier visualization.", `<span class="section-caption">${analysis.scenarios.length + 1} evaluated scenarios</span>`)}<div id="scenario-table-results">${scenarioTable(analysis)}</div></section></div>`;
  const governanceView = `<div class="analysis-grid"><section class="panel span-12" id="response-governance">${panelHeader("Response governance", "Create a local review package, then require an explicit human decision.")}<div class="panel-body">${renderResponseGovernance(item, analysis, recommended, incidentDrafts)}</div></section></div>`;
  const auditView = `<div class="analysis-grid"><section class="panel span-12" id="incident-audit">${panelHeader("Incident audit trail", "System and human actions recorded for this workspace.", `<a class="text-link" href="/audit" data-link>Open audit explorer ${icon("arrow")}</a>`)}<div class="panel-body">${renderIncidentAudit(incidentAudit)}</div></section></div>`;
  const views = { summary: summaryView, inventory: inventoryView, scenarios: scenariosView, governance: governanceView, audit: auditView };
  const activeView = standalone ? "scenarios" : state.incidentView;
  return `${renderWorkspaceSectionNav(item, standalone)}<div class="workspace-view" data-workspace-view="${activeView}">${views[activeView] || summaryView}</div>`;
}

async function renderIncidentWorkspace(incidentId) {
  const item = findPortfolioItem(incidentId);
  if (!item) throw new Error(`Incident not found: ${incidentId}`);
  setBusy(true, "Loading incident");
  const [analysisPayload, draftPayload, auditPayload] = await Promise.all([
    api(`/api/v1/analyses/latest?incident_id=${encodeURIComponent(incidentId)}`),
    api(`/api/v1/transaction-drafts?incident_id=${encodeURIComponent(incidentId)}`),
    api(`/api/v1/audit?incident_id=${encodeURIComponent(incidentId)}`),
  ]);
  state.analysis = analysisPayload.analysis;
  const requestedView = new URLSearchParams(window.location.search).get("view");
  if (["summary", "inventory", "scenarios", "governance", "audit"].includes(requestedView)) state.incidentView = requestedView;
  saveUiPreferences();
  const incidentDrafts = draftPayload.drafts;
  const incidentAudit = auditPayload.records;
  ui.pageRoot.innerHTML = `
    ${pageHeading({
      eyebrow: "Incident workspace",
      title: item.title,
      description: item.description,
      backHref: "/incidents",
      backLabel: "Back to incident portfolio",
      actions: state.analysis ? `<button class="button button-secondary" type="button" data-run-analysis>${icon("refresh")}Refresh analysis</button>` : "",
    })}
    ${renderIncidentContext(item)}
    <div class="workspace-analysis">
      ${state.analysis ? renderAnalysisSections(item, state.analysis, incidentDrafts, incidentAudit) : renderNoAnalysis(item)}
    </div>`;
  setBusy(false);
  ui.syncState.querySelector("span:last-child").textContent = "Operational";
}

async function renderScenarioPage(analysisId) {
  setBusy(true, "Loading scenario");
  const payload = await api(`/api/v1/analyses/${encodeURIComponent(analysisId)}`);
  const analysis = payload.analysis;
  const item = findPortfolioItem(analysis.incident_id);
  if (!item) throw new Error(`Incident context not found for analysis ${analysisId}`);
  const drafts = state.drafts.filter((draft) => draft.incident_id === analysis.incident_id);
  state.analysis = analysis;
  updateChrome(parseRoute());
  ui.pageRoot.innerHTML = `
    ${pageHeading({
      eyebrow: "Scenario intelligence",
      title: "Response scenario analysis",
      description: `${item.title} · ${analysis.facility.name} · ${analysis.affected_material.name}`,
      backHref: `/incidents/${encodeURIComponent(item.incident_id)}`,
      backLabel: "Back to incident workspace",
    })}
    ${renderAnalysisSections(item, analysis, drafts, [], true)}`;
  setBusy(false);
  ui.syncState.querySelector("span:last-child").textContent = "Operational";
}

function filteredDrafts() {
  return state.drafts.filter((draft) => state.approvalStatus === "ALL" || draft.status === state.approvalStatus);
}

function renderApprovalResults() {
  const drafts = filteredDrafts();
  if (!drafts.length) {
    return emptyState(
      state.drafts.length ? "No packages in this state" : "Approval inbox is clear",
      state.drafts.length ? "Choose another status filter." : "Create a grounded response package from an incident workspace. It will appear here for an independent human decision.",
      state.drafts.length ? "" : '<a class="button button-primary" href="/incidents" data-link>Open incident portfolio</a>',
    );
  }
  return `<div class="approval-list">${drafts.map((draft) => {
    const incident = findPortfolioItem(draft.incident_id);
    const pending = draft.status === "PENDING_APPROVAL";
    return `<article class="approval-package">
      <div class="approval-package-main">
        <div class="approval-package-heading"><div>${stateBadge(draft.status)}<span class="mono">${escapeHtml(draft.draft_id)}</span></div><time datetime="${escapeHtml(draft.created_at)}">${escapeHtml(formatDateTime(draft.created_at))}</time></div>
        <h2>${escapeHtml(incident?.title || draft.incident_id)}</h2>
        <p>${escapeHtml(draft.draft_type.replaceAll("_", " "))} · ${escapeHtml(incident?.facility_name || draft.destination_facility_id)} · requested by ${escapeHtml(draft.requested_by)}</p>
        <div class="package-allocations">${draft.allocations.map((allocation) => `<span><strong>${formatNumber(allocation.quantity)} ${escapeHtml(allocation.unit)}</strong> from ${escapeHtml(allocation.source_name)}</span>`).join("")}</div>
      </div>
      <div class="approval-package-side">
        <span>Estimated response cost</span><strong>${formatCurrency(draft.estimated_cost_idr, true)}</strong><small>Version ${draft.version} · simulated only</small>
        ${pending ? `<button class="button button-primary" type="button" data-review-draft="${escapeHtml(draft.draft_id)}">${icon("shield")}Review decision</button>` : `<a class="button button-secondary" href="/incidents/${encodeURIComponent(draft.incident_id)}" data-link>Open incident</a>`}
      </div>
    </article>`;
  }).join("")}</div>`;
}

function renderApprovalsPage() {
  const pending = state.drafts.filter((draft) => draft.status === "PENDING_APPROVAL").length;
  const approved = state.drafts.filter((draft) => draft.status === "APPROVED").length;
  const rejected = state.drafts.filter((draft) => draft.status === "REJECTED").length;
  ui.pageRoot.innerHTML = `
    ${pageHeading({
      eyebrow: "Human governance",
      title: "Approval inbox",
      description: "Review grounded response packages, preserve separation of duties, and record explicit authorization without executing an external ERP transaction.",
      summary: `<span class="snapshot-time">${pending} pending decisions</span>`,
    })}
    ${kpiStrip([
      { label: "Pending", value: String(pending), detail: pending ? "decision required" : "inbox clear", tone: pending ? "tone-warning" : "tone-success" },
      { label: "Approved", value: String(approved), detail: "local authorization records" },
      { label: "Rejected", value: String(rejected), detail: "closed without execution" },
      { label: "ERP execution", value: "Disabled", detail: "simulation boundary enforced", tone: "tone-success" },
    ])}
    <section class="panel">
      ${panelHeader("Response packages", "Packages are created from persisted analyses and retain their source allocations.")}
      <div class="approval-filter segmented-filter" aria-label="Filter approval status">
        ${["ALL", "PENDING_APPROVAL", "APPROVED", "REJECTED"].map((status) => `<button type="button" data-approval-status="${status}" class="${state.approvalStatus === status ? "is-selected" : ""}" aria-pressed="${state.approvalStatus === status}">${status === "ALL" ? "All packages" : sentenceCase(status)}</button>`).join("")}
      </div>
      <div id="approval-results" class="panel-body">${renderApprovalResults()}</div>
    </section>`;
}

function filteredAudit() {
  const query = state.auditQuery.trim().toLowerCase();
  if (!query) return state.audit;
  return state.audit.filter((record) => [record.action, record.actor, record.entity_id, record.incident_id, record.summary].join(" ").toLowerCase().includes(query));
}

function renderAuditResults() {
  const records = filteredAudit();
  if (!records.length) return emptyState("No matching audit records", "Adjust the search text to include an action, actor, entity, or incident.");
  const sorted = sortRows(records, "audit", {
    timestamp: (record) => new Date(record.timestamp).getTime(),
    action: (record) => record.action,
    actor: (record) => record.actor,
    entity: (record) => record.entity_id,
    incident: (record) => record.incident_id || "",
    summary: (record) => record.summary,
  });
  const page = paginateRows(sorted, "audit");
  return `<div class="table-wrap">
    <table class="data-table audit-table">
      <thead><tr>${sortableHeader("Timestamp", "audit", "timestamp")}${sortableHeader("Action", "audit", "action")}${sortableHeader("Actor", "audit", "actor")}${sortableHeader("Entity", "audit", "entity")}${sortableHeader("Incident", "audit", "incident")}${sortableHeader("Summary", "audit", "summary")}</tr></thead>
      <tbody>${page.rows.map((record) => `<tr>
        <td><time datetime="${escapeHtml(record.timestamp)}">${escapeHtml(formatDateTime(record.timestamp))}</time></td>
        <td>${stateBadge(record.action)}</td>
        <td>${escapeHtml(record.actor)}</td>
        <td><strong>${escapeHtml(record.entity_type)}</strong><small class="mono">${escapeHtml(record.entity_id)}</small></td>
        <td>${record.incident_id ? `<a class="text-link mono" href="/incidents/${encodeURIComponent(record.incident_id)}" data-link>${escapeHtml(record.incident_id)}</a>` : "—"}</td>
        <td>${escapeHtml(record.summary)}</td>
      </tr>`).join("")}</tbody>
    </table>
  </div>${tableFooter("audit", sorted.length, page.pages, "records")}`;
}

function renderAuditPage() {
  const actions = new Set(state.audit.map((record) => record.action)).size;
  const actors = new Set(state.audit.map((record) => record.actor)).size;
  ui.pageRoot.innerHTML = `
    ${pageHeading({
      eyebrow: "Decision traceability",
      title: "Audit explorer",
      description: "Inspect the complete local trail from reference-state reset through analysis, package creation, submission, and human decision.",
      summary: `<span class="snapshot-time">${state.audit.length} immutable local records</span>`,
    })}
    ${kpiStrip([
      { label: "Audit records", value: String(state.audit.length), detail: "current local state" },
      { label: "Action types", value: String(actions), detail: "system and human events" },
      { label: "Actors", value: String(actors), detail: "identified principals" },
      { label: "Trace boundary", value: "Local", detail: "no external execution", tone: "tone-success" },
    ])}
    <section class="panel">
      ${panelHeader("Recorded events", "Search by action, actor, entity, incident ID, or event summary.")}
      <div class="audit-toolbar"><label class="search-field wide" for="audit-search">${icon("search")}<span class="sr-only">Search audit records</span><input id="audit-search" type="search" value="${escapeHtml(state.auditQuery)}" placeholder="Search audit trail" autocomplete="off"></label><button class="button button-secondary" type="button" data-export-table="audit">${icon("download")}Export CSV</button></div>
      <div id="audit-results">${renderAuditResults()}</div>
    </section>`;
}

function integrationStatusDescription(component) {
  if (component.status === "OPERATIONAL") return "Live local";
  if (component.status === "READY") return "Configured";
  if (component.status === "EMULATED") return "Contract verified";
  if (component.status === "DISABLED") return "Safety boundary";
  return "Fallback active";
}

function renderIntegrationsPage() {
  const operational = state.integrations.filter((component) => ["OPERATIONAL", "READY"].includes(component.status)).length;
  const guarded = state.integrations.filter((component) => ["EMULATED", "DISABLED", "NOT_CONFIGURED"].includes(component.status)).length;
  ui.pageRoot.innerHTML = `
    ${pageHeading({
      eyebrow: "Platform operations",
      title: "Integration health",
      description: "Understand which components are operational, configured, locally emulated, or intentionally disabled before relying on a response.",
      summary: `<span class="snapshot-time">Checked · ${escapeHtml(formatDateTime(state.status?.demo_now || state.overview.generated_at))} WITA</span>`,
    })}
    ${kpiStrip([
      { label: "Operational / ready", value: String(operational), detail: "available capabilities", tone: "tone-success" },
      { label: "Guarded boundaries", value: String(guarded), detail: "emulated, fallback, or disabled" },
      { label: "State persistence", value: state.status.state_store.persistent ? "Enabled" : "Session only", detail: state.status.state_store.engine },
      { label: "External writeback", value: state.status.real_transactions_enabled ? "Enabled" : "Disabled", detail: "approval remains local", tone: state.status.real_transactions_enabled ? "tone-warning" : "tone-success" },
    ])}
    <section class="integration-flow panel">
      ${panelHeader("Decision architecture", "Operational data moves through controlled boundaries before a human authorization record is created.")}
      <div class="panel-body">
        <ol class="system-flow">
          <li><span>${icon("route")}</span><div><small>Signals</small><strong>AWS event contract</strong><p>Local event adapter validates disruption payloads.</p></div></li>
          <li class="flow-connector" aria-hidden="true">${icon("arrow")}</li>
          <li><span>${icon("database")}</span><div><small>Decision core</small><strong>NSRA deterministic engine</strong><p>Projects inventory and ranks bounded scenarios.</p></div></li>
          <li class="flow-connector" aria-hidden="true">${icon("arrow")}</li>
          <li><span>${icon("shield")}</span><div><small>Control</small><strong>Human approval</strong><p>Records an explicit local approve or reject decision.</p></div></li>
          <li class="flow-connector guarded" aria-hidden="true">${icon("arrow")}</li>
          <li class="is-guarded"><span>${icon("alert")}</span><div><small>Execution boundary</small><strong>SAP ERP writeback</strong><p>Intentionally blocked in this environment.</p></div></li>
        </ol>
      </div>
    </section>
    <div class="integration-grid">
      ${state.integrations.map((component) => `<article class="panel integration-card">
        <div class="integration-card-header"><span class="integration-icon">${icon(component.component_id === "state-store" ? "database" : component.component_id === "decision-engine" ? "analyze" : component.component_id === "sap-erp" ? "shield" : "route")}</span>${stateBadge(component.status)}</div>
        <span class="eyebrow">${escapeHtml(component.category)}</span><h2>${escapeHtml(component.name)}</h2><p>${escapeHtml(component.detail)}</p>
        <div class="integration-meta"><span>Connection mode</span><strong>${escapeHtml(integrationStatusDescription(component))}</strong></div>
      </article>`).join("")}
    </div>`;
}

async function loadBaseData({ force = false } = {}) {
  if (state.loaded && !force) return;
  setBusy(true, "Synchronizing");
  clearError();
  const [statusPayload, overviewPayload, networkPayload, portfolioPayload, inventoryPayload, shipmentPayload, draftPayload, auditPayload, integrationPayload, basemapPayload] = await Promise.all([
    api("/api/v1/status"),
    api("/api/v1/overview"),
    api("/api/v1/network"),
    api("/api/v1/portfolio"),
    api("/api/v1/inventory"),
    api("/api/v1/shipments"),
    api("/api/v1/transaction-drafts"),
    api("/api/v1/audit"),
    api("/api/v1/integrations/health"),
    api("/assets/indonesia-50m.json"),
  ]);
  state.status = statusPayload;
  state.overview = overviewPayload.overview;
  state.network = networkPayload.network;
  state.portfolio = portfolioPayload.items;
  state.inventory = inventoryPayload.items;
  state.shipments = shipmentPayload.shipments;
  state.drafts = draftPayload.drafts;
  state.audit = auditPayload.records;
  state.integrations = integrationPayload.components;
  state.basemap = basemapPayload;
  state.loaded = true;
  ui.approvalCount.textContent = state.drafts.filter((draft) => draft.status === "PENDING_APPROVAL").length;
  ui.approvalCount.hidden = Number(ui.approvalCount.textContent) === 0;
  ui.incidentCount.textContent = state.portfolio.filter((item) => item.active).length;
  ui.incidentCount.hidden = false;
  ui.syncState.querySelector("span:last-child").textContent = "Operational";
  setBusy(false);
}

function loadingPage() {
  ui.pageRoot.innerHTML = `<section class="page-loading" aria-label="Loading operations workspace"><div class="skeleton-line skeleton-title"></div><div class="skeleton-line skeleton-copy"></div><div class="loading-grid" aria-hidden="true"><span></span><span></span><span></span><span></span></div></section>`;
}

async function renderRoute({ focus = false } = {}) {
  const route = parseRoute();
  updateChrome(route);
  if (!state.loaded) loadingPage();
  try {
    await loadBaseData();
    updateChrome(route);
    clearError();
    if (route.name === "overview") renderOverviewPage();
    else if (route.name === "network") renderNetworkPage();
    else if (route.name === "incidents") renderIncidentPortfolioPage();
    else if (route.name === "incident") await renderIncidentWorkspace(route.id);
    else if (route.name === "scenario") await renderScenarioPage(route.id);
    else if (route.name === "approvals") renderApprovalsPage();
    else if (route.name === "audit") renderAuditPage();
    else if (route.name === "integrations") renderIntegrationsPage();
    ui.pageRoot.setAttribute("aria-busy", "false");
    const title = document.querySelector("#page-title");
    document.title = `${title?.textContent || "Operations"} · NSRA`;
    ui.routeAnnouncer.textContent = `${title?.textContent || "Workspace"} loaded`;
    if (focus && title) title.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "auto" });
    syncSectionNavigation();
    if (window.location.hash) {
      const section = document.querySelector(window.location.hash);
      if (section) window.requestAnimationFrame(() => {
        section.scrollIntoView({ behavior: "auto", block: "start" });
        syncSectionNavigation();
      });
    }
  } catch (error) {
    setBusy(false);
    showError(error);
    ui.pageRoot.innerHTML = emptyState("Workspace unavailable", "The requested operational view could not be loaded. Use Retry after checking the local API.");
  }
}

async function runAnalysis(button) {
  const route = parseRoute();
  const incidentId = route.name === "incident" ? route.id : state.analysis?.incident_id;
  if (!incidentId) return;
  const original = button.innerHTML;
  button.disabled = true;
  button.innerHTML = `${icon("refresh")}Running model…`;
  try {
    const useLiveAi = Boolean(document.querySelector("#live-ai-toggle")?.checked);
    const payload = await api("/api/v1/analysis/disruption", {
      method: "POST",
      body: JSON.stringify({ incident_id: incidentId, target_downtime_hours: 0, use_live_ai: useLiveAi }),
    });
    state.analysis = payload.analysis;
    state.loaded = false;
    showToast("Risk analysis completed and saved to the incident workspace.");
    await renderRoute();
  } catch (error) {
    showToast(error.message, true);
    button.disabled = false;
    button.innerHTML = original;
  }
}

async function createDraft(button) {
  const route = parseRoute();
  const incidentId = route.name === "incident" ? route.id : state.analysis?.incident_id;
  if (!incidentId || !state.analysis) return;
  const recommended = findRecommendedScenario(state.analysis);
  button.disabled = true;
  button.innerHTML = `${icon("refresh")}Creating package…`;
  try {
    await api("/api/v1/transaction-drafts", {
      method: "POST",
      body: JSON.stringify({
        incident_id: incidentId,
        analysis_id: state.analysis.analysis_id,
        scenario_id: recommended.scenario_id,
        requested_by: "operations.planner",
        idempotency_key: `web-${state.analysis.analysis_id}-${recommended.scenario_id}`,
      }),
    });
    state.loaded = false;
    showToast("Response package created and submitted for approval.");
    await renderRoute();
  } catch (error) {
    showToast(error.message, true);
    button.disabled = false;
    button.innerHTML = `${icon("package")}Create response package`;
  }
}

function openDecision(draftId) {
  const draft = state.drafts.find((item) => item.draft_id === draftId);
  if (!draft) {
    showToast("The selected approval package is no longer available.", true);
    return;
  }
  state.selectedDraft = draft;
  const incident = findPortfolioItem(draft.incident_id);
  ui.decisionSummary.innerHTML = `<div class="decision-package">
    <div><span>Package</span><strong class="mono">${escapeHtml(draft.draft_id)}</strong></div>
    <div><span>Incident</span><strong>${escapeHtml(incident?.title || draft.incident_id)}</strong></div>
    <div><span>Response cost</span><strong>${formatCurrency(draft.estimated_cost_idr)}</strong></div>
    <div><span>Requested by</span><strong>${escapeHtml(draft.requested_by)}</strong></div>
  </div>`;
  ui.decisionError.hidden = true;
  ui.decisionJustification.value = "";
  ui.simulationAcknowledgement.checked = false;
  ui.decisionDialog.showModal();
  ui.decisionActor.focus();
}

async function submitDecision(action, button) {
  const draft = state.selectedDraft;
  if (!draft) return;
  const actor = ui.decisionActor.value.trim();
  const justification = ui.decisionJustification.value.trim();
  let message = "";
  if (!actor) message = "Enter the approver identity.";
  else if (actor.toLowerCase() === draft.requested_by.toLowerCase()) message = "The approver must be different from the requesting planner.";
  else if (justification.length < 10) message = "Provide a decision rationale of at least 10 characters.";
  else if (!ui.simulationAcknowledgement.checked) message = "Acknowledge the simulated execution boundary before deciding.";
  if (message) {
    ui.decisionError.textContent = message;
    ui.decisionError.hidden = false;
    ui.decisionError.focus();
    return;
  }
  ui.decisionError.hidden = true;
  const original = button.textContent;
  button.disabled = true;
  button.textContent = action === "APPROVE" ? "Approving…" : "Rejecting…";
  try {
    await api(`/api/v1/transaction-drafts/${encodeURIComponent(draft.draft_id)}/decision`, {
      method: "POST",
      body: JSON.stringify({ action, actor, justification, expected_version: draft.version }),
    });
    ui.decisionDialog.close();
    state.selectedDraft = null;
    state.loaded = false;
    showToast(`Response package ${action === "APPROVE" ? "approved" : "rejected"} and recorded in the audit trail.`);
    await renderRoute();
  } catch (error) {
    ui.decisionError.textContent = error.message;
    ui.decisionError.hidden = false;
    ui.decisionError.focus();
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

function renderEnvironment() {
  if (!state.status) return;
  const sapState = state.status.sap_ai.live_call_performed
    ? state.status.sap_ai.live_requests_enabled ? "Live verified · on-demand enabled" : "Live verified · public requests disabled"
    : state.status.sap_ai.configured ? "Configured · not called" : "Fallback active";
  ui.environmentList.innerHTML = `
    <div><dt>Application version</dt><dd>${escapeHtml(state.status.version)}</dd></div>
    <div><dt>Data classification</dt><dd>Reference fixture</dd></div>
    <div><dt>State store</dt><dd>${escapeHtml(state.status.state_store.engine)} · ${state.status.state_store.persistent ? "persistent" : "session only"}</dd></div>
    <div><dt>Decision engine</dt><dd>Deterministic local model</dd></div>
    <div><dt>SAP AI Core</dt><dd>${escapeHtml(sapState)}</dd></div>
    <div><dt>AWS events</dt><dd>${escapeHtml(state.status.aws.event_flow)}</dd></div>
    <div><dt>ERP writeback</dt><dd>${state.status.real_transactions_enabled ? "Enabled" : "Disabled"}</dd></div>`;
}

async function resetWorkspace() {
  ui.confirmResetButton.disabled = true;
  ui.confirmResetButton.textContent = "Resetting…";
  try {
    await api("/api/v1/demo/reset", { method: "POST", body: "{}" });
    ui.environmentDialog.close();
    ui.resetConfirmation.hidden = true;
    state.loaded = false;
    state.analysis = null;
    state.selectedDraft = null;
    showToast("Workspace state reset to the reviewed reference records.");
    navigate("/overview", { replace: true });
  } catch (error) {
    showToast(error.message, true);
  } finally {
    ui.confirmResetButton.disabled = false;
    ui.confirmResetButton.textContent = "Confirm reset";
  }
}

function openMobileNav() {
  ui.sidebar.classList.add("is-open");
  ui.sidebarScrim.hidden = false;
  ui.mobileMenu.setAttribute("aria-expanded", "true");
  ui.mobileNavClose.focus();
}

function closeMobileNav() {
  if (!ui.sidebar.classList.contains("is-open")) return;
  ui.sidebar.classList.remove("is-open");
  ui.sidebarScrim.hidden = true;
  ui.mobileMenu.setAttribute("aria-expanded", "false");
}

function selectNetworkNode(nodeId) {
  state.selectedNodeId = nodeId;
  document.querySelectorAll("[data-network-node]").forEach((node) => node.classList.toggle("is-selected", node.dataset.networkNode === nodeId));
  document.querySelectorAll("[data-network-node-detail]").forEach((detail) => { detail.innerHTML = renderNetworkNodeDetail(selectedNetworkNode()); });
}

function applyNetworkView() {
  document.querySelectorAll("[data-network-map]").forEach((map) => {
    const viewport = map.querySelector("[data-network-viewport]");
    if (!viewport) return;
    const viewBox = map.getAttribute("viewBox").split(/\s+/).map(Number);
    viewport.setAttribute("transform", networkTransform(viewBox[2], viewBox[3]));
  });
  document.querySelectorAll("[data-map-zoom-output]").forEach((output) => { output.textContent = `${Math.round(state.networkZoom * 100)}%`; });
}

function openNetworkMapDialog() {
  ui.networkMapDialogBody.innerHTML = `<div class="fullscreen-map-layout"><div>${renderNetworkMap(state.network, false, true)}</div><aside class="panel fullscreen-node-detail" data-network-node-detail>${renderNetworkNodeDetail(selectedNetworkNode())}</aside></div>`;
  ui.networkMapDialog.showModal();
  ui.networkMapDialog.querySelector("[data-network-map]")?.focus();
}

function setNetworkZoom(delta) {
  state.networkZoom = Math.max(1, Math.min(2.5, state.networkZoom + delta));
  if (state.networkZoom === 1) {
    state.networkPanX = 0;
    state.networkPanY = 0;
  }
  applyNetworkView();
}

function panNetworkMap(deltaX, deltaY) {
  if (state.networkZoom <= 1) return;
  const maxX = 460 * (state.networkZoom - 1);
  const maxY = 210 * (state.networkZoom - 1);
  state.networkPanX = Math.max(-maxX, Math.min(maxX, state.networkPanX + deltaX));
  state.networkPanY = Math.max(-maxY, Math.min(maxY, state.networkPanY + deltaY));
  applyNetworkView();
}

function resetNetworkView() {
  state.networkZoom = 1;
  state.networkPanX = 0;
  state.networkPanY = 0;
  applyNetworkView();
}

function syncSectionNavigation() {
  const links = [...document.querySelectorAll("[data-section-link]")];
  if (!links.length) return;
  let active = links[0];
  links.forEach((link) => {
    const target = document.querySelector(link.getAttribute("href"));
    if (target && target.getBoundingClientRect().top <= 150) active = link;
  });
  links.forEach((link) => {
    if (link === active) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  });
}

function refreshTable(tableName) {
  if (tableName === "portfolio") {
    const target = document.querySelector("#portfolio-results");
    if (target) target.innerHTML = renderPortfolioResults(filteredPortfolio());
  } else if (tableName === "routes") {
    const target = document.querySelector("#route-register-results");
    if (target) target.innerHTML = renderRouteTable(state.network);
  } else if (tableName === "scenarios") {
    const target = document.querySelector("#scenario-table-results");
    if (target && state.analysis) target.innerHTML = scenarioTable(state.analysis);
  } else if (tableName === "audit") {
    const target = document.querySelector("#audit-results");
    if (target) target.innerHTML = renderAuditResults();
  }
}

function exportTable(tableName) {
  if (tableName === "portfolio") {
    downloadCsv("nsra-incidents.csv", [
      { label: "Incident ID", value: (row) => row.incident_id }, { label: "Title", value: (row) => row.title }, { label: "Severity", value: (row) => row.severity }, { label: "Facility", value: (row) => row.facility_name }, { label: "Material", value: (row) => row.material_name }, { label: "Hours of cover", value: (row) => row.hours_of_cover }, { label: "Downtime hours", value: (row) => row.baseline_downtime_hours }, { label: "Exposure IDR", value: (row) => row.baseline_exposure_idr }, { label: "Approval", value: (row) => row.approval_status },
    ], filteredPortfolio());
  } else if (tableName === "routes") {
    const config = state.tables.routes;
    const query = config.query.trim().toLowerCase();
    const rows = state.network.routes.filter((route) => {
      const haystack = [route.route_id, route.label, route.material_id, route.source_id, route.destination_id].join(" ").toLowerCase();
      return (state.networkMode === "ALL" || route.route_type === "INBOUND_SHIPMENT") && (config.filter === "ALL" || route.status === config.filter) && (state.globalFilters.material === "ALL" || route.material_id === state.globalFilters.material) && (state.globalFilters.facility === "ALL" || route.source_id === state.globalFilters.facility || route.destination_id === state.globalFilters.facility) && (!query || haystack.includes(query));
    });
    downloadCsv("nsra-network-routes.csv", [{ label: "Route ID", value: (row) => row.route_id }, { label: "Route", value: (row) => row.label }, { label: "Type", value: (row) => row.route_type }, { label: "Material", value: (row) => row.material_id }, { label: "Delay hours", value: (row) => row.delay_hours }, { label: "Status", value: (row) => row.status }, { label: "Exposure IDR", value: (row) => row.exposure_idr }], rows);
  } else if (tableName === "scenarios" && state.analysis) {
    const config = state.tables.scenarios;
    const rows = [state.analysis.baseline, ...state.analysis.scenarios].filter((scenario) => config.filter === "ALL" || (config.filter === "FEASIBLE" ? scenario.feasible : !scenario.feasible));
    downloadCsv("nsra-scenarios.csv", [{ label: "Scenario ID", value: (row) => row.scenario_id }, { label: "Scenario", value: (row) => row.name }, { label: "Response cost IDR", value: (row) => row.cost_breakdown.logistics_and_purchase_idr }, { label: "Downtime hours", value: (row) => row.simulation.downtime_hours }, { label: "Total impact IDR", value: (row) => row.cost_breakdown.total_idr }, { label: "Feasible", value: (row) => row.feasible }], rows);
  } else if (tableName === "audit") {
    downloadCsv("nsra-audit.csv", [{ label: "Timestamp", value: (row) => row.timestamp }, { label: "Action", value: (row) => row.action }, { label: "Actor", value: (row) => row.actor }, { label: "Entity", value: (row) => `${row.entity_type}:${row.entity_id}` }, { label: "Incident", value: (row) => row.incident_id }, { label: "Summary", value: (row) => row.summary }], filteredAudit());
  } else if (tableName === "inventory" && state.analysis) {
    const recommended = findRecommendedScenario(state.analysis);
    const baseline = new Map(state.analysis.baseline.simulation.inventory_by_time.map((point) => [point.hour, point]));
    const response = recommended.simulation.inventory_by_time;
    downloadCsv("nsra-inventory-projection.csv", [{ label: "Hour", value: (row) => row.hour }, { label: "Baseline quantity", value: (row) => baseline.get(row.hour)?.quantity }, { label: "Recommended quantity", value: (row) => row.quantity }, { label: "Arrival quantity", value: (row) => row.arrival_quantity }, { label: "Unit", value: (row) => row.unit }], response);
  }
}

function positionTooltip(tooltip, target, event) {
  const shell = target.closest(".chart-shell");
  if (!shell || !tooltip) return;
  const shellRect = shell.getBoundingClientRect();
  const targetRect = target.getBoundingClientRect();
  const left = event?.clientX ? event.clientX - shellRect.left : targetRect.left - shellRect.left + targetRect.width / 2;
  const top = event?.clientY ? event.clientY - shellRect.top : targetRect.top - shellRect.top;
  tooltip.style.left = `${Math.max(12, Math.min(shellRect.width - 220, left + 12))}px`;
  tooltip.style.top = `${Math.max(12, top - 78)}px`;
}

function showInventoryTooltip(target, event) {
  const tooltip = target.closest("[data-inventory-chart]")?.querySelector("[data-inventory-tooltip]");
  if (!tooltip) return;
  tooltip.innerHTML = `<strong>Hour +${escapeHtml(target.dataset.hour)}</strong><span>Baseline <b>${formatNumber(target.dataset.baseline)} ${escapeHtml(target.dataset.unit)}</b></span><span>Recommended <b>${formatNumber(target.dataset.recommended)} ${escapeHtml(target.dataset.unit)}</b></span>${target.dataset.event ? `<small>${escapeHtml(target.dataset.event)}</small>` : ""}`;
  tooltip.hidden = false;
  positionTooltip(tooltip, target, event);
}

function showFrontierTooltip(target, event) {
  const tooltip = target.closest(".frontier-chart-shell")?.querySelector("[data-frontier-tooltip]");
  if (!tooltip) return;
  tooltip.innerHTML = `<strong>${escapeHtml(target.dataset.scenarioIndex)} · ${escapeHtml(target.dataset.scenarioName)}</strong><span>${escapeHtml(target.dataset.scenarioCost)} response</span><span>${escapeHtml(target.dataset.scenarioDowntime)} downtime</span><small>${escapeHtml(target.dataset.scenarioStatus)}</small>`;
  tooltip.hidden = false;
  positionTooltip(tooltip, target, event);
}

function hideChartTooltip(target) {
  const tooltip = target.closest(".chart-shell")?.querySelector(".chart-tooltip");
  if (tooltip) tooltip.hidden = true;
}

document.addEventListener("click", (event) => {
  const incidentViewLink = event.target.closest("[data-incident-view]");
  if (incidentViewLink) {
    event.preventDefault();
    state.incidentView = incidentViewLink.dataset.incidentView;
    saveUiPreferences();
    navigate(incidentViewLink.getAttribute("href"));
    return;
  }
  const sortButton = event.target.closest("[data-sort-table]");
  if (sortButton) {
    const config = state.tables[sortButton.dataset.sortTable];
    if (config.sortKey === sortButton.dataset.sortKey) config.direction = config.direction === "asc" ? "desc" : "asc";
    else { config.sortKey = sortButton.dataset.sortKey; config.direction = "asc"; }
    config.page = 1;
    refreshTable(sortButton.dataset.sortTable);
    return;
  }
  const pageButton = event.target.closest("[data-page-table]");
  if (pageButton) {
    state.tables[pageButton.dataset.pageTable].page += Number(pageButton.dataset.pageDelta);
    refreshTable(pageButton.dataset.pageTable);
    return;
  }
  const exportButton = event.target.closest("[data-export-table]");
  if (exportButton) { exportTable(exportButton.dataset.exportTable); return; }
  const rangeButton = event.target.closest("[data-inventory-range]");
  if (rangeButton && state.analysis) {
    state.inventoryRange = rangeButton.dataset.inventoryRange;
    saveUiPreferences();
    const target = document.querySelector("[data-inventory-chart]");
    if (target) target.outerHTML = renderInventoryProjection(state.analysis, findRecommendedScenario(state.analysis));
    return;
  }
  const scenarioPoint = event.target.closest("[data-scenario-point]");
  if (scenarioPoint && state.analysis) {
    state.selectedScenarioId = scenarioPoint.dataset.scenarioPoint;
    const target = document.querySelector("#scenario-frontier-body");
    if (target) target.outerHTML = renderScenarioFrontier(state.analysis);
    return;
  }
  if (event.target.closest("[data-clear-global-filters]")) {
    state.globalFilters = { facility: "ALL", material: "ALL", severity: "ALL" };
    saveUiPreferences();
    renderRoute();
    return;
  }
  if (event.target.closest("[data-map-fullscreen]")) { openNetworkMapDialog(); return; }
  if (event.target.closest("[data-close-network-map]")) { ui.networkMapDialog.close(); return; }
  const sectionLink = event.target.closest("[data-section-link]");
  if (sectionLink) {
    event.preventDefault();
    const target = document.querySelector(sectionLink.getAttribute("href"));
    if (target) {
      window.history.replaceState({}, "", `${window.location.pathname}${sectionLink.getAttribute("href")}`);
      target.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
      if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
      target.focus({ preventScroll: true });
      syncSectionNavigation();
    }
    return;
  }
  const link = event.target.closest("a[data-link], a.nav-item");
  if (link && link.origin === window.location.origin && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) {
    event.preventDefault();
    navigate(link.pathname + link.search);
    return;
  }
  const runButton = event.target.closest("[data-run-analysis]");
  if (runButton) { runAnalysis(runButton); return; }
  const createButton = event.target.closest("[data-create-draft]");
  if (createButton) { createDraft(createButton); return; }
  const reviewButton = event.target.closest("[data-review-draft]");
  if (reviewButton) { openDecision(reviewButton.dataset.reviewDraft); return; }
  const severityButton = event.target.closest("[data-portfolio-severity]");
  if (severityButton) {
    state.portfolioSeverity = severityButton.dataset.portfolioSeverity;
    state.tables.portfolio.page = 1;
    renderIncidentPortfolioPage();
    return;
  }
  const approvalButton = event.target.closest("[data-approval-status]");
  if (approvalButton) {
    state.approvalStatus = approvalButton.dataset.approvalStatus;
    renderApprovalsPage();
    return;
  }
  const modeButton = event.target.closest("[data-network-mode]");
  if (modeButton) {
    state.networkMode = modeButton.dataset.networkMode;
    state.selectedNodeId = null;
    state.tables.routes.page = 1;
    renderNetworkPage();
    return;
  }
  const zoomButton = event.target.closest("[data-map-zoom]");
  if (zoomButton) {
    setNetworkZoom(Number(zoomButton.dataset.mapZoom));
    return;
  }
  if (event.target.closest("[data-map-reset]")) {
    resetNetworkView();
    return;
  }
  const mapNode = event.target.closest("[data-network-node]");
  if (mapNode) selectNetworkNode(mapNode.dataset.networkNode);
});

document.addEventListener("input", (event) => {
  if (event.target.id === "portfolio-search") {
    state.portfolioQuery = event.target.value;
    state.tables.portfolio.page = 1;
    const results = document.querySelector("#portfolio-results");
    if (results) results.innerHTML = renderPortfolioResults(filteredPortfolio());
  }
  if (event.target.id === "route-search") {
    state.tables.routes.query = event.target.value;
    state.tables.routes.page = 1;
    const results = document.querySelector("#route-register-results");
    if (results) results.innerHTML = renderRouteTable(state.network);
    document.querySelector("#route-search")?.focus();
  }
  if (event.target.id === "audit-search") {
    state.auditQuery = event.target.value;
    state.tables.audit.page = 1;
    const results = document.querySelector("#audit-results");
    if (results) results.innerHTML = renderAuditResults();
  }
});

document.addEventListener("change", (event) => {
  if (event.target.matches("[data-global-filter]")) {
    state.globalFilters[event.target.dataset.globalFilter] = event.target.value;
    saveUiPreferences();
    renderRoute();
  } else if (event.target.matches("[data-page-size]")) {
    const config = state.tables[event.target.dataset.pageSize];
    config.pageSize = Number(event.target.value);
    config.page = 1;
    refreshTable(event.target.dataset.pageSize);
  } else if (event.target.matches("[data-route-status]")) {
    state.tables.routes.filter = event.target.value;
    state.tables.routes.page = 1;
    refreshTable("routes");
  } else if (event.target.matches("[data-scenario-filter]")) {
    state.tables.scenarios.filter = event.target.value;
    state.tables.scenarios.page = 1;
    refreshTable("scenarios");
  }
});

document.addEventListener("mouseover", (event) => {
  const inventoryHit = event.target.closest?.("[data-inventory-hit]");
  if (inventoryHit) showInventoryTooltip(inventoryHit, event);
  const frontierPoint = event.target.closest?.("[data-scenario-point]");
  if (frontierPoint) showFrontierTooltip(frontierPoint, event);
});

document.addEventListener("mouseout", (event) => {
  const target = event.target.closest?.("[data-inventory-hit], [data-scenario-point]");
  if (target && !target.contains(event.relatedTarget)) hideChartTooltip(target);
});

document.addEventListener("focusin", (event) => {
  const inventoryHit = event.target.closest?.("[data-inventory-hit]");
  if (inventoryHit) showInventoryTooltip(inventoryHit);
  const frontierPoint = event.target.closest?.("[data-scenario-point]");
  if (frontierPoint) showFrontierTooltip(frontierPoint);
});

document.addEventListener("focusout", (event) => {
  const target = event.target.closest?.("[data-inventory-hit], [data-scenario-point]");
  if (target) hideChartTooltip(target);
});

document.addEventListener("keydown", (event) => {
  const scenarioPoint = event.target.closest?.("[data-scenario-point]");
  if (scenarioPoint && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    scenarioPoint.click();
    return;
  }
  const node = event.target.closest?.("[data-network-node]");
  if (node && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    selectNetworkNode(node.dataset.networkNode);
  }
  const map = event.target.closest?.("[data-network-map]");
  if (map && event.target === map) {
    const keyActions = {
      "+": () => setNetworkZoom(0.25),
      "=": () => setNetworkZoom(0.25),
      "-": () => setNetworkZoom(-0.25),
      "0": resetNetworkView,
      ArrowLeft: () => panNetworkMap(40, 0),
      ArrowRight: () => panNetworkMap(-40, 0),
      ArrowUp: () => panNetworkMap(0, 32),
      ArrowDown: () => panNetworkMap(0, -32),
    };
    if (keyActions[event.key]) {
      event.preventDefault();
      keyActions[event.key]();
    }
  }
  if (event.key === "Escape") closeMobileNav();
});

let sectionScrollFrame = 0;
window.addEventListener("scroll", () => {
  if (sectionScrollFrame) return;
  sectionScrollFrame = window.requestAnimationFrame(() => {
    sectionScrollFrame = 0;
    syncSectionNavigation();
  });
}, { passive: true });

ui.retryButton.addEventListener("click", async () => {
  state.loaded = false;
  await renderRoute();
});

ui.refreshButton.addEventListener("click", async () => {
  try {
    await loadBaseData({ force: true });
    await renderRoute();
    showToast("Operational data refreshed.");
  } catch (error) {
    setBusy(false);
    showError(error);
  }
});

ui.mobileMenu.addEventListener("click", openMobileNav);
ui.mobileNavClose.addEventListener("click", closeMobileNav);
ui.sidebarScrim.addEventListener("click", closeMobileNav);
ui.environmentButton.addEventListener("click", () => {
  renderEnvironment();
  ui.resetConfirmation.hidden = true;
  ui.environmentDialog.showModal();
});
document.querySelectorAll("[data-close-environment]").forEach((button) => button.addEventListener("click", () => ui.environmentDialog.close()));
document.querySelectorAll("[data-close-dialog]").forEach((button) => button.addEventListener("click", () => ui.decisionDialog.close()));
ui.resetButton.addEventListener("click", () => {
  ui.resetConfirmation.hidden = false;
  ui.cancelResetButton.focus();
});
ui.cancelResetButton.addEventListener("click", () => {
  ui.resetConfirmation.hidden = true;
  ui.resetButton.focus();
});
ui.confirmResetButton.addEventListener("click", resetWorkspace);
document.querySelectorAll("[data-decision]").forEach((button) => button.addEventListener("click", () => submitDecision(button.dataset.decision, button)));
[ui.environmentDialog, ui.decisionDialog, ui.networkMapDialog].forEach((dialog) => dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
}));
window.addEventListener("popstate", () => renderRoute({ focus: true }));

if (window.location.pathname === "/") {
  window.history.replaceState({}, "", "/overview");
}
renderRoute();
