function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function hoursBetween(newer, older) {
  return Math.abs(newer.getTime() - older.getTime()) / 36e5;
}

function recencyWeight(hoursAgo) {
  return Math.exp(-hoursAgo / 16);
}

function unique(values) {
  return [...new Set(values)];
}

function signalEventScore(event, referenceTime) {
  const hoursAgo = hoursBetween(referenceTime, new Date(event.timestamp));
  const sourceDiversityBoost = 1 + (event.corroborationCount - 1) * 0.12;
  const confidencePenalty = 1 - Math.max(event.classification.confidencePenalty, 1 - event.geo.confidence);

  return (
    recencyWeight(hoursAgo) *
    event.classification.severity *
    (event.classification.civilWeight + event.classification.militaryWeight) *
    sourceDiversityBoost *
    confidencePenalty
  );
}

function computeHistory(events, referenceTime) {
  const windows = [36, 30, 24, 18, 12, 6].reverse();

  return windows.map((windowHours) => {
    const windowEvents = events.filter((event) => {
      return hoursBetween(referenceTime, new Date(event.timestamp)) <= windowHours;
    });
    const value = windowEvents.reduce((sum, event) => sum + signalEventScore(event, referenceTime), 0);
    return Number(value.toFixed(2));
  });
}

function dominantSourceFamilies(events) {
  return Object.entries(
    events.reduce((counts, event) => {
      counts[event.sourceFamily] = (counts[event.sourceFamily] ?? 0) + 1;
      return counts;
    }, {})
  )
    .sort((left, right) => right[1] - left[1])
    .map(([sourceFamily]) => sourceFamily);
}

function computeTrend(recent, previous) {
  const delta = recent - previous;
  if (delta > 8) {
    return "warming";
  }
  if (delta < -5) {
    return "cooling";
  }
  return "steady";
}

export function buildSignalEvent(sourceItem, geo, classification, corroborationCount = 1) {
  return {
    id: `signal-${sourceItem.id}`,
    sourceId: sourceItem.id,
    sourceFamily: sourceItem.sourceFamily,
    sourceName: sourceItem.source,
    title: sourceItem.title,
    excerpt: sourceItem.rawText,
    url: sourceItem.url,
    author: sourceItem.author,
    provenance: sourceItem.provenance,
    engagement: sourceItem.engagement ?? {},
    timestamp: sourceItem.publishedAt,
    geo,
    classification,
    corroborationCount
  };
}

export function computeLocationScores(signalEvents, options = {}) {
  const referenceTime = new Date(options.referenceTime ?? new Date());
  const emphasis = options.emphasis ?? "blend";
  const grouped = signalEvents.reduce((accumulator, event) => {
    const shouldRollUp = event.geo.resolution !== "city" || event.geo.confidence < 0.68;
    const locationKey = shouldRollUp ? (event.geo.country ?? event.geo.name) : event.geo.name;
    const existing = accumulator.get(locationKey) ?? [];
    existing.push({
      ...event,
      displayLocationName: locationKey
    });
    accumulator.set(locationKey, existing);
    return accumulator;
  }, new Map());

  return [...grouped.entries()]
    .map(([locationName, events]) => {
      const civilComponent = events.reduce((sum, event) => {
        return sum + recencyWeight(hoursBetween(referenceTime, new Date(event.timestamp))) * event.classification.civilWeight * 6.4;
      }, 0);
      const militaryComponent = events.reduce((sum, event) => {
        return sum + recencyWeight(hoursBetween(referenceTime, new Date(event.timestamp))) * event.classification.militaryWeight * 6.8;
      }, 0);
      const baseHeat =
        emphasis === "civil"
          ? civilComponent
          : emphasis === "military"
            ? militaryComponent
            : civilComponent * 0.56 + militaryComponent * 0.44;
      const corroboration = unique(events.map((event) => event.sourceFamily)).length;
      const velocityRecent = events.filter((event) => hoursBetween(referenceTime, new Date(event.timestamp)) <= 12).length;
      const velocityPrevious = events.filter((event) => {
        const age = hoursBetween(referenceTime, new Date(event.timestamp));
        return age > 12 && age <= 24;
      }).length;
      const penalty = events.some((event) => event.corroborationCount < 2) && corroboration === 1 ? 0.82 : 1;
      const heat = clamp(baseHeat * (1 + corroboration * 0.14) * penalty, 0, 100);
      const delta = clamp((velocityRecent - velocityPrevious) * 6 + (baseHeat > 45 ? 4 : 0), -40, 40);
      const strongestEvent = events.slice().sort((left, right) => {
        return signalEventScore(right, referenceTime) - signalEventScore(left, referenceTime);
      })[0];
      const history = computeHistory(events, referenceTime);
      const confidence =
        events.reduce((sum, event) => sum + event.geo.confidence, 0) / Math.max(events.length, 1) *
        (0.72 + corroboration * 0.08);

      return {
        id: locationName.toLowerCase().replace(/[^\w]+/g, "-"),
        name: locationName,
        heat: Number(heat.toFixed(1)),
        delta: Number(delta.toFixed(1)),
        confidence: clamp(Number(confidence.toFixed(2)), 0.12, 0.97),
        civilComponent: Number(clamp(civilComponent, 0, 100).toFixed(1)),
        militaryComponent: Number(clamp(militaryComponent, 0, 100).toFixed(1)),
        trend: computeTrend(velocityRecent * 10 + baseHeat, velocityPrevious * 10 + baseHeat * 0.6),
        history,
        sourceBreakdown: dominantSourceFamilies(events),
        topDrivers: unique(events.flatMap((event) => event.classification.drivers)).slice(0, 6),
        evidenceBundle: events
          .slice()
          .sort((left, right) => signalEventScore(right, referenceTime) - signalEventScore(left, referenceTime))
          .slice(0, 4),
        center: {
          lat: strongestEvent.geo.lat,
          lon: strongestEvent.geo.lon
        },
        resolution: strongestEvent.geo.resolution
      };
    })
    .sort((left, right) => right.heat - left.heat);
}
