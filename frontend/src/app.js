import { dataset } from "./generated/osint-data.js";
import { computeLocationScores } from "./lib/scoring.js";
import { scoresToGeoJSON, signalEventsToGeoJSON } from "./lib/geojson.js";
import {
  OVERLAY_REGISTRY,
  OVERLAY_CATEGORIES,
  loadOverlayPreferences,
  saveOverlayPreference,
  addOverlayLayers,
  setOverlayVisibility,
} from "./lib/overlays.js";
import { applyMapTheme } from "./lib/mapTheme.js";
import { loadFlagImage } from "./lib/flagImage.js";

/* global maplibregl */

const controls = {
  projection: document.getElementById("projection-select"),
  timeWindow: document.getElementById("time-window-select"),
  sourceFamily: document.getElementById("source-family-select"),
  emphasis: document.getElementById("emphasis-select"),
  confidence: document.getElementById("confidence-range"),
  heatmap: document.getElementById("heatmap-toggle")
};

const ui = {
  hotspotList: document.getElementById("hotspot-list"),
  lastUpdated: document.getElementById("last-updated"),
  sourceSummary: document.getElementById("source-summary"),
  detailName: document.getElementById("detail-name"),
  detailBrief: document.getElementById("detail-brief"),
  trendPill: document.getElementById("trend-pill"),
  detailHeat: document.getElementById("detail-heat"),
  detailDelta: document.getElementById("detail-delta"),
  detailConfidence: document.getElementById("detail-confidence"),
  civilScore: document.getElementById("civil-score"),
  militaryScore: document.getElementById("military-score"),
  civilMeter: document.getElementById("civil-meter"),
  militaryMeter: document.getElementById("military-meter"),
  driverList: document.getElementById("driver-list"),
  evidenceList: document.getElementById("evidence-list"),
  actionList: document.getElementById("action-list"),
  sparkline: document.getElementById("sparkline"),
  confidenceOutput: document.getElementById("confidence-output"),
  metricHotspots: document.getElementById("metric-hotspots"),
  metricSignals: document.getElementById("metric-signals"),
  metricSources: document.getElementById("metric-sources"),
  metricWindow: document.getElementById("metric-window")
};

const state = {
  projection: "globe",
  sourceFamily: "all",
  emphasis: "blend",
  timeWindowHours: 24,
  confidenceFloor: 0.5,
  selectedLocationId: null,
  heatmapEnabled: true
};

let visibleScores = [];
let map = null;
let overlayPrefs = loadOverlayPreferences();

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function formatHoursAgo(timestamp) {
  const hours = Math.round(
    (new Date(dataset.generatedAt).getTime() - new Date(timestamp).getTime()) / 36e5
  );
  return `${hours}h ago`;
}

function formatDelta(delta) {
  return `${delta > 0 ? "+" : ""}${delta.toFixed(0)}`;
}

function selectedLabel(score) {
  return score ? score.trend : "steady";
}

function getFilteredSignalEvents() {
  return dataset.signalEvents.filter((event) => {
    const ageHours = (new Date(dataset.generatedAt).getTime() - new Date(event.timestamp).getTime()) / 36e5;
    const withinWindow = ageHours <= state.timeWindowHours;
    const matchesSource = state.sourceFamily === "all" || event.sourceFamily === state.sourceFamily;
    const matchesConfidence = event.geo.confidence >= state.confidenceFloor;
    return withinWindow && matchesSource && matchesConfidence;
  });
}

function recomputeVisibleScores() {
  visibleScores = computeLocationScores(getFilteredSignalEvents(), {
    referenceTime: dataset.generatedAt,
    emphasis: state.emphasis
  }).filter((score) => score.confidence >= state.confidenceFloor);

  if (!visibleScores.length) {
    state.selectedLocationId = null;
    return;
  }

  const selectedStillVisible = visibleScores.some((score) => score.id === state.selectedLocationId);
  if (!selectedStillVisible) {
    state.selectedLocationId = visibleScores[0].id;
  }
}

