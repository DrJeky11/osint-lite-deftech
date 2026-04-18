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
  const components = [
    { name: "War", value: score.warComponent ?? 0 },
    { name: "Military", value: score.militaryComponent ?? 0 },
    { name: "Civil", value: score.civilComponent ?? 0 },
    { name: "Terrorism", value: score.terrorismComponent ?? 0 },
    { name: "Humanitarian", value: score.humanitarianComponent ?? 0 },
    { name: "Infowar", value: score.infowarComponent ?? 0 },
  ];
  components.sort((a, b) => b.value - a.value);
  const top = components[0];
  const dominant = top.value > (components[1]?.value ?? 0) + 8
    ? `${top.name}-led`
    : "Mixed";

  return `${dominant} pressure profile with ${score.evidenceBundle.length} corroborating items in the current ${timeWindowHours}h watch window at ${Math.round(score.confidence * 100)}% geo confidence.`;
}

export function recommendedActions(score) {
  const actions = [];

  const components = [
    { key: "war", value: score.warComponent ?? 0 },
    { key: "military", value: score.militaryComponent ?? 0 },
    { key: "civil", value: score.civilComponent ?? 0 },
    { key: "terrorism", value: score.terrorismComponent ?? 0 },
    { key: "humanitarian", value: score.humanitarianComponent ?? 0 },
    { key: "infowar", value: score.infowarComponent ?? 0 },
  ];
  components.sort((a, b) => b.value - a.value);
  const dominant = components[0].key;

  if (dominant === "war") {
    actions.push("Cross-reference casualty and damage reports against satellite imagery and NOTAM advisories.");
    actions.push("Monitor ceasefire or escalation indicators across official military communiques.");
  } else if (dominant === "military") {
    actions.push("Review recent reporting on force posture, officer churn, and command changes in nearby garrisons.");
    actions.push("Cross-check convoy and deployment mentions against satellite, NOTAM, or transport disruption signals.");
  } else if (dominant === "civil") {
    actions.push("Expand collection on protest organizers, strike calls, and security-force response in adjacent districts.");
    actions.push("Look for linked local radio, civic channels, and municipal feeds to confirm whether unrest is spreading.");
  } else if (dominant === "terrorism") {
    actions.push("Check for claim-of-responsibility statements and known threat-group signatures in recent communications.");
    actions.push("Monitor border crossings, transport hubs, and security alerts for follow-on attack indicators.");
  } else if (dominant === "humanitarian") {
    actions.push("Assess displacement corridors and cross-reference with NGO situation reports and UN OCHA flash updates.");
    actions.push("Monitor food security indicators, medical supply chain disruptions, and relief access constraints.");
  } else {
    actions.push("Sample high-velocity social accounts for coordination patterns and repeated narrative frames.");
    actions.push("Cross-reference trending claims against verified source material and official statements.");
  }

  if (score.sourceBreakdown?.includes("x") || score.sourceBreakdown?.includes("bluesky")) {
    actions.push("Sample high-velocity social accounts for coordination patterns and repeated narrative frames.");
  }

  return actions.slice(0, 3);
}
