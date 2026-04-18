const WGI_DIMENSIONS = [
  { key: 'voiceAccountability', endpoint: '/voice-accountability', label: 'Voice & Accountability' },
  { key: 'politicalStability', endpoint: '/political-stability', label: 'Political Stability' },
  { key: 'governmentEffectiveness', endpoint: '/government-effectiveness', label: 'Gov. Effectiveness' },
  { key: 'regulatoryQuality', endpoint: '/regulatory-quality', label: 'Regulatory Quality' },
  { key: 'ruleOfLaw', endpoint: '/rule-of-law', label: 'Rule of Law' },
  { key: 'controlOfCorruption', endpoint: '/control-of-corruption', label: 'Control of Corruption' },
];

const CACHE_TTL = 600000; // 10 minutes
const cache = new Map();
const inflight = new Map();

export async function fetchWgiForCountry(country, baseUrl) {
  // Check cache with TTL
  if (cache.has(country)) {
    const entry = cache.get(country);
    if (Date.now() - entry.ts < CACHE_TTL) return entry.data;
    cache.delete(country);
  }

  // Deduplicate in-flight requests for the same country
  if (inflight.has(country)) return inflight.get(country);

  const promise = _doFetch(country, baseUrl);
  inflight.set(country, promise);
  promise.finally(() => inflight.delete(country));
  return promise;
}

async function _doFetch(country, baseUrl) {
  let timedOut = false;

  const results = await Promise.allSettled(
    WGI_DIMENSIONS.map(async (dim) => {
      try {
        const res = await fetch(baseUrl + dim.endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ countries: [country], metric: 'percentile_rank' }),
          signal: AbortSignal.timeout(10000),
        });
        if (!res.ok) return null;
        const data = await res.json();
        const latest = data.results?.[0];
        return { key: dim.key, label: dim.label, value: latest?.value ?? null, year: latest?.year ?? null };
      } catch (err) {
        if (err.name === 'TimeoutError' || err.name === 'AbortError') timedOut = true;
        throw err;
      }
    })
  );

  const wgiData = {};
  for (const r of results) {
    if (r.status === 'fulfilled' && r.value) {
      wgiData[r.value.key] = r.value;
    }
  }

  if (Object.keys(wgiData).length > 0) {
    cache.set(country, { data: wgiData, ts: Date.now() });
    return wgiData;
  }

  // All dimensions failed — return error info instead of null
  if (timedOut) return { error: 'Timeout' };
  return { error: 'Service unavailable' };
}

export { WGI_DIMENSIONS };