function getSelectedScore() {
  return visibleScores.find((score) => score.id === state.selectedLocationId) ?? visibleScores[0] ?? null;
}

// ---------------------------------------------------------------------------
// MapLibre Setup
// ---------------------------------------------------------------------------

function initMap() {
  map = new maplibregl.Map({
    container: "map-container",
    style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    center: [32, 10],
    zoom: 2,
    attributionControl: false,
    maxZoom: 12,
    minZoom: 1
  });

  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

  map.on("style.load", () => {
    applyProjection();
  });

  map.on("load", () => {
    applyMapTheme(map);
    setupSources();

    // Register flag image handler BEFORE layers that reference flag-* images
    map.on("styleimagemissing", (e) => {
      if (e.id.startsWith("flag-")) {
        const countryCode = e.id.replace("flag-", "");
        loadFlagImage(map, countryCode).then(() => {
          map.triggerRepaint();
        });
      }
    });

    setupOverlayLayers();
    setupLayers();
    setupInteractivity();
    updateMapData();
    renderOverlayPanel();
  });
}

function applyProjection() {
  if (!map) return;
  map.setProjection({ type: state.projection === "globe" ? "globe" : "mercator" });
}

function setupSources() {
  map.addSource("signal-events", {
    type: "geojson",
    data: signalEventsToGeoJSON([])
  });

  map.addSource("hotspots", {
    type: "geojson",
    data: scoresToGeoJSON([]),
    generateId: true
  });

  // Overlay sources — load GeoJSON for each registered overlay
  for (const overlay of OVERLAY_REGISTRY) {
    map.addSource(overlay.id, {
      type: "geojson",
      data: overlay.dataUrl
    });
  }
}

function setupOverlayLayers() {
  for (const overlay of OVERLAY_REGISTRY) {
    addOverlayLayers(map, overlay.id, overlayPrefs[overlay.id]);
  }
}

function setupLayers() {
  // Heatmap layer — signal event density weighted by severity
  map.addLayer({
    id: "signal-heatmap",
    type: "heatmap",
    source: "signal-events",
    paint: {
      "heatmap-weight": ["get", "weight"],
      "heatmap-intensity": [
        "interpolate", ["linear"], ["zoom"],
        1, 0.6,
        6, 1.2,
        10, 2
      ],
      "heatmap-radius": [
        "interpolate", ["linear"], ["zoom"],
        1, 20,
        6, 35,
        10, 50
      ],
      "heatmap-color": [
        "interpolate", ["linear"], ["heatmap-density"],
        0,    "rgba(0, 0, 0, 0)",
        0.1,  "rgba(10, 60, 120, 0.35)",
        0.25, "rgba(20, 140, 210, 0.5)",
        0.4,  "rgba(73, 212, 186, 0.6)",
        0.6,  "rgba(180, 210, 140, 0.7)",
        0.8,  "rgba(255, 178, 95, 0.85)",
        1.0,  "rgba(255, 80, 50, 0.95)"
      ],
      "heatmap-opacity": 0.75
    }
  });

  // Glow ring behind hotspot circles
  map.addLayer({
    id: "hotspot-glow",
    type: "circle",
    source: "hotspots",
    paint: {
      "circle-radius": [
        "interpolate", ["linear"], ["get", "heat"],
        0, 14,
        50, 24,
        100, 40
      ],
      "circle-color": [
        "interpolate", ["linear"], ["get", "heat"],
        0,   "#49d4ba",
        50,  "#ffb25f",
        100, "#ff7557"
      ],
      "circle-opacity": 0.14,
      "circle-blur": 0.9
    }
  });

  // Hotspot markers
  map.addLayer({
    id: "hotspot-circles",
    type: "circle",
    source: "hotspots",
    paint: {
      "circle-radius": [
        "interpolate", ["linear"], ["get", "heat"],
        0, 6,
        50, 11,
        100, 18
      ],
      "circle-color": [
        "interpolate", ["linear"], ["get", "heat"],
        0,   "#49d4ba",
        50,  "#ffb25f",
        100, "#ff7557"
      ],
      "circle-opacity": 0.88,
      "circle-stroke-width": [
        "case",
        ["==", ["get", "id"], state.selectedLocationId || ""],
        2.2,
        0
      ],
      "circle-stroke-color": "rgba(255, 255, 255, 0.92)",
      "circle-blur": 0.1
    }
  });

  // Bright center dot
  map.addLayer({
    id: "hotspot-center",
    type: "circle",
    source: "hotspots",
    paint: {
      "circle-radius": 3,
      "circle-color": "rgba(245, 250, 255, 0.96)",
      "circle-opacity": 0.95
    }
  });

  // Labels for hotspots
  map.addLayer({
    id: "hotspot-labels",
    type: "symbol",
    source: "hotspots",
    layout: {
      "text-field": ["upcase", ["get", "name"]],
      "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
      "text-size": 11,
      "text-offset": [0, -2.2],
      "text-anchor": "bottom",
      "text-allow-overlap": true
    },
    paint: {
      "text-color": "#f5f8ff",
      "text-halo-color": "rgba(4, 9, 16, 0.92)",
      "text-halo-width": 2
    },
    filter: ["==", ["get", "id"], state.selectedLocationId || ""]
  });
}

