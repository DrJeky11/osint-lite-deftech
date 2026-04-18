import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { inferGeo } from "../src/lib/geo.js";
import { classifySignal } from "../src/lib/signals.js";
import { buildSignalEvent, computeLocationScores } from "../src/lib/scoring.js";
import { BASE_TIME, SOURCE_ITEMS } from "../src/lib/demo-seed.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const generatedDir = path.resolve(__dirname, "../src/generated");
const rssCachePath = path.join(generatedDir, "rss-cache.json");
const blueskyCachePath = path.join(generatedDir, "bluesky-cache.json");
const referenceTime = new Date(BASE_TIME);

function materializeSourceItem(sourceItem) {
  return {
    ...sourceItem,
    publishedAt: new Date(referenceTime.getTime() - sourceItem.hoursAgo * 36e5).toISOString()
  };
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function dedupeSourceItems(items) {
  const merged = new Map();

  for (const item of items) {
    const existing = merged.get(item.id);
    if (!existing) {
      merged.set(item.id, item);
      continue;
    }

    merged.set(item.id, {
      ...existing,
      placeHints: unique([...(existing.placeHints ?? []), ...(item.placeHints ?? [])]),
      provenance: unique([existing.provenance, item.provenance]).join(" + "),
      watchRefs: [...(existing.watchRefs ?? []), ...(item.watchRefs ?? [])]
    });
  }

  return [...merged.values()];
}

function countCorroboration(materializedItems, targetItem) {
  const windowStart = new Date(new Date(targetItem.publishedAt).getTime() - 6 * 36e5);

  return materializedItems.filter((candidate) => {
    const publishedAt = new Date(candidate.publishedAt);
    const overlappingPlace = candidate.placeHints.some((hint) => targetItem.placeHints.includes(hint));
    return candidate.id !== targetItem.id && overlappingPlace && publishedAt >= windowStart;
  }).length + 1;
}

async function loadSourceItems() {
  const sourceItems = [];
  const sourceCatalog = [];
  const failures = [];
  const generatedAtCandidates = [];
  const sourceStatus = {
    rss: "missing",
    bluesky: "missing"
  };

  try {
    const raw = await readFile(rssCachePath, "utf8");
    const rssCache = JSON.parse(raw);
    const rssItems = rssCache.feeds.flatMap((feed) => feed.items);
    sourceItems.push(...rssItems);
    sourceCatalog.push(
      ...rssCache.feeds.map((feed) => ({
        id: feed.id,
        label: feed.label,
        source: feed.source,
        sourceFamily: feed.sourceFamily,
        sourceKind: "rss-feed",
        url: feed.url,
        itemCount: feed.itemCount
      }))
    );
    failures.push(...(rssCache.failures ?? []));
    if (rssCache.refreshedAt) {
      generatedAtCandidates.push(rssCache.refreshedAt);
    }
    sourceStatus.rss = rssItems.length ? "loaded" : "empty";
  } catch {
    // Ignore a missing or invalid RSS cache and continue with other sources.
  }

  try {
    const raw = await readFile(blueskyCachePath, "utf8");
    const blueskyCache = JSON.parse(raw);
    const blueskyItems = blueskyCache.watches.flatMap((watch) => watch.items);
    sourceItems.push(...blueskyItems);
    sourceCatalog.push(
      ...blueskyCache.watches.map((watch) => ({
        id: watch.id,
        label: watch.label,
        source: watch.source,
        sourceFamily: watch.sourceFamily,
        sourceKind: watch.type,
        itemCount: watch.itemCount
      }))
    );
    failures.push(...(blueskyCache.failures ?? []));
    if (blueskyCache.refreshedAt) {
      generatedAtCandidates.push(blueskyCache.refreshedAt);
    }
    sourceStatus.bluesky = blueskyItems.length ? "loaded" : (blueskyCache.failures?.length ? "failed" : "empty");
  } catch {
    // Ignore a missing or invalid Bluesky cache and continue with other sources.
  }

  if (sourceItems.length) {
    const generatedAt =
      generatedAtCandidates
        .map((value) => new Date(value))
        .filter((value) => !Number.isNaN(value.getTime()))
        .sort((left, right) => right.getTime() - left.getTime())[0]
        ?.toISOString() ?? referenceTime.toISOString();

    return {
      sourceItems: dedupeSourceItems(sourceItems),
      sourceCatalog,
      feedCatalog: sourceCatalog.filter((entry) => entry.sourceKind === "rss-feed"),
      failures,
      sourceStatus,
      generatedAt
    };
  }

  return {
    sourceItems: SOURCE_ITEMS.map(materializeSourceItem),
    sourceCatalog: [],
    feedCatalog: [],
    failures: [],
    sourceStatus,
    generatedAt: referenceTime.toISOString()
  };
}

async function main() {
  const { sourceItems, sourceCatalog, feedCatalog, failures, sourceStatus, generatedAt } = await loadSourceItems();
  const liveReferenceTime = new Date(generatedAt);
  const signalEvents = sourceItems.map((sourceItem) => {
    const geo = inferGeo(sourceItem);
    const classification = classifySignal(sourceItem);
    const corroborationCount = countCorroboration(sourceItems, sourceItem);
    return buildSignalEvent(sourceItem, geo, classification, corroborationCount);
  });
  const locationScores = computeLocationScores(signalEvents, {
    referenceTime: liveReferenceTime,
    emphasis: "blend"
  });
  const dataset = {
    generatedAt: liveReferenceTime.toISOString(),
    sourceCatalog,
    feedCatalog,
    failures,
    sourceStatus,
    sourceItems,
    signalEvents,
    locationScores
  };

  await mkdir(generatedDir, { recursive: true });
  await writeFile(
    path.join(generatedDir, "osint-data.js"),
    `export const dataset = ${JSON.stringify(dataset, null, 2)};\n`,
    "utf8"
  );
  await writeFile(path.join(generatedDir, "signal-events.json"), JSON.stringify(signalEvents, null, 2), "utf8");
  await writeFile(path.join(generatedDir, "location-scores.json"), JSON.stringify(locationScores, null, 2), "utf8");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
