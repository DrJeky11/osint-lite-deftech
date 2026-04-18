import { json, preflight, findLocation, briefLocation } from "./_shared.js";

export const onRequestOptions = () => preflight();

export async function onRequest({ request }) {
  const url = new URL(request.url);
  let a = url.searchParams.get("a");
  let b = url.searchParams.get("b");
  if (request.method === "POST") {
    try {
      const body = await request.json();
      a = body.a ?? a;
      b = body.b ?? b;
    } catch {}
  }
  if (!a || !b) return json({ error: "missing 'a' or 'b' parameter" }, 400);

  const locA = findLocation(a);
  const locB = findLocation(b);
  if (!locA || !locB) {
    return json(
      {
        error: "one or both locations not found",
        a_found: !!locA,
        b_found: !!locB,
        query: { a, b },
      },
      404
    );
  }

  const heatDelta = (Number(locA.heat) || 0) - (Number(locB.heat) || 0);
  const hotter = heatDelta > 0 ? locA.name : heatDelta < 0 ? locB.name : "tie";

  return json({
    query: { a, b },
    verdict: {
      hotter,
      heat_difference: Math.round(heatDelta * 100) / 100,
      trend_a: locA.trend,
      trend_b: locB.trend,
    },
    a: briefLocation(locA),
    b: briefLocation(locB),
  });
}
