const COUNTRY_TYPE = "country";

export const GAZETTEER = [
  {
    id: "sudan",
    name: "Sudan",
    aliases: ["Republic of the Sudan"],
    country: "Sudan",
    lat: 15.5007,
    lon: 32.5599,
    resolution: COUNTRY_TYPE
  },
  {
    id: "khartoum",
    name: "Khartoum",
    aliases: ["Khartoum State"],
    country: "Sudan",
    lat: 15.5007,
    lon: 32.5599,
    resolution: "city"
  },
  {
    id: "myanmar",
    name: "Myanmar",
    aliases: ["Burma"],
    country: "Myanmar",
    lat: 21.9162,
    lon: 95.956,
    resolution: COUNTRY_TYPE
  },
  {
    id: "yangon",
    name: "Yangon",
    aliases: ["Rangoon"],
    country: "Myanmar",
    lat: 16.8661,
    lon: 96.1951,
    resolution: "city"
  },
  {
    id: "pakistan",
    name: "Pakistan",
    aliases: ["Islamic Republic of Pakistan"],
    country: "Pakistan",
    lat: 30.3753,
    lon: 69.3451,
    resolution: COUNTRY_TYPE
  },
  {
    id: "quetta",
    name: "Quetta",
    aliases: ["Balochistan capital"],
    country: "Pakistan",
    lat: 30.1798,
    lon: 66.975,
    resolution: "city"
  },
  {
    id: "venezuela",
    name: "Venezuela",
    aliases: ["Bolivarian Republic of Venezuela"],
    country: "Venezuela",
    lat: 6.4238,
    lon: -66.5897,
    resolution: COUNTRY_TYPE
  },
  {
    id: "caracas",
    name: "Caracas",
    aliases: ["Distrito Capital"],
    country: "Venezuela",
    lat: 10.4806,
    lon: -66.9036,
    resolution: "city"
  },
  {
    id: "haiti",
    name: "Haiti",
    aliases: ["Republic of Haiti"],
    country: "Haiti",
    lat: 18.9712,
    lon: -72.2852,
    resolution: COUNTRY_TYPE
  },
  {
    id: "port-au-prince",
    name: "Port-au-Prince",
    aliases: ["Port au Prince", "PaP"],
    country: "Haiti",
    lat: 18.5944,
    lon: -72.3074,
    resolution: "city"
  },
  {
    id: "ecuador",
    name: "Ecuador",
    aliases: ["Republic of Ecuador"],
    country: "Ecuador",
    lat: -1.8312,
    lon: -78.1834,
    resolution: COUNTRY_TYPE
  },
  {
    id: "guayaquil",
    name: "Guayaquil",
    aliases: [],
    country: "Ecuador",
    lat: -2.1709,
    lon: -79.9224,
    resolution: "city"
  },
  {
    id: "nigeria",
    name: "Nigeria",
    aliases: ["Federal Republic of Nigeria"],
    country: "Nigeria",
    lat: 9.082,
    lon: 8.6753,
    resolution: COUNTRY_TYPE
  },
  {
    id: "abuja",
    name: "Abuja",
    aliases: [],
    country: "Nigeria",
    lat: 9.0765,
    lon: 7.3986,
    resolution: "city"
  },
  {
    id: "libya",
    name: "Libya",
    aliases: ["State of Libya"],
    country: "Libya",
    lat: 26.3351,
    lon: 17.2283,
    resolution: COUNTRY_TYPE
  },
  {
    id: "tripoli-ly",
    name: "Tripoli",
    aliases: ["Tarabulus"],
    country: "Libya",
    lat: 32.8872,
    lon: 13.1913,
    resolution: "city"
  },
  {
    id: "lebanon",
    name: "Lebanon",
    aliases: ["Lebanese Republic"],
    country: "Lebanon",
    lat: 33.8547,
    lon: 35.8623,
    resolution: COUNTRY_TYPE
  },
  {
    id: "tripoli-lb",
    name: "Tripoli",
    aliases: ["Trablous"],
    country: "Lebanon",
    lat: 34.4367,
    lon: 35.8497,
    resolution: "city"
  }
];

