import { dataset as staticDataset } from "./generated/osint-data.js";
import { computeLocationScores, DEFAULT_SCORING_CONFIG } from "./lib/scoring.js";

const SCRAPER_URL = typeof localStorage !== 'undefined'
  ? (localStorage.getItem("sa-scraper-config") || "http://localhost:8000")
  : "http://localhost:8000";

export const dataset = $state({ ...staticDataset });

export const scoringConfig = $state({ ...DEFAULT_SCORING_CONFIG });

// Try to fetch live data and scoring config from backend on load
if (typeof window !== 'undefined') {
  fetch(SCRAPER_URL + "/dataset", { signal: AbortSignal.timeout(5000) })
    .then(res => res.ok ? res.json() : null)
    .then(live => {
      if (live && live.signalEvents?.length) {
        Object.assign(dataset, live);
      }
    })
    .catch(() => {});

  fetch(SCRAPER_URL + "/config/scoring", { signal: AbortSignal.timeout(5000) })
    .then(res => res.ok ? res.json() : null)
    .then(cfg => {
      if (cfg) Object.assign(scoringConfig, cfg);
    })
    .catch(() => {});
}

export const filters = $state({
  projection: "globe",
  sourceFamily: "all",
  emphasis: "blend",
  timeWindowHours: 24,
  confidenceFloor: 0.5,
  heatmapEnabled: true
});

export const selection = $state({
  locationId: null
});

export function getFilteredSignalEvents() {
  return dataset.signalEvents.filter((event) => {
    const ageHours = (new Date(dataset.generatedAt).getTime() - new Date(event.timestamp).getTime()) / 36e5;
    return (
      ageHours <= filters.timeWindowHours &&
      (filters.sourceFamily === "all" || event.sourceFamily === filters.sourceFamily) &&
      event.geo.confidence >= filters.confidenceFloor
    );
  });
}

export function getVisibleScores() {
  return computeLocationScores(getFilteredSignalEvents(), {
    referenceTime: dataset.generatedAt,
    emphasis: filters.emphasis,
    scoringConfig,
  }).filter((score) => score.confidence >= filters.confidenceFloor);
}

export function getSelectedScore(visibleScores) {
  if (!selection.locationId) return null;
  return visibleScores.find((s) => s.id === selection.locationId) ?? null;
}

export function ensureValidSelection(visibleScores) {
  if (!visibleScores.length) {
    selection.locationId = null;
    return;
  }
  const stillVisible = visibleScores.some((s) => s.id === selection.locationId);
  if (!stillVisible) {
    selection.locationId = visibleScores[0].id;
  }
}