function setupInteractivity() {
  map.on("click", "hotspot-circles", (event) => {
    const feature = event.features[0];
    if (feature) {
      selectHotspot(feature.properties.id);
    }
  });

  map.on("mouseenter", "hotspot-circles", () => {
    map.getCanvas().style.cursor = "pointer";
  });

  map.on("mouseleave", "hotspot-circles", () => {
    map.getCanvas().style.cursor = "";
  });
}

function selectHotspot(scoreId) {
  state.selectedLocationId = scoreId;
  const score = getSelectedScore();

  updateSelectedStyling();
  renderHotspotList();
  renderDetails();

  if (score) {
    map.flyTo({
      center: [score.center.lon, score.center.lat],
      zoom: Math.max(map.getZoom(), 4),
      duration: 1200
    });
  }
}

function updateSelectedStyling() {
  if (!map.getLayer("hotspot-circles")) return;

  map.setPaintProperty("hotspot-circles", "circle-stroke-width", [
    "case",
    ["==", ["get", "id"], state.selectedLocationId || ""],
    2.2,
    0
  ]);

  map.setFilter("hotspot-labels", [
    "==", ["get", "id"], state.selectedLocationId || ""
  ]);
}

function updateMapData() {
  recomputeVisibleScores();

  if (!map || !map.getSource("signal-events")) return;

  const filteredEvents = getFilteredSignalEvents();
  map.getSource("signal-events").setData(signalEventsToGeoJSON(filteredEvents));
  map.getSource("hotspots").setData(scoresToGeoJSON(visibleScores));

  map.setLayoutProperty("signal-heatmap", "visibility",
    state.heatmapEnabled ? "visible" : "none"
  );

  updateSelectedStyling();
  renderMetrics();
  renderHotspotList();
  renderDetails();
}

// ---------------------------------------------------------------------------
// Overlay Panel
// ---------------------------------------------------------------------------

