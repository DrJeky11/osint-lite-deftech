import { json, preflight, findLocation, briefLocation } from "./_shared.js";

export const onRequestOptions = () => preflight();

export async function onRequest({ request }) {
  const url = new URL(request.url);
  let location = url.searchParams.get("location");
  if (!location && request.method === "POST") {
    try {
      const body = await request.json();
      location = body.location;
    } catch {}
  }
  if (!location) return json({ error: "missing 'location' parameter" }, 400);

  const loc = findLocation(location);
  if (!loc) return json({ error: `no hotspot found for '${location}'`, query: location }, 404);

  return json({ query: location, hotspot: briefLocation(loc) });
}
