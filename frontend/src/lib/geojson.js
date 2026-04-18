/**
 * Convert location scores and signal events into GeoJSON for MapLibre layers.
 */

/**
 * Map from score/gazetteer country names to the country names used in the
 * Natural Earth GeoJSON (countries.json).  Only entries that differ need to
 * be listed here — identical names are matched automatically.
 */
const COUNTRY_NAME_ALIASES = {
  "DRC":                "Democratic Republic of the Congo",
  "DR Congo":           "Democratic Republic of the Congo",
  "Dem. Rep. Congo":    "Democratic Republic of the Congo",
  "Palestine":          "West Bank",          // GeoJSON has "West Bank" polygon
  "Ivory Coast":        "Ivory Coast",
  "Côte d'Ivoire":      "Ivory Coast",
  "Burma":              "Myanmar",
  "Czech Republic":     "Czech Republic",
  "Czechia":            "Czech Republic",
  "Republic of Congo":  "Republic of the Congo",
  "Timor-Leste":        "East Timor",
  "Eswatini":           "Swaziland",
  "North Macedonia":    "Macedonia",
  "Bahamas":            "The Bahamas",
  "S. Sudan":           "South Sudan",
};

const TREND_RANK = { warming: 2, steady: 1, cooling: 0 };

/**
 * Resolve a score's country name — prefer geo.country from the evidence
 * bundle, fall back to score.name.
 */
export function resolveCountryName(score) {
  const countries = (score.evidenceBundle ?? [])
    .map((e) => e.geo?.country)
    .filter(Boolean);
  return countries[0] ?? score.name;
}

/**
 * Build a lookup from normalised country name -> GeoJSON feature index.
 * Called once when the countries source GeoJSON is loaded.
 */
function buildCountryIndex(countriesGeoJSON) {
  const index = new Map();
  for (let i = 0; i < countriesGeoJSON.features.length; i++) {
    const name = countriesGeoJSON.features[i].properties.name;
    index.set(name.toLowerCase(), i);
  }
  return index;
}

/**
 * Produce a FeatureCollection of country polygons enriched with heat/trend
 * properties derived from visible location scores.
 *
 * @param {Array} visibleScores  - output of computeLocationScores()
 * @param {Object} countriesGeoJSON - raw Natural Earth FeatureCollection
 * @returns {Object} GeoJSON FeatureCollection
 */
export function countryFillGeoJSON(visibleScores, countriesGeoJSON) {
  if (!countriesGeoJSON || !countriesGeoJSON.features) {
    return { type: "FeatureCollection", features: [] };
  }

  const index = buildCountryIndex(countriesGeoJSON);

  // Aggregate scores per country
  const countryAgg = new Map(); // normalised name -> { heat, delta, trend, featureIdx }

  for (const score of visibleScores) {
    const rawName = resolveCountryName(score);
    const canonical = COUNTRY_NAME_ALIASES[rawName] ?? rawName;
    const key = canonical.toLowerCase();
    let featureIdx = index.get(key);

    // If no direct match, try the alias table with the score.name as well
    if (featureIdx === undefined) {
      const altCanonical = COUNTRY_NAME_ALIASES[score.name] ?? score.name;
      featureIdx = index.get(altCanonical.toLowerCase());
    }

    if (featureIdx === undefined) continue;

    const existing = countryAgg.get(key);
    if (!existing) {
      countryAgg.set(key, {
        heat: score.heat,
        delta: score.delta,
        trend: score.trend,
        featureIdx,
      });
    } else {
      existing.heat = Math.max(existing.heat, score.heat);
      existing.delta += score.delta;
      if ((TREND_RANK[score.trend] ?? 0) > (TREND_RANK[existing.trend] ?? 0)) {
        existing.trend = score.trend;
      }
    }
  }

  // Include ALL countries — scored ones get their data, unscored get defaults
  const features = [];
  for (let i = 0; i < countriesGeoJSON.features.length; i++) {
    const baseFeature = countriesGeoJSON.features[i];
    const key = baseFeature.properties.name.toLowerCase();
    const agg = countryAgg.get(key);

    features.push({
      type: "Feature",
      geometry: baseFeature.geometry,
      properties: {
        id: baseFeature.properties?.id || baseFeature.id,
        name: baseFeature.properties.name,
        heat: agg ? agg.heat : 0,
        delta: agg ? Number(agg.delta.toFixed(1)) : 0,
        trend: agg ? agg.trend : "none",
        hasData: !!agg,
      },
    });
  }

  return { type: "FeatureCollection", features };
}

export function scoresToGeoJSON(visibleScores) {
  return {
    type: "FeatureCollection",
    features: visibleScores.map((score, index) => ({
      type: "Feature",
      id: index,
      geometry: {
        type: "Point",
        coordinates: [score.center.lon, score.center.lat]
      },
      properties: {
        id: score.id,
        name: score.name,
        heat: score.heat,
        delta: score.delta,
        confidence: score.confidence,
        civilComponent: score.civilComponent,
        militaryComponent: score.militaryComponent,
        trend: score.trend
      }
    }))
  };
}

export function signalEventsToGeoJSON(filteredEvents) {
  return {
    type: "FeatureCollection",
    features: filteredEvents
      .filter((event) => event.geo.lat !== 0 || event.geo.lon !== 0)
      .map((event, index) => {
        const weight =
          event.classification.severity *
          (event.classification.civilWeight + event.classification.militaryWeight);

        return {
          type: "Feature",
          id: index,
          geometry: {
            type: "Point",
            coordinates: [event.geo.lon, event.geo.lat]
          },
          properties: {
            weight: Math.min(weight / 10, 1),
            sourceFamily: event.sourceFamily,
            confidence: event.geo.confidence
          }
        };
      })
  };
}
