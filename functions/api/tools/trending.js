import { json, preflight, allLocations, briefLocation } from "./_shared.js";

export const onRequestOptions = () => preflight();

export async function onRequest({ request }) {
  const url = new URL(request.url);
  const topN = Math.min(Math.max(parseInt(url.searchParams.get("top_n") || "5", 10) || 5, 1), 20);
  const direction = (url.searchParams.get("direction") || "warming").toLowerCase();

  const filtered = allLocations().filter((l) => {
    if (direction === "all") return true;
    return (l.trend || "").toLowerCase() === direction;
  });

  const sorted = [...filtered].sort((a, b) => {
    const da = Number(a.delta) || 0;
    const db = Number(b.delta) || 0;
    if (db !== da) return db - da;
    return (Number(b.heat) || 0) - (Number(a.heat) || 0);
  });

  return json({
    direction,
    top_n: topN,
    hotspots: sorted.slice(0, topN).map(briefLocation),
  });
}
