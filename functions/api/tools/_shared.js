import locations from "../../../frontend/src/generated/location-scores.json";
import events from "../../../frontend/src/generated/signal-events.json";

export const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,POST,OPTIONS",
  "access-control-allow-headers": "content-type,authorization",
};

export const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...CORS },
  });

export const preflight = () => new Response(null, { status: 204, headers: CORS });

export const allLocations = () => locations;
export const allEvents = () => events;

const norm = (s) => (s || "").toString().trim().toLowerCase();

export function findLocation(query) {
  const q = norm(query);
  if (!q) return null;
  return (
    locations.find((l) => norm(l.id) === q) ||
    locations.find((l) => norm(l.name) === q) ||
    locations.find((l) => norm(l.name).includes(q) || q.includes(norm(l.name))) ||
    null
  );
}

export function eventsWithinHours(hours) {
  const cutoff = Date.now() - hours * 3600 * 1000;
  return events.filter((e) => {
    const t = Date.parse(e.timestamp || "");
    return Number.isFinite(t) && t >= cutoff;
  });
}

export function briefLocation(loc) {
  if (!loc) return null;
  return {
    id: loc.id,
    name: loc.name,
    heat: loc.heat,
    trend: loc.trend,
    delta_pct: loc.delta,
    confidence: loc.confidence,
    civil_component: loc.civilComponent,
    military_component: loc.militaryComponent,
    top_drivers: loc.topDrivers,
    source_breakdown: loc.sourceBreakdown,
    evidence: (loc.evidenceBundle || []).slice(0, 3).map((e) => ({
      title: e.title,
      excerpt: e.excerpt,
      url: e.url,
      source: e.sourceName,
      timestamp: e.timestamp,
      signal_type: e.classification?.signalType,
      drivers: e.classification?.drivers,
    })),
  };
}
