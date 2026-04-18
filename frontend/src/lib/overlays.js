/**
 * Overlay registry and preferences management.
 * Mirrors the cnak MapPreferencesContext pattern adapted for vanilla JS.
 */

const STORAGE_PREFIX = "signalatlas_overlay_";

export const OVERLAY_CATEGORIES = [
  { key: "military",       label: "Military" },
  { key: "infrastructure", label: "Infrastructure" },
  { key: "maritime",       label: "Maritime" },
  { key: "air",            label: "Air" },
  { key: "ground",         label: "Ground" },
  { key: "geopolitical",   label: "Geopolitical" },
  { key: "humanitarian",   label: "Humanitarian" },
  { key: "hazard",         label: "Natural Hazard" },
];

export const OVERLAY_REGISTRY = [
  {
    id: "bases",
    label: "Military Bases",
    desc: "Known military installations, airfields, and naval stations worldwide.",
    category: "military",
    dataUrl: "/overlays/bases.json",
    defaultVisible: false,
    layerType: "point",
  },
  {
    id: "embassies",
    label: "Embassies & Consulates",
    desc: "Diplomatic missions, embassies, and consulates by operating country.",
    category: "ground",
    dataUrl: "/overlays/embassies.json",
    defaultVisible: false,
    layerType: "point",
  },
  {
    id: "airports",
    label: "Airports",
    desc: "Major, mid-size, military, and small airfields globally.",
    category: "air",
    dataUrl: "/overlays/airports.json",
    defaultVisible: false,
    layerType: "point",
  },
  {
    id: "ports",
    label: "Ports & Harbors",
    desc: "Major seaports and harbors by size classification.",
    category: "maritime",
    dataUrl: "/overlays/ports.json",
    defaultVisible: false,
    layerType: "point",
  },
  {
    id: "pipelines",
    label: "Pipelines",
    desc: "Oil, gas, and ethylene pipeline routes.",
    category: "infrastructure",
    dataUrl: "/overlays/pipelines.json",
    defaultVisible: false,
    layerType: "line",
  },
  {
    id: "cables",
    label: "Submarine Cables",
    desc: "Undersea telecommunications cable routes.",
    category: "infrastructure",
    dataUrl: "/overlays/cables.json",
    defaultVisible: false,
    layerType: "line",
  },
  {
    id: "nuclear",
    label: "Nuclear Facilities",
    desc: "Nuclear power plants by operational status and capacity.",
    category: "infrastructure",
    dataUrl: "/overlays/nuclear.json",
    defaultVisible: false,
    layerType: "point",
  },
  {
    id: "eez",
    label: "Exclusive Economic Zones",
    desc: "Maritime EEZ boundary lines (200 nautical miles).",
    category: "maritime",
    dataUrl: "/overlays/eez.json",
    defaultVisible: false,
    layerType: "line",
  },
  {
    id: "spaceports",
    label: "Space Launch Facilities",
    desc: "Orbital and suborbital launch sites worldwide.",
    category: "air",
    dataUrl: "/overlays/spaceports.json",
    defaultVisible: false,
    layerType: "point",
  },
  {
    id: "chokepoints",
    label: "Maritime Chokepoints",
    desc: "Strategic straits, canals, and transit zones controlling global shipping lanes.",
    category: "maritime",
    dataUrl: "/overlays/chokepoints.json",
    defaultVisible: false,
    layerType: "point",
  },
  {
    id: "disputed",
    label: "Disputed Territories",
    desc: "Contested sovereignty zones, occupied territories, and breakaway regions.",
    category: "geopolitical",
    dataUrl: "/overlays/disputed.json",
    defaultVisible: false,
    layerType: "polygon",
  },
  {
    id: "powerplants",
    label: "Power Plants",
    desc: "Major power generation facilities (500 MW+) by fuel type and capacity.",
    category: "infrastructure",
    dataUrl: "/overlays/powerplants.json",
    defaultVisible: false,
    layerType: "point",
  },
  {
    id: "cable-landings",
    label: "Cable Landing Stations",
    desc: "Shore terminals where undersea telecommunications cables make landfall.",
    category: "infrastructure",
    dataUrl: "/overlays/cable-landings.json",
    defaultVisible: false,
    layerType: "point",
  },
  {
    id: "volcanoes",
    label: "Volcanoes",
    desc: "Significant Holocene volcanoes by type and activity status.",
    category: "hazard",
    dataUrl: "/overlays/volcanoes.json",
    defaultVisible: false,
    layerType: "point",
  },
  {
    id: "refugee-camps",
    label: "Refugee & IDP Camps",
    desc: "Major refugee camps, IDP settlements, and humanitarian reception centers.",
    category: "humanitarian",
    dataUrl: "/overlays/refugee-camps.json",
    defaultVisible: false,
    layerType: "point",
  },
];

