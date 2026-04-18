import { dataset } from "../generated/osint-data.js";

export function formatHoursAgo(timestamp) {
  const hours = Math.round(
    (new Date(dataset.generatedAt).getTime() - new Date(timestamp).getTime()) / 36e5
  );
  return `${hours}h ago`;
}

export function formatDelta(delta) {
  return `${delta > 0 ? "+" : ""}${delta.toFixed(0)}`;
}

export function selectedLabel(score) {
  return score ? score.trend : "steady";
}

export function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

export function buildDetailBrief(score, timeWindowHours) {
  const dominant = score.militaryComponent > score.civilComponent + 8
    ? "Military-led"
    : score.civilComponent > score.militaryComponent + 8
      ? "Civil-led"
      : "Mixed";

  return `${dominant} pressure profile with ${score.evidenceBundle.length} corroborating items in the current ${timeWindowHours}h watch window at ${Math.round(score.confidence * 100)}% geo confidence.`;
}

export function recommendedActions(score) {
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