export const LANDMASSES = [
  {
    id: "north-america",
    points: [
      [-168, 72], [-148, 69], [-130, 57], [-126, 49], [-117, 32], [-110, 23],
      [-98, 18], [-88, 20], [-83, 24], [-78, 31], [-72, 42], [-60, 50],
      [-50, 58], [-55, 66], [-88, 80], [-120, 79], [-150, 74]
    ]
  },
  {
    id: "south-america",
    points: [
      [-81, 12], [-78, 2], [-75, -7], [-73, -16], [-69, -24], [-63, -33],
      [-58, -43], [-54, -52], [-46, -55], [-39, -40], [-34, -17], [-35, 2],
      [-46, 9], [-61, 10], [-73, 11]
    ]
  },
  {
    id: "eurasia-west",
    points: [
      [-10, 72], [12, 72], [28, 64], [38, 57], [36, 44], [30, 32], [17, 31],
      [5, 36], [-7, 45], [-12, 56]
    ]
  },
  {
    id: "africa",
    points: [
      [-17, 34], [-6, 36], [13, 34], [24, 32], [34, 30], [41, 12], [45, 4],
      [42, -12], [33, -22], [22, -34], [11, -35], [3, -30], [-8, -1], [-15, 13]
    ]
  },
  {
    id: "asia",
    points: [
      [30, 74], [56, 72], [82, 70], [106, 63], [130, 54], [146, 48], [154, 34],
      [140, 20], [120, 8], [104, 1], [95, 6], [82, 20], [72, 28], [62, 32],
      [48, 34], [38, 40], [32, 52]
    ]
  },
  {
    id: "australia",
    points: [
      [112, -11], [129, -10], [143, -18], [154, -28], [151, -39], [137, -43],
      [121, -35], [113, -24]
    ]
  },
  {
    id: "greenland",
    points: [
      [-54, 82], [-42, 77], [-33, 69], [-40, 61], [-50, 59], [-61, 65], [-60, 76]
    ]
  }
];

function normalizeText(value = "") {
  return value.toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu, " ");
}

function unique(values) {
  return [...new Set(values)];
}

export function extractPlaceMentions(text = "") {
  const normalized = normalizeText(text);

  return GAZETTEER.filter((entry) => {
    return [entry.name, ...entry.aliases].some((variant) => {
      const normalizedVariant = normalizeText(variant).trim();
      return normalizedVariant && normalized.includes(normalizedVariant);
    });
  }).map((entry) => entry.id);
}

function scoreEntry(entry, context) {
  let score = 0;
  const reasons = [];
  const normalizedText = normalizeText(`${context.title} ${context.rawText}`);
  const normalizedProfile = normalizeText(context.profileLocation);
  const hints = normalizeText(context.placeHints.join(" "));
  const countries = unique(
    extractPlaceMentions(`${context.title} ${context.rawText} ${context.placeHints.join(" ")}`)
      .map((id) => GAZETTEER.find((candidate) => candidate.id === id))
      .filter(Boolean)
      .map((candidate) => candidate.country)
  );

  const exactMention = [entry.name, ...entry.aliases].some((variant) => {
    return normalizedText.includes(normalizeText(variant).trim());
  });

  if (exactMention) {
    score += entry.resolution === COUNTRY_TYPE ? 0.3 : 0.44;
    reasons.push("mentioned in source text");
  }

  if (hints && hints.includes(normalizeText(entry.name))) {
    score += entry.resolution === COUNTRY_TYPE ? 0.34 : 0.52;
    reasons.push("provided in place hint");
  }

  if (normalizedProfile && normalizedProfile.includes(normalizeText(entry.name))) {
    score += 0.16;
    reasons.push("matches profile location");
  }

  if (countries.includes(entry.country) && entry.resolution !== COUNTRY_TYPE) {
    score += 0.18;
    reasons.push("country context supports subnational match");
  }

  if (normalizedText.includes(normalizeText(entry.country))) {
    score += 0.14;
    reasons.push("country named explicitly");
  }

  return { score, reasons };
}