// ---------------------------------------------------------------------------
// Preferences (localStorage persistence)
// ---------------------------------------------------------------------------

export function loadOverlayPreferences() {
  const prefs = {};
  for (const overlay of OVERLAY_REGISTRY) {
    const stored = localStorage.getItem(STORAGE_PREFIX + overlay.id);
    prefs[overlay.id] = stored !== null ? stored === "true" : overlay.defaultVisible;
  }
  return prefs;
}

export function saveOverlayPreference(id, visible) {
  localStorage.setItem(STORAGE_PREFIX + id, String(visible));
}

export function loadOverlayOpacity(id) {
  const stored = localStorage.getItem(STORAGE_PREFIX + id + "_opacity");
  return stored !== null ? Number(stored) : 100;
}

export function saveOverlayOpacity(id, opacity) {
  localStorage.setItem(STORAGE_PREFIX + id + "_opacity", String(opacity));
}

// ---------------------------------------------------------------------------
// MapLibre Layer Definitions (matching cnak styling)
// ---------------------------------------------------------------------------

const AIRPORT_COLORS = {
  major:                "#9333ea",
  "major and military": "#9333ea",
  "military major":     "#9333ea",
  mid:                  "#a855f7",
  "mid and military":   "#a855f7",
  "military mid":       "#a855f7",
  military:             "#c084fc",
  small:                "#d8b4fe",
  spaceport:            "#ec4899",
  default:              "#a855f7",
};

