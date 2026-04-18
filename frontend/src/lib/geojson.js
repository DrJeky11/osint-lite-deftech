/**
 * Convert location scores and signal events into GeoJSON for MapLibre layers.
 */

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
