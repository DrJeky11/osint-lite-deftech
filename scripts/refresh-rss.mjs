import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { RSS_FEED_CATALOG } from "../src/lib/rss-feeds.js";
import { normalizeFeedItems, parseFeed } from "../src/lib/rss.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const generatedDir = path.resolve(__dirname, "../src/generated");

async function fetchFeed(feed) {
  try {
    const response = await fetch(feed.url, {
      headers: {
        "user-agent": "SignalAtlas/0.1 (+https://github.com/DrJeky11/osint-lite-deftech)"
      }
    });

    if (!response.ok) {
      throw new Error(`${feed.id} failed with ${response.status}`);
    }

    const xml = await response.text();
    const items = normalizeFeedItems(feed, parseFeed(xml));

    return {
      ...feed,
      fetchedAt: new Date().toISOString(),
      itemCount: items.length,
      items
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`${feed.id}: ${message}`);
  }
}

async function main() {
  const results = await Promise.allSettled(RSS_FEED_CATALOG.map(fetchFeed));
  const feeds = [];
  const failures = [];

  for (const result of results) {
    if (result.status === "fulfilled") {
      feeds.push(result.value);
    } else {
      failures.push(result.reason instanceof Error ? result.reason.message : String(result.reason));
    }
  }

  const cache = {
    refreshedAt: new Date().toISOString(),
    feeds,
    failures
  };

  await mkdir(generatedDir, { recursive: true });
  await writeFile(path.join(generatedDir, "rss-cache.json"), JSON.stringify(cache, null, 2), "utf8");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