export function addOverlayLayers(map, overlayId, visible) {
  const vis = visible ? "visible" : "none";

  switch (overlayId) {
    case "bases":
      map.addLayer({
        id: "bases-markers",
        type: "symbol",
        source: "bases",
        layout: {
          visibility: vis,
          "icon-image": ["concat", "flag-", ["downcase", ["get", "country"]]],
          "icon-size": ["interpolate", ["linear"], ["zoom"], 2, 0.3, 6, 0.45, 10, 0.6],
          "icon-allow-overlap": true,
          "icon-ignore-placement": true,
          "icon-anchor": "center",
        },
        paint: {
          "icon-opacity": 0.85,
        },
        minzoom: 1,
      });
      map.addLayer({
        id: "bases-labels",
        type: "symbol",
        source: "bases",
        layout: {
          visibility: vis,
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": ["interpolate", ["linear"], ["zoom"], 4, 0, 6, 10, 10, 12],
          "text-offset": [0, 1.2],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#fca5a5",
          "text-halo-color": "rgba(17,18,23,0.8)",
          "text-halo-width": 1,
        },
        minzoom: 3,
      });
      break;

    case "embassies":
      map.addLayer({
        id: "embassies-markers",
        type: "symbol",
        source: "embassies",
        layout: {
          visibility: vis,
          "icon-image": [
            "case",
            ["all", ["has", "operatorCode"], ["!=", ["get", "operatorCode"], ""]],
            ["concat", "flag-", ["downcase", ["get", "operatorCode"]]],
            "flag-xx",
          ],
          "icon-size": ["interpolate", ["linear"], ["zoom"], 2, 0.3, 6, 0.45, 10, 0.6],
          "icon-allow-overlap": true,
          "icon-ignore-placement": true,
          "icon-anchor": "center",
        },
        paint: {
          "icon-opacity": 0.75,
        },
        minzoom: 1,
      });
      map.addLayer({
        id: "embassies-labels",
        type: "symbol",
        source: "embassies",
        layout: {
          visibility: vis,
          "text-field": ["get", "operator"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": ["interpolate", ["linear"], ["zoom"], 4, 0, 6, 10, 10, 12],
          "text-offset": [0, 1.2],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#a5f3fc",
          "text-halo-color": "rgba(17,18,23,0.8)",
          "text-halo-width": 1,
        },
        minzoom: 6,
      });
      break;

    case "airports":
      map.addLayer({
        id: "airports-markers",
        type: "circle",
        source: "airports",
        layout: { visibility: vis },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 2, 6, 4, 10, 6],
          "circle-color": [
            "match", ["get", "type"],
            "major",              AIRPORT_COLORS.major,
            "major and military", AIRPORT_COLORS["major and military"],
            "military major",     AIRPORT_COLORS["military major"],
            "mid",                AIRPORT_COLORS.mid,
            "mid and military",   AIRPORT_COLORS["mid and military"],
            "military mid",       AIRPORT_COLORS["military mid"],
            "military",           AIRPORT_COLORS.military,
            "small",              AIRPORT_COLORS.small,
            "spaceport",          AIRPORT_COLORS.spaceport,
            AIRPORT_COLORS.default,
          ],
          "circle-opacity": 0.85,
          "circle-stroke-width": 1.5,
          "circle-stroke-color": "rgba(255,255,255,0.3)",
        },
      });
      map.addLayer({
        id: "airports-labels",
        type: "symbol",
        source: "airports",
        layout: {
          visibility: vis,
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": 10,
          "text-offset": [0, 1.4],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#c4b5fd",
          "text-halo-color": "rgba(17,18,23,0.8)",
          "text-halo-width": 1,
        },
        minzoom: 5,
      });
      break;

    case "ports":
      map.addLayer({
        id: "ports-markers",
        type: "circle",
        source: "ports",
        layout: { visibility: vis },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 3, 6, 5, 10, 7],
          "circle-color": [
            "match", ["get", "harborSize"],
            "large",  "#0ea5e9",
            "medium", "#38bdf8",
            "small",  "#7dd3fc",
            "#38bdf8",
          ],
          "circle-opacity": 0.85,
          "circle-stroke-width": 1.5,
          "circle-stroke-color": "rgba(255,255,255,0.4)",
        },
      });
      map.addLayer({
        id: "ports-labels",
        type: "symbol",
        source: "ports",
        layout: {
          visibility: vis,
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": 10,
          "text-offset": [0, 1.4],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#7dd3fc",
          "text-halo-color": "rgba(17,18,23,0.8)",
          "text-halo-width": 1,
        },
        minzoom: 4,
      });
      break;

    case "pipelines":
      map.addLayer({
        id: "pipelines-lines",
        type: "line",
        source: "pipelines",
        layout: { visibility: vis },
        paint: {
          "line-color": [
            "match", ["get", "substance"],
            "gas",      "#60a5fa",
            "oil",      "#f97316",
            "ethylene", "#a78bfa",
            "#94a3b8",
          ],
          "line-width": ["interpolate", ["linear"], ["zoom"], 2, 1, 6, 1.5, 10, 2.5],
          "line-opacity": 0.7,
        },
      });
      map.addLayer({
        id: "pipelines-labels",
        type: "symbol",
        source: "pipelines",
        layout: {
          visibility: vis,
          "symbol-placement": "line",
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": 10,
          "text-optional": true,
        },
        paint: {
          "text-color": "#94a3b8",
          "text-halo-color": "rgba(17,18,23,0.8)",
          "text-halo-width": 1,
        },
        minzoom: 5,
      });
      break;

    case "cables":
      map.addLayer({
        id: "cables-lines",
        type: "line",
        source: "cables",
        layout: { visibility: vis },
        paint: {
          "line-color": ["coalesce", ["get", "color"], "#94a3b8"],
          "line-width": ["interpolate", ["linear"], ["zoom"], 2, 0.8, 6, 1.2, 10, 2],
          "line-opacity": 0.6,
        },
      });
      map.addLayer({
        id: "cables-labels",
        type: "symbol",
        source: "cables",
        layout: {
          visibility: vis,
          "symbol-placement": "line",
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": 10,
          "text-optional": true,
        },
        paint: {
          "text-color": "#cbd5e1",
          "text-halo-color": "rgba(17,18,23,0.8)",
          "text-halo-width": 1,
        },
        minzoom: 4,
      });
      break;

    case "nuclear":
      map.addLayer({
        id: "nuclear-markers",
        type: "circle",
        source: "nuclear",
        layout: { visibility: vis },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 3, 6, 5, 10, 7],
          "circle-color": [
            "match", ["get", "status"],
            "Operating",        "#facc15",
            "Under Construction", "#fb923c",
            "Planned",          "#a3e635",
            "Shutdown",         "#6b7280",
            "#facc15",
          ],
          "circle-opacity": 0.85,
          "circle-stroke-width": 1.5,
          "circle-stroke-color": [
            "match", ["get", "status"],
            "Operating",        "rgba(250,204,21,0.4)",
            "Under Construction", "rgba(251,146,60,0.4)",
            "Planned",          "rgba(163,230,53,0.4)",
            "Shutdown",         "rgba(107,114,128,0.3)",
            "rgba(250,204,21,0.4)",
          ],
        },
      });
      map.addLayer({
        id: "nuclear-labels",
        type: "symbol",
        source: "nuclear",
        layout: {
          visibility: vis,
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": 10,
          "text-offset": [0, 1.4],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#fde68a",
          "text-halo-color": "rgba(17,18,23,0.8)",
          "text-halo-width": 1,
        },
        minzoom: 4,
      });
      break;

    case "eez":
      map.addLayer({
        id: "eez-lines",
        type: "line",
        source: "eez",
        layout: { visibility: vis },
        paint: {
          "line-color": "#38bdf8",
          "line-width": ["interpolate", ["linear"], ["zoom"], 2, 1, 6, 2, 10, 3],
          "line-opacity": 0.45,
          "line-dasharray": [4, 2],
        },
      });
      break;

    case "spaceports":
      map.addLayer({
        id: "spaceports-markers",
        type: "circle",
        source: "spaceports",
        layout: { visibility: vis },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 4, 6, 6, 10, 8],
          "circle-color": [
            "match", ["get", "status"],
            "Active",   "#ec4899",
            "Inactive", "#6b7280",
            "#ec4899",
          ],
          "circle-opacity": 0.85,
          "circle-stroke-width": 2,
          "circle-stroke-color": [
            "match", ["get", "status"],
            "Active",   "rgba(236,72,153,0.4)",
            "Inactive", "rgba(107,114,128,0.3)",
            "rgba(236,72,153,0.4)",
          ],
        },
      });
      map.addLayer({
        id: "spaceports-labels",
        type: "symbol",
        source: "spaceports",
        layout: {
          visibility: vis,
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": 10,
          "text-offset": [0, 1.4],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#f9a8d4",
          "text-halo-color": "rgba(17,18,23,0.8)",
          "text-halo-width": 1,
        },
        minzoom: 3,
      });
      break;

    case "chokepoints":
      map.addLayer({
        id: "chokepoints-markers",
        type: "circle",
        source: "chokepoints",
        layout: { visibility: vis },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 5, 6, 8, 10, 12],
          "circle-color": "#f59e0b",
          "circle-opacity": 0.9,
          "circle-stroke-width": 2,
          "circle-stroke-color": "rgba(245,158,11,0.35)",
        },
      });
      map.addLayer({
        id: "chokepoints-labels",
        type: "symbol",
        source: "chokepoints",
        layout: {
          visibility: vis,
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": 11,
          "text-offset": [0, 1.6],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#fcd34d",
          "text-halo-color": "rgba(17,18,23,0.85)",
          "text-halo-width": 1.5,
        },
        minzoom: 3,
      });
      break;

    case "disputed":
      map.addLayer({
        id: "disputed-fill",
        type: "fill",
        source: "disputed",
        layout: { visibility: vis },
        paint: {
          "fill-color": [
            "match", ["get", "type"],
            "Occupied",  "rgba(239,68,68,0.18)",
            "Disputed",  "rgba(251,146,60,0.15)",
            "Breakaway", "rgba(168,85,247,0.15)",
            "Claimed",   "rgba(56,189,248,0.12)",
            "rgba(251,146,60,0.12)",
          ],
          "fill-opacity": 0.7,
        },
      });
      map.addLayer({
        id: "disputed-outline",
        type: "line",
        source: "disputed",
        layout: { visibility: vis },
        paint: {
          "line-color": [
            "match", ["get", "type"],
            "Occupied",  "#ef4444",
            "Disputed",  "#fb923c",
            "Breakaway", "#a855f7",
            "Claimed",   "#38bdf8",
            "#fb923c",
          ],
          "line-width": ["interpolate", ["linear"], ["zoom"], 2, 1, 6, 1.5, 10, 2],
          "line-opacity": 0.7,
          "line-dasharray": [3, 2],
        },
      });
      map.addLayer({
        id: "disputed-labels",
        type: "symbol",
        source: "disputed",
        layout: {
          visibility: vis,
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": 11,
          "text-optional": true,
        },
        paint: {
          "text-color": "#fca5a5",
          "text-halo-color": "rgba(17,18,23,0.85)",
          "text-halo-width": 1.5,
        },
        minzoom: 4,
      });
      break;

    case "powerplants":
      map.addLayer({
        id: "powerplants-markers",
        type: "circle",
        source: "powerplants",
        layout: { visibility: vis },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 2, 6, 4, 10, 6],
          "circle-color": [
            "match", ["get", "fuelType"],
            "Coal",        "#78716c",
            "Gas",         "#60a5fa",
            "Hydro",       "#22d3ee",
            "Nuclear",     "#facc15",
            "Oil",         "#f97316",
            "Wind",        "#34d399",
            "Solar",       "#fbbf24",
            "Geothermal",  "#f472b6",
            "Biomass",     "#a3e635",
            "#94a3b8",
          ],
          "circle-opacity": 0.8,
          "circle-stroke-width": 1,
          "circle-stroke-color": "rgba(255,255,255,0.2)",
        },
      });
      map.addLayer({
        id: "powerplants-labels",
        type: "symbol",
        source: "powerplants",
        layout: {
          visibility: vis,
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": 10,
          "text-offset": [0, 1.4],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#cbd5e1",
          "text-halo-color": "rgba(17,18,23,0.8)",
          "text-halo-width": 1,
        },
        minzoom: 5,
      });
      break;

    case "cable-landings":
      map.addLayer({
        id: "cable-landings-markers",
        type: "circle",
        source: "cable-landings",
        layout: { visibility: vis },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 2, 6, 4, 10, 6],
          "circle-color": "#818cf8",
          "circle-opacity": 0.85,
          "circle-stroke-width": 1.5,
          "circle-stroke-color": "rgba(129,140,248,0.3)",
        },
      });
      map.addLayer({
        id: "cable-landings-labels",
        type: "symbol",
        source: "cable-landings",
        layout: {
          visibility: vis,
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": 10,
          "text-offset": [0, 1.4],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#a5b4fc",
          "text-halo-color": "rgba(17,18,23,0.8)",
          "text-halo-width": 1,
        },
        minzoom: 5,
      });
      break;

    case "volcanoes":
      map.addLayer({
        id: "volcanoes-markers",
        type: "circle",
        source: "volcanoes",
        layout: { visibility: vis },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 3, 6, 5, 10, 7],
          "circle-color": [
            "match", ["get", "status"],
            "Active",     "#ef4444",
            "Historical", "#fb923c",
            "Holocene",   "#f97316",
            "#ef4444",
          ],
          "circle-opacity": 0.85,
          "circle-stroke-width": 1.5,
          "circle-stroke-color": [
            "match", ["get", "status"],
            "Active",     "rgba(239,68,68,0.35)",
            "Historical", "rgba(251,146,60,0.3)",
            "Holocene",   "rgba(249,115,22,0.3)",
            "rgba(239,68,68,0.3)",
          ],
        },
      });
      map.addLayer({
        id: "volcanoes-labels",
        type: "symbol",
        source: "volcanoes",
        layout: {
          visibility: vis,
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": 10,
          "text-offset": [0, 1.4],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#fca5a5",
          "text-halo-color": "rgba(17,18,23,0.8)",
          "text-halo-width": 1,
        },
        minzoom: 4,
      });
      break;

    case "refugee-camps":
      map.addLayer({
        id: "refugee-camps-markers",
        type: "circle",
        source: "refugee-camps",
        layout: { visibility: vis },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 3, 6, 5, 10, 7],
          "circle-color": "#f472b6",
          "circle-opacity": 0.85,
          "circle-stroke-width": 1.5,
          "circle-stroke-color": "rgba(244,114,182,0.3)",
        },
      });
      map.addLayer({
        id: "refugee-camps-labels",
        type: "symbol",
        source: "refugee-camps",
        layout: {
          visibility: vis,
          "text-field": ["get", "name"],
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
          "text-size": 10,
          "text-offset": [0, 1.4],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#f9a8d4",
          "text-halo-color": "rgba(17,18,23,0.8)",
          "text-halo-width": 1,
        },
        minzoom: 4,
      });
      break;
  }
}