function countryFallback(countryName) {
  return GAZETTEER.find((entry) => {
    return entry.country === countryName && entry.resolution === COUNTRY_TYPE;
  });
}

export function inferGeo(sourceItem) {
  const context = {
    title: sourceItem.title ?? "",
    rawText: sourceItem.rawText ?? "",
    profileLocation: sourceItem.author?.profileLocation ?? "",
    placeHints: sourceItem.placeHints ?? []
  };

  const candidates = GAZETTEER.map((entry) => ({
    entry,
    ...scoreEntry(entry, context)
  }))
    .filter((candidate) => candidate.score > 0)
    .sort((left, right) => right.score - left.score);

  if (!candidates.length) {
    return {
      locationId: "unknown",
      name: "Unknown",
      lat: 0,
      lon: 0,
      resolution: COUNTRY_TYPE,
      confidence: 0.18,
      justification: "No reliable place evidence found."
    };
  }

  const best = candidates[0];
  const runnerUp = candidates[1];
  const confidence = Math.min(
    0.96,
    Math.max(
      0.2,
      best.score - (runnerUp ? runnerUp.score * 0.18 : 0) + (best.entry.resolution === "city" ? 0.08 : 0)
    )
  );

  if (
    runnerUp &&
    best.entry.name === runnerUp.entry.name &&
    best.entry.country !== runnerUp.entry.country &&
    confidence < 0.75
  ) {
    const sameCountry = extractPlaceMentions(`${context.title} ${context.rawText}`).some((id) => {
      const mention = GAZETTEER.find((entry) => entry.id === id);
      return mention && mention.country === best.entry.country && mention.resolution === COUNTRY_TYPE;
    });

    if (!sameCountry) {
      return {
        locationId: best.entry.country.toLowerCase(),
        name: best.entry.country,
        lat: countryFallback(best.entry.country)?.lat ?? best.entry.lat,
        lon: countryFallback(best.entry.country)?.lon ?? best.entry.lon,
        resolution: COUNTRY_TYPE,
        confidence: 0.52,
        justification: "Ambiguous city name; rolled up to country because country context was weak."
      };
    }
  }

  if (best.entry.resolution === "city" && confidence < 0.6) {
    const fallback = countryFallback(best.entry.country);

    if (fallback) {
      return {
        locationId: fallback.id,
        name: fallback.name,
        lat: fallback.lat,
        lon: fallback.lon,
        resolution: COUNTRY_TYPE,
        confidence,
        justification: "Low-confidence geolocation; rolled up to country level."
      };
    }
  }

  return {
    locationId: best.entry.id,
    name: best.entry.name,
    lat: best.entry.lat,
    lon: best.entry.lon,
    country: best.entry.country,
    resolution: best.entry.resolution,
    confidence,
    justification: unique(best.reasons).join(", ") || "Resolved from source metadata."
  };
}

export function projectOrthographic(lon, lat, rotation, radius) {
  const lambda = ((lon + rotation.lon) * Math.PI) / 180;
  const phi = (lat * Math.PI) / 180;
  const phi0 = (rotation.lat * Math.PI) / 180;
  const x = radius * Math.cos(phi) * Math.sin(lambda);
  const y =
    radius *
    (Math.cos(phi0) * Math.sin(phi) - Math.sin(phi0) * Math.cos(phi) * Math.cos(lambda));
  const visible = Math.sin(phi0) * Math.sin(phi) + Math.cos(phi0) * Math.cos(phi) * Math.cos(lambda) > 0;

  return { x, y, visible };
}

export function projectEquirectangular(lon, lat, width, height) {
  return {
    x: ((lon + 180) / 360) * width,
    y: ((90 - lat) / 180) * height,
    visible: true
  };
}