function renderOverlayPanel() {
  const panel = document.getElementById("overlay-panel");
  const list = document.getElementById("overlay-list");
  const badge = document.getElementById("overlay-count");
  if (!list) return;

  const activeCount = OVERLAY_REGISTRY.filter((o) => overlayPrefs[o.id]).length;
  if (badge) {
    badge.textContent = activeCount > 0 ? `${activeCount}` : "";
    badge.hidden = activeCount === 0;
  }

  list.innerHTML = "";

  for (const cat of OVERLAY_CATEGORIES) {
    const overlaysInCategory = OVERLAY_REGISTRY.filter((o) => o.category === cat.key);
    if (!overlaysInCategory.length) continue;

    const group = document.createElement("div");
    group.className = "overlay-group";

    const heading = document.createElement("p");
    heading.className = "overlay-category";
    heading.textContent = cat.label;
    group.appendChild(heading);

    for (const overlay of overlaysInCategory) {
      const row = document.createElement("label");
      row.className = `overlay-item${overlayPrefs[overlay.id] ? " is-active" : ""}`;

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = overlayPrefs[overlay.id];
      checkbox.addEventListener("change", () => {
        overlayPrefs[overlay.id] = checkbox.checked;
        saveOverlayPreference(overlay.id, checkbox.checked);
        setOverlayVisibility(map, overlay.id, checkbox.checked);
        row.classList.toggle("is-active", checkbox.checked);
        renderOverlayPanel();
      });

      const info = document.createElement("div");
      info.className = "overlay-info";

      const name = document.createElement("span");
      name.className = "overlay-name";
      name.textContent = overlay.label;

      const desc = document.createElement("span");
      desc.className = "overlay-desc";
      desc.textContent = overlay.desc;

      info.append(name, desc);
      row.append(checkbox, info);
      group.appendChild(row);
    }

    list.appendChild(group);
  }
}

function attachOverlayPanelListeners() {
  const toggle = document.getElementById("overlay-toggle");
  const panel = document.getElementById("overlay-panel");
  if (!toggle || !panel) return;

  toggle.addEventListener("click", () => {
    panel.classList.toggle("is-open");
    toggle.classList.toggle("is-active");
  });
}

// ---------------------------------------------------------------------------
// UI Rendering (unchanged from original)
// ---------------------------------------------------------------------------

function renderMetrics() {
  const filteredEvents = getFilteredSignalEvents();
  const sourceCount = unique(
    filteredEvents.map((event) => event.sourceName ?? event.sourceFamily ?? event.source)
  ).length;

  ui.metricHotspots.textContent = `${visibleScores.length}`;
  ui.metricSignals.textContent = `${filteredEvents.length}`;
  ui.metricSources.textContent = `${sourceCount}`;
  ui.metricWindow.textContent = `${state.timeWindowHours}h`;
  ui.confidenceOutput.textContent = `${Math.round(state.confidenceFloor * 100)}%`;
}

function renderHotspotList() {
  ui.hotspotList.innerHTML = "";

  if (!visibleScores.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No theaters match the active filters";
    ui.hotspotList.appendChild(empty);
    return;
  }

  visibleScores.slice(0, 6).forEach((score, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `hotspot-chip${score.id === state.selectedLocationId ? " is-active" : ""}`;
    button.innerHTML = `
      <span class="chip-rank">${String(index + 1).padStart(2, "0")} priority</span>
      <span class="chip-name">${score.name}</span>
      <span class="chip-delta">${formatDelta(score.delta)} delta</span>
      <span class="chip-meta">${score.heat.toFixed(0)} heat · ${selectedLabel(score)}</span>
    `;
    button.addEventListener("click", () => {
      selectHotspot(score.id);
    });
    ui.hotspotList.appendChild(button);
  });
}

function renderSparkline(history) {
  if (!history.length) {
    ui.sparkline.innerHTML = "";
    return;
  }

  const maxValue = Math.max(...history, 1);
  const points = history.map((value, index) => ({
    x: index * (240 / Math.max(history.length - 1, 1)),
    y: 68 - (value / maxValue) * 54
  }));
  const polylinePoints = points.map((point) => `${point.x},${point.y}`).join(" ");
  const areaPoints = `0,72 ${polylinePoints} 240,72`;
  const lastPoint = points.at(-1);

  ui.sparkline.innerHTML = `
    <defs>
      <linearGradient id="spark-fill" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="rgba(255, 178, 95, 0.42)" />
        <stop offset="100%" stop-color="rgba(255, 178, 95, 0)" />
      </linearGradient>
    </defs>
    <polygon fill="url(#spark-fill)" points="${areaPoints}" />
    <polyline
      fill="none"
      stroke="rgba(255, 178, 95, 0.95)"
      stroke-width="3"
      points="${polylinePoints}"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <circle
      cx="${lastPoint.x}"
      cy="${lastPoint.y}"
      r="4"
      fill="rgba(255, 245, 232, 0.96)"
      stroke="rgba(255, 178, 95, 0.88)"
      stroke-width="2"
    />
  `;
}

