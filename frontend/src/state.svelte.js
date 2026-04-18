import { dataset } from "./generated/osint-data.js";
import { computeLocationScores } from "./lib/scoring.js";

export { dataset };

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
    emphasis: filters.emphasis
  }).filter((score) => score.confidence >= filters.confidenceFloor);
}

export function getSelectedScore(visibleScores) {
  return visibleScores.find((s) => s.id === selection.locationId) ?? visibleScores[0] ?? null;
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