/**
 * Build HTML tooltip content for an overlay feature.
 */
export function buildOverlayTooltip(overlayId, properties) {
  const name = properties.name || properties.operator || "Unknown";
  const rows = [];

  switch (overlayId) {
    case "bases":
      if (properties.branch) rows.push(["Branch", properties.branch]);
      if (properties.type) rows.push(["Type", properties.type]);
      if (properties.country) rows.push(["Country", properties.country]);
      break;
    case "embassies":
      if (properties.operator) rows.push(["Operator", properties.operator]);
      if (properties.country) rows.push(["Host country", properties.country]);
      if (properties.operatorCode) rows.push(["Code", properties.operatorCode]);
      break;
    case "airports":
      if (properties.type) rows.push(["Type", properties.type]);
      if (properties.country) rows.push(["Country", properties.country]);
      break;
    case "ports":
      if (properties.harborSize) rows.push(["Size", properties.harborSize]);
      if (properties.harborType) rows.push(["Type", properties.harborType]);
      if (properties.country) rows.push(["Country", properties.country]);
      break;
    case "pipelines":
      if (properties.substance) rows.push(["Substance", properties.substance]);
      break;
    case "cables":
      break;
    case "nuclear":
      if (properties.status) rows.push(["Status", properties.status]);
      if (properties.type) rows.push(["Reactor", properties.type]);
      if (properties.capacity_mw) rows.push(["Capacity", `${properties.capacity_mw} MW`]);
      if (properties.country) rows.push(["Country", properties.country]);
      break;
    case "spaceports":
      if (properties.status) rows.push(["Status", properties.status]);
      if (properties.country) rows.push(["Country", properties.country]);
      break;
    case "chokepoints":
      if (properties.region) rows.push(["Region", properties.region]);
      if (properties.dailyVessels) rows.push(["Daily traffic", properties.dailyVessels]);
      if (properties.significance) rows.push(["Significance", properties.significance]);
      break;
    case "disputed":
      if (properties.claimants) rows.push(["Claimants", properties.claimants]);
      if (properties.type) rows.push(["Type", properties.type]);
      if (properties.status) rows.push(["Status", properties.status]);
      break;
    case "powerplants":
      if (properties.fuelType) rows.push(["Fuel", properties.fuelType]);
      if (properties.capacityMw) rows.push(["Capacity", `${properties.capacityMw} MW`]);
      if (properties.status) rows.push(["Status", properties.status]);
      if (properties.country) rows.push(["Country", properties.country]);
      break;
    case "cable-landings":
      if (properties.country) rows.push(["Country", properties.country]);
      if (properties.region) rows.push(["Region", properties.region]);
      break;
    case "volcanoes":
      if (properties.type) rows.push(["Type", properties.type]);
      if (properties.status) rows.push(["Status", properties.status]);
      if (properties.elevation) rows.push(["Elevation", `${properties.elevation} m`]);
      if (properties.country) rows.push(["Country", properties.country]);
      break;
    case "refugee-camps":
      if (properties.type) rows.push(["Type", properties.type]);
      if (properties.population) rows.push(["Population", Number(properties.population).toLocaleString()]);
      if (properties.crisis) rows.push(["Crisis", properties.crisis]);
      if (properties.country) rows.push(["Country", properties.country]);
      break;
  }

  const label = OVERLAY_REGISTRY.find((o) => o.id === overlayId)?.label || overlayId;
  const rowsHtml = rows.map(([k, v]) =>
    `<div style="display:flex;justify-content:space-between;gap:12px"><span style="color:#8a9db5">${k}</span><span>${v}</span></div>`
  ).join("");

  return `<div style="font-family:'SF Mono','IBM Plex Mono',monospace;font-size:11px;line-height:1.5;min-width:160px">` +
    `<div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:#78d6ff;margin-bottom:4px">${label}</div>` +
    `<div style="font-size:12px;font-weight:600;color:#f0f4fb;margin-bottom:6px">${name}</div>` +
    rowsHtml +
    `</div>`;
}

