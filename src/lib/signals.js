const TAXONOMY = {
  civil: [
    { pattern: /\bprotest|march|demonstration|strike\b/gi, weight: 1.1, driver: "protest activity" },
    { pattern: /\briot|looting|clashes|roadblock\b/gi, weight: 1.25, driver: "street-level unrest" },
    { pattern: /\bcrackdown|curfew|state of emergency|detentions\b/gi, weight: 1.35, driver: "state response escalation" },
    { pattern: /\bpolice|security forces\b/gi, weight: 0.5, driver: "security-force presence" }
  ],
  military: [
    { pattern: /\barmy|military|junta|national guard\b/gi, weight: 0.7, driver: "military actor involvement" },
    { pattern: /\bmutiny|defection|purge|dismissed officers\b/gi, weight: 1.65, driver: "force cohesion stress" },
    { pattern: /\bcoup|coup rumor|takeover\b/gi, weight: 1.75, driver: "coup-related narrative" },
    { pattern: /\btroop movement|convoy|mobilization|border deployment\b/gi, weight: 1.45, driver: "force movement" }
  ],
  narrative: [
    { pattern: /\bdisinformation|rumor|coordinated campaign|deepfake\b/gi, weight: 0.95, driver: "narrative manipulation" },
    { pattern: /\bviral|amplified|trending\b/gi, weight: 0.55, driver: "acceleration in discussion volume" },
    { pattern: /\bdehumanizing|traitor|enemy within\b/gi, weight: 0.85, driver: "destabilizing rhetoric" }
  ]
};

const NOISE_PATTERNS = /\bfootball|soccer|concert|celebrity|festival|movie premiere\b/gi;

function countMatches(text, rules) {
  return rules.reduce(
    (accumulator, rule) => {
      const matches = text.match(rule.pattern) ?? [];

      if (matches.length > 0) {
        accumulator.score += matches.length * rule.weight;
        accumulator.drivers.push(rule.driver);
      }

      return accumulator;
    },
    { score: 0, drivers: [] }
  );
}

export function classifySignal(sourceItem) {
  const text = `${sourceItem.title ?? ""} ${sourceItem.rawText ?? ""}`;

  if (NOISE_PATTERNS.test(text)) {
    return {
      signalType: "noise",
      severity: 0.2,
      civilWeight: 0.05,
      militaryWeight: 0.05,
      narrativeWeight: 0.05,
      drivers: ["non-instability chatter"],
      confidencePenalty: 0.55
    };
  }

  const civil = countMatches(text, TAXONOMY.civil);
  const military = countMatches(text, TAXONOMY.military);
  const narrative = countMatches(text, TAXONOMY.narrative);
  const allDrivers = [...civil.drivers, ...military.drivers, ...narrative.drivers];
  const peak = Math.max(civil.score, military.score, narrative.score);
  const severity = Math.min(5, 1 + peak);
  const militaryPriorityDrivers = ["force movement", "force cohesion stress", "coup-related narrative"];
  const hasMilitaryPriorityDriver = military.drivers.some((driver) => militaryPriorityDrivers.includes(driver));
  const signalType =
    military.score > civil.score || (hasMilitaryPriorityDriver && military.score >= civil.score * 0.65)
      ? "military"
      : civil.score > 0
        ? "civil"
        : "narrative";

  return {
    signalType,
    severity,
    civilWeight: Number((civil.score + narrative.score * 0.25).toFixed(2)),
    militaryWeight: Number((military.score + narrative.score * 0.35).toFixed(2)),
    narrativeWeight: Number(narrative.score.toFixed(2)),
    drivers: [...new Set(allDrivers)],
    confidencePenalty: narrative.score > 0 && civil.score === 0 && military.score === 0 ? 0.22 : 0
  };
}
