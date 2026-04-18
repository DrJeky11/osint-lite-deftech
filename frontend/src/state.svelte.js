import { dataset as staticDataset } from "./generated/osint-data.js";
import { computeLocationScores, DEFAULT_SCORING_CONFIG } from "./lib/scoring.js";

const SCRAPER_STORAGE_KEY = "sa-scraper-config";
const WGI_STORAGE_KEY = "sa-wgi-url";

function _readScraperUrl() {
  return typeof localStorage !== 'undefined'
    ? (localStorage.getItem(SCRAPER_STORAGE_KEY) || "http://localhost:8000")
    : "http://localhost:8000";
}

function _readWgiUrl() {
  return typeof localStorage !== 'undefined'
    ? (localStorage.getItem(WGI_STORAGE_KEY) || "http://localhost:8001")
    : "http://localhost:8001";
}

/** Reactive scraper URL state. Use scraperUrl.value to read. */
export const scraperUrl = $state({ value: _readScraperUrl() });

/** Reactive WGI service URL state. Use wgiUrl.value to read. */
export const wgiUrl = $state({ value: _readWgiUrl() });

/** Call after the admin page saves a new scraper URL to localStorage. */
export function syncScraperUrl() {
  scraperUrl.value = _readScraperUrl();
}

/** Call after the admin page saves a new WGI URL to localStorage. */
export function syncWgiUrl() {
  wgiUrl.value = _readWgiUrl();
}

export const dataset = $state({ ...staticDataset });

export const scoringConfig = $state({ ...DEFAULT_SCORING_CONFIG });

/**
 * Re-fetch the full dataset from the backend and update global state.
 * Can be called after an admin refresh to push fresh data to the whole app.
 * Optionally accepts a pre-fetched dataset object to skip the network call.
 */
export async function refreshDataset(prefetched) {
  try {
    if (prefetched) {
      Object.assign(dataset, prefetched);
      return;
    }
    const res = await fetch(scraperUrl.value + "/dataset", { signal: AbortSignal.timeout(10000) });
    if (res.ok) {
      const live = await res.json();
      if (live) Object.assign(dataset, live);
    }
  } catch { /* ignore — stale data is better than crashing */ }
}

// Try to fetch live data and scoring config from backend on load
if (typeof window !== 'undefined') {
  fetch(scraperUrl.value + "/dataset", { signal: AbortSignal.timeout(5000) })
    .then(res => res.ok ? res.json() : null)
    .then(live => {
      if (live && live.signalEvents?.length) {
        Object.assign(dataset, live);
      }
    })
    .catch(() => {});

  fetch(scraperUrl.value + "/config/scoring", { signal: AbortSignal.timeout(5000) })
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
  heatmapEnabled: false
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