/**
 * Returns the primary interactive layer ID for an overlay (for hover events).
 */
export function getOverlayInteractiveLayerId(overlayId) {
  const entry = OVERLAY_REGISTRY.find((o) => o.id === overlayId);
  if (!entry) return null;
  if (entry.layerType === "line") return `${overlayId}-lines`;
  if (entry.layerType === "polygon") return `${overlayId}-fill`;
  return `${overlayId}-markers`;
}

/**
 * Returns all MapLibre layer IDs associated with an overlay.
 */
export function getOverlayLayerIds(overlayId) {
  const entry = OVERLAY_REGISTRY.find((o) => o.id === overlayId);
  if (!entry) return [];

  if (entry.layerType === "polygon") {
    return [`${overlayId}-fill`, `${overlayId}-outline`, `${overlayId}-labels`];
  }
  if (entry.layerType === "line" && overlayId !== "eez") {
    return [`${overlayId}-lines`, `${overlayId}-labels`];
  }
  if (overlayId === "eez") {
    return ["eez-lines"];
  }
  return [`${overlayId}-markers`, `${overlayId}-labels`];
}

/**
 * Toggle visibility of all layers belonging to an overlay.
 */
export function setOverlayVisibility(map, overlayId, visible) {
  const vis = visible ? "visible" : "none";
  for (const layerId of getOverlayLayerIds(overlayId)) {
    if (map.getLayer(layerId)) {
      map.setLayoutProperty(layerId, "visibility", vis);
    }
  }
}
