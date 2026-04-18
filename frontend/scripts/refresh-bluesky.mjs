import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { mergeBlueskyItems, normalizeBlueskyEntries } from "../src/lib/bluesky.js";
import { BLUESKY_WATCH_CATALOG } from "../src/lib/bluesky-watch.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const generatedDir = path.resolve(__dirname, "../src/generated");
const appViewBaseUrls = [
  "https://api.bsky.app/xrpc",
  "https://public.api.bsky.app/xrpc"
];

function buildRequest(watch) {
  switch (watch.type) {
    case "authorFeed":
      return {
        endpoint: "app.bsky.feed.getAuthorFeed",
        params: {
          actor: watch.actor,
          filter: watch.filter ?? "posts_no_replies",
          limit: String(watch.limit ?? 25)
        }
      };
    case "feed":
      return {
        endpoint: "app.bsky.feed.getFeed",
        params: {
          feed: watch.feed,
          limit: String(watch.limit ?? 25)
        }
      };
    case "listFeed":
      return {
        endpoint: "app.bsky.feed.getListFeed",
        params: {
          list: watch.list,
          limit: String(watch.limit ?? 25)
        }
      };
    case "searchPosts":
    default:
      return {
        endpoint: "app.bsky.feed.searchPosts",
        params: {
          q: watch.q,
          sort: watch.sort ?? "latest",
          limit: String(watch.limit ?? 25)
        }
      };
  }
}

function extractEntries(watch, data) {
  if (watch.type === "searchPosts") {
    return data.posts ?? [];
  }
  return data.feed ?? [];
}

async function fetchWatch(watch) {
  const { endpoint, params } = buildRequest(watch);
  const failures = [];

  for (const baseUrl of appViewBaseUrls) {
    const url = new URL(`${baseUrl}/${endpoint}`);

    for (const [key, value] of Object.entries(params)) {
      if (value) {
        url.searchParams.set(key, value);
      }
    }

    try {
      const response = await fetch(url, {
        headers: {
          "accept-language": watch.language ?? "en",
          "user-agent": "SignalAtlas/0.1 (+https://github.com/DrJeky11/osint-lite-deftech)"
        }
      });

      if (!response.ok) {
        failures.push(`${baseUrl} -> ${response.status}`);
        continue;
      }

      const data = await response.json();
      const items = mergeBlueskyItems(normalizeBlueskyEntries(watch, extractEntries(watch, data)));

      return {
        ...watch,
        fetchedAt: new Date().toISOString(),
        itemCount: items.length,
        items
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const cause =
        error && typeof error === "object" && "cause" in error && error.cause
          ? String(error.cause)
          : "";
      const detail = cause && !message.includes(cause) ? `${message} (${cause})` : message;
      failures.push(`${baseUrl} -> ${detail}`);
    }
  }

  throw new Error(`${watch.id}: ${failures.join("; ")}`);
}

async function main() {
  const watches = [];
  const failures = [];

  for (const watch of BLUESKY_WATCH_CATALOG) {
    try {
      watches.push(await fetchWatch(watch));
    } catch (error) {
      failures.push(error instanceof Error ? error.message : String(error));
    }
  }

  const cache = {
    refreshedAt: new Date().toISOString(),
    watches,
    failures
  };

  await mkdir(generatedDir, { recursive: true });
  await writeFile(path.join(generatedDir, "bluesky-cache.json"), JSON.stringify(cache, null, 2), "utf8");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
