const DEFAULT_SCORING_CONFIG = {
  warMultiplier: 7.2,
  militaryMultiplier: 6.8,
  terrorismMultiplier: 6.6,
  civilMultiplier: 6.4,
  humanitarianMultiplier: 5.8,
  infowarMultiplier: 5.2,
  blendWeights: {
    war: 0.25,
    military: 0.20,
    civil: 0.18,
    terrorism: 0.15,
    humanitarian: 0.12,
    infowar: 0.10,
  },
  recencyDecayHours: 16,
  corroborationBoost: 0.14,
  singleSourcePenalty: 0.82,
  warmingThreshold: 8,
  coolingThreshold: -5,
  confidenceFloor: 0.12,
  confidenceCeiling: 0.97,
  confidenceBaseWeight: 0.72,
  confidenceCorrobWeight: 0.08,
  componentDisplayMax: 100,
  trendHeatFloor: 0.1,
  sparklineReferenceMax: 100,
  wgiEnabled: true,
};

export { DEFAULT_SCORING_CONFIG };

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function hoursBetween(newer, older) {
  return Math.abs(newer.getTime() - older.getTime()) / 36e5;
}

function recencyWeight(hoursAgo, decayHours) {
  return Math.exp(-hoursAgo / decayHours);
}

function unique(values) {
  return [...new Set(values)];
}

function signalEventScore(event, referenceTime, cfg) {
  const hoursAgo = hoursBetween(referenceTime, new Date(event.timestamp));
  const sourceDiversityBoost = 1 + (event.corroborationCount - 1) * cfg.corroborationBoost;
  const confidencePenalty = 1 - Math.max(event.classification.confidencePenalty, 1 - event.geo.confidence);
  const c = event.classification;

  return (
    recencyWeight(hoursAgo, cfg.recencyDecayHours) *
    event.classification.severity *
    ((c.warWeight ?? 0) + (c.militaryWeight ?? 0) + (c.civilWeight ?? 0) + (c.terrorismWeight ?? 0) + (c.humanitarianWeight ?? 0) + (c.narrativeWeight ?? 0)) *
    sourceDiversityBoost *
    confidencePenalty
  );
}

function computeHistory(events, referenceTime, cfg) {
  const windows = [36, 30, 24, 18, 12, 6].reverse();

  return windows.map((windowHours) => {
    const windowEvents = events.filter((event) => {
      return hoursBetween(referenceTime, new Date(event.timestamp)) <= windowHours;
    });
    const value = windowEvents.reduce((sum, event) => sum + signalEventScore(event, referenceTime, cfg), 0);
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

function computeTrend(recent, previous, heat, cfg) {
  // Suppress trend signals when heat is negligible — avoids false "warming"
  // badges on locations with 1-2 low-weight events and near-zero scores
  if (heat < cfg.trendHeatFloor) return "steady";
  const delta = recent - previous;
  if (delta > cfg.warmingThreshold) {
    return "warming";
  }
  if (delta < cfg.coolingThreshold) {
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
  const cfg = { ...DEFAULT_SCORING_CONFIG, ...options.scoringConfig };
  const bw = cfg.blendWeights ?? DEFAULT_SCORING_CONFIG.blendWeights;

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
      const rw = (event) => recencyWeight(hoursBetween(referenceTime, new Date(event.timestamp)), cfg.recencyDecayHours);

      const warComponent = events.reduce((sum, event) => sum + rw(event) * (event.classification.warWeight ?? 0) * cfg.warMultiplier, 0);
      const militaryComponent = events.reduce((sum, event) => sum + rw(event) * (event.classification.militaryWeight ?? 0) * cfg.militaryMultiplier, 0);
      const civilComponent = events.reduce((sum, event) => sum + rw(event) * (event.classification.civilWeight ?? 0) * cfg.civilMultiplier, 0);
      const terrorismComponent = events.reduce((sum, event) => sum + rw(event) * (event.classification.terrorismWeight ?? 0) * cfg.terrorismMultiplier, 0);
      const humanitarianComponent = events.reduce((sum, event) => sum + rw(event) * (event.classification.humanitarianWeight ?? 0) * cfg.humanitarianMultiplier, 0);
      const infowarComponent = events.reduce((sum, event) => sum + rw(event) * (event.classification.narrativeWeight ?? 0) * cfg.infowarMultiplier, 0);

      const baseHeat =
        emphasis === "war"
          ? warComponent
          : emphasis === "military"
            ? militaryComponent
            : emphasis === "civil"
              ? civilComponent
              : emphasis === "terrorism"
                ? terrorismComponent
                : emphasis === "humanitarian"
                  ? humanitarianComponent
                  : emphasis === "infowar"
                    ? infowarComponent
                    : warComponent * bw.war + militaryComponent * bw.military + civilComponent * bw.civil + terrorismComponent * bw.terrorism + humanitarianComponent * bw.humanitarian + infowarComponent * bw.infowar;

      const corroboration = unique(events.map((event) => event.sourceFamily)).length;
      const velocityRecent = events.filter((event) => hoursBetween(referenceTime, new Date(event.timestamp)) <= 12).length;
      const velocityPrevious = events.filter((event) => {
        const age = hoursBetween(referenceTime, new Date(event.timestamp));
        return age > 12 && age <= 24;
      }).length;
      const penalty = events.some((event) => event.corroborationCount < 2) && corroboration === 1 ? cfg.singleSourcePenalty : 1;
      const heat = clamp(baseHeat * (1 + corroboration * cfg.corroborationBoost) * penalty, 0, 100);
      const delta = clamp((velocityRecent - velocityPrevious) * 6 + (baseHeat > 45 ? 4 : 0), -40, 40);
      const strongestEvent = events.slice().sort((left, right) => {
        return signalEventScore(right, referenceTime, cfg) - signalEventScore(left, referenceTime, cfg);
      })[0];
      const history = computeHistory(events, referenceTime, cfg);
      const confidence =
        events.reduce((sum, event) => sum + event.geo.confidence, 0) / Math.max(events.length, 1) *
        (cfg.confidenceBaseWeight + corroboration * cfg.confidenceCorrobWeight);

      return {
        id: locationName.toLowerCase().replace(/[^\w]+/g, "-"),
        name: locationName,
        heat: Number(heat.toFixed(1)),
        delta: Number(delta.toFixed(1)),
        confidence: clamp(Number(confidence.toFixed(2)), cfg.confidenceFloor, cfg.confidenceCeiling),
        warComponent: Number(Math.max(0, warComponent).toFixed(1)),
        militaryComponent: Number(Math.max(0, militaryComponent).toFixed(1)),
        civilComponent: Number(Math.max(0, civilComponent).toFixed(1)),
        terrorismComponent: Number(Math.max(0, terrorismComponent).toFixed(1)),
        humanitarianComponent: Number(Math.max(0, humanitarianComponent).toFixed(1)),
        infowarComponent: Number(Math.max(0, infowarComponent).toFixed(1)),
        trend: computeTrend(velocityRecent * 10 + baseHeat, velocityPrevious * 10 + baseHeat * 0.6, heat, cfg),
        history,
        sourceBreakdown: dominantSourceFamilies(events),
        topDrivers: unique(events.flatMap((event) => event.classification.drivers)).slice(0, 6),
        evidenceBundle: events
          .slice()
          .sort((left, right) => new Date(right.timestamp) - new Date(left.timestamp))
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