function recommendedActions(score) {
  const actions = [];

  if (score.militaryComponent > score.civilComponent) {
    actions.push("Review recent reporting on force posture, officer churn, and command changes in nearby garrisons.");
    actions.push("Cross-check convoy and deployment mentions against satellite, NOTAM, or transport disruption signals.");
  } else {
    actions.push("Expand collection on protest organizers, strike calls, and security-force response in adjacent districts.");
    actions.push("Look for linked local radio, civic channels, and municipal feeds to confirm whether unrest is spreading.");
  }

  if (score.sourceBreakdown.includes("x") || score.sourceBreakdown.includes("bluesky")) {
    actions.push("Sample high-velocity social accounts for coordination patterns and repeated narrative frames.");
  }

  return actions.slice(0, 3);
}

function buildDetailBrief(score) {
  const dominant = score.militaryComponent > score.civilComponent + 8
    ? "Military-led"
    : score.civilComponent > score.militaryComponent + 8
      ? "Civil-led"
      : "Mixed";

  return `${dominant} pressure profile with ${score.evidenceBundle.length} corroborating items in the current ${state.timeWindowHours}h watch window at ${Math.round(score.confidence * 100)}% geo confidence.`;
}

function clearDetails() {
  ui.detailName.textContent = "No active theater";
  ui.detailBrief.textContent = "Adjust the current filters to surface an active location.";
  ui.trendPill.textContent = "steady";
  ui.trendPill.dataset.trend = "steady";
  ui.detailHeat.textContent = "0";
  ui.detailDelta.textContent = "0";
  ui.detailConfidence.textContent = "0%";
  ui.civilScore.textContent = "0";
  ui.militaryScore.textContent = "0";
  ui.civilMeter.style.width = "0%";
  ui.militaryMeter.style.width = "0%";
  ui.driverList.innerHTML = "";
  ui.evidenceList.innerHTML = '<p class="empty-state">No corroborating items for the current filter set</p>';
  ui.actionList.innerHTML = "";
  ui.sparkline.innerHTML = "";
}

function renderDetails() {
  const score = getSelectedScore();

  if (!score) {
    clearDetails();
    return;
  }

  ui.detailName.textContent = score.name;
  ui.detailBrief.textContent = buildDetailBrief(score);
  ui.trendPill.textContent = selectedLabel(score);
  ui.trendPill.dataset.trend = score.trend;
  ui.detailHeat.textContent = score.heat.toFixed(0);
  ui.detailDelta.textContent = formatDelta(score.delta);
  ui.detailConfidence.textContent = `${Math.round(score.confidence * 100)}%`;
  ui.civilScore.textContent = score.civilComponent.toFixed(0);
  ui.militaryScore.textContent = score.militaryComponent.toFixed(0);
  ui.civilMeter.style.width = `${Math.min(100, score.civilComponent)}%`;
  ui.militaryMeter.style.width = `${Math.min(100, score.militaryComponent)}%`;

  renderSparkline(score.history);

  ui.driverList.innerHTML = "";
  score.topDrivers.forEach((driver) => {
    const item = document.createElement("li");
    item.textContent = driver;
    ui.driverList.appendChild(item);
  });

  ui.evidenceList.innerHTML = "";
  score.evidenceBundle.forEach((event) => {
    const card = document.createElement("article");
    card.className = "evidence-item";
    const meta = document.createElement("div");
    meta.className = "evidence-meta";
    const sourceLabel = document.createElement("span");
    sourceLabel.textContent = event.sourceFamily;
    const ageLabel = document.createElement("span");
    ageLabel.textContent = formatHoursAgo(event.timestamp);
    meta.append(sourceLabel, ageLabel);

    const heading = document.createElement("h4");
    if (event.url) {
      const link = document.createElement("a");
      link.href = event.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = event.title;
      heading.appendChild(link);
    } else {
      heading.textContent = event.title;
    }

    const body = document.createElement("p");
    body.textContent = event.excerpt;

    const footer = document.createElement("footer");
    const authorName = event.author?.handle ? `@${event.author.handle}` : event.author?.name ?? event.sourceName;
    const geoLabel = document.createElement("span");
    geoLabel.textContent = `${authorName} · ${event.geo.name} · ${Math.round(event.geo.confidence * 100)}% geo confidence`;
    const typeLabel = document.createElement("span");
    typeLabel.textContent = event.classification.signalType;
    footer.append(geoLabel, typeLabel);

    card.append(meta, heading, body, footer);
    ui.evidenceList.appendChild(card);
  });

  ui.actionList.innerHTML = "";
  recommendedActions(score).forEach((action) => {
    const item = document.createElement("li");
    item.textContent = action;
    ui.actionList.appendChild(item);
  });
}

