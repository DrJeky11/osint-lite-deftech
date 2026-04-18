import { json, preflight, eventsWithinHours } from "./_shared.js";

export const onRequestOptions = () => preflight();

export async function onRequest({ request }) {
  const url = new URL(request.url);
  let query = url.searchParams.get("query");
  let hours = parseInt(url.searchParams.get("hours") || "24", 10);
  let sourceFamily = url.searchParams.get("source_family");
  let limit = parseInt(url.searchParams.get("limit") || "10", 10);

  if (request.method === "POST") {
    try {
      const body = await request.json();
      query = body.query ?? query;
      hours = body.hours ?? hours;
      sourceFamily = body.source_family ?? sourceFamily;
      limit = body.limit ?? limit;
    } catch {}
  }
  if (!query) return json({ error: "missing 'query' parameter" }, 400);
  hours = Math.min(Math.max(hours || 24, 1), 168);
  limit = Math.min(Math.max(limit || 10, 1), 50);

  const q = query.toString().toLowerCase();
  const pool = eventsWithinHours(hours);

  const matches = pool.filter((e) => {
    if (sourceFamily && (e.sourceFamily || "").toLowerCase() !== sourceFamily.toLowerCase()) return false;
    const hay = `${e.title || ""} ${e.excerpt || ""} ${(e.classification?.drivers || []).join(" ")} ${e.displayLocationName || ""}`.toLowerCase();
    return hay.includes(q);
  });

  matches.sort((a, b) => Date.parse(b.timestamp || 0) - Date.parse(a.timestamp || 0));

  return json({
    query,
    hours,
    source_family: sourceFamily || null,
    total_matches: matches.length,
    results: matches.slice(0, limit).map((e) => ({
      title: e.title,
      excerpt: e.excerpt,
      url: e.url,
      source: e.sourceName,
      source_family: e.sourceFamily,
      timestamp: e.timestamp,
      location: e.displayLocationName || e.geo?.name,
      signal_type: e.classification?.signalType,
      drivers: e.classification?.drivers,
    })),
  });
}