// ---------------------------------------------------------------------------
// Controls & Listeners
// ---------------------------------------------------------------------------

function syncControls() {
  const sourceOptions = [
    { value: "all", label: "All sources" },
    ...unique(dataset.signalEvents.map((event) => event.sourceFamily)).map((family) => ({
      value: family,
      label: family.charAt(0).toUpperCase() + family.slice(1)
    }))
  ];

  controls.sourceFamily.innerHTML = sourceOptions
    .map((option) => `<option value="${option.value}">${option.label}</option>`)
    .join("");

  controls.projection.value = state.projection;
  controls.timeWindow.value = String(state.timeWindowHours);
  controls.sourceFamily.value = state.sourceFamily;
  controls.emphasis.value = state.emphasis;
  controls.confidence.value = String(state.confidenceFloor * 100);
  controls.heatmap.checked = state.heatmapEnabled;
  ui.confidenceOutput.textContent = `${Math.round(state.confidenceFloor * 100)}%`;
}

function attachListeners() {
  controls.projection.addEventListener("change", (event) => {
    state.projection = event.target.value;
    applyProjection();
  });

  controls.timeWindow.addEventListener("change", (event) => {
    state.timeWindowHours = Number(event.target.value);
    updateMapData();
  });

  controls.sourceFamily.addEventListener("change", (event) => {
    state.sourceFamily = event.target.value;
    updateMapData();
  });

  controls.emphasis.addEventListener("change", (event) => {
    state.emphasis = event.target.value;
    updateMapData();
  });

  controls.confidence.addEventListener("input", (event) => {
    state.confidenceFloor = Number(event.target.value) / 100;
    ui.confidenceOutput.textContent = `${Math.round(state.confidenceFloor * 100)}%`;
    updateMapData();
  });

  controls.heatmap.addEventListener("change", (event) => {
    state.heatmapEnabled = event.target.checked;
    if (map && map.getLayer("signal-heatmap")) {
      map.setLayoutProperty("signal-heatmap", "visibility",
        state.heatmapEnabled ? "visible" : "none"
      );
    }
  });

  window.addEventListener("resize", () => {
    if (map) map.resize();
  });
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

function init() {
  ui.lastUpdated.textContent = `Snapshot ${new Date(dataset.generatedAt).toLocaleString()}`;

  const sourceCatalog = dataset.sourceCatalog?.length ? dataset.sourceCatalog : dataset.feedCatalog ?? [];
  if (sourceCatalog.length) {
    const sources = unique(sourceCatalog.map((entry) => entry.source));
    let summary = `${sources.slice(0, 4).join(" + ")} · ${sourceCatalog.length} live feeds`;
    if (dataset.sourceStatus?.bluesky !== "loaded") {
      summary += " · Bluesky cache missing";
    }
    ui.sourceSummary.textContent = summary;
  } else if (dataset.failures?.length) {
    ui.sourceSummary.textContent = "Live refresh failed, showing demo cache";
  } else if (dataset.sourceStatus?.bluesky !== "loaded") {
    ui.sourceSummary.textContent = "Bluesky cache missing, showing available sources only";
  }

  syncControls();
  attachListeners();
  attachOverlayPanelListeners();
  initMap();
}

init();
