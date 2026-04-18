import { createHash } from "node:crypto";

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function cleanText(value = "") {
  return value.replace(/\s+/g, " ").trim();
}

function summarizeText(value = "", maximum = 110) {
  const normalized = cleanText(value);
  if (!normalized) {
    return "Bluesky post";
  }
  if (normalized.length <= maximum) {
    return normalized;
  }
  const truncated = normalized.slice(0, maximum - 1).trimEnd();
  const boundary = truncated.lastIndexOf(" ");
  return `${(boundary > 36 ? truncated.slice(0, boundary) : truncated).trimEnd()}…`;
}

function parseAtUri(uri = "") {
  const match = uri.match(/^at:\/\/([^/]+)\/app\.bsky\.feed\.post\/([^/?#]+)$/);
  if (!match) {
    return null;
  }

  return {
    repo: match[1],
    rkey: match[2]
  };
}

export function buildBlueskyWebUrl(handle, uri, did = "") {
  const parsed = parseAtUri(uri);
  const actor = handle || did || parsed?.repo;

  if (!actor) {
    return "https://bsky.app";
  }

  if (parsed?.rkey) {
    return `https://bsky.app/profile/${actor}/post/${parsed.rkey}`;
  }

  return `https://bsky.app/profile/${actor}`;
}

function unwrapPostView(entry) {
  return entry?.post ?? entry;
}

function normalizeLanguage(post) {
  return post?.record?.langs?.[0] ?? post?.langs?.[0] ?? "und";
}

function normalizeBlueskyEntry(watch, entry) {
  const post = unwrapPostView(entry);
  if (!post?.uri || !post?.author) {
    return null;
  }

  const text = cleanText(post.record?.text ?? "");
  const stableKey = post.uri || `${post.author.did}:${text}`;
  const hash = createHash("sha1").update(stableKey).digest("hex").slice(0, 10);
  const publishedAt = post.record?.createdAt ?? post.indexedAt ?? new Date().toISOString();

  return {
    id: `bluesky-${hash}`,
    sourceQueryId: watch.id,
    sourceFamily: watch.sourceFamily ?? "bluesky",
    source: watch.source ?? "Bluesky AppView",
    sourceLabel: watch.label,
    title: summarizeText(text),
    rawText: text || summarizeText(post.embed?.external?.title ?? post.embed?.external?.description ?? ""),
    language: normalizeLanguage(post),
    url: buildBlueskyWebUrl(post.author.handle, post.uri, post.author.did),
    author: {
      name: post.author.displayName || post.author.handle || post.author.did,
      handle: post.author.handle ?? "",
      did: post.author.did ?? "",
      profileLocation: "",
      description: post.author.description ?? ""
    },
    engagement: {
      likes: post.likeCount ?? 0,
      reposts: post.repostCount ?? 0,
      replies: post.replyCount ?? 0,
      quotes: post.quoteCount ?? 0
    },
    placeHints: watch.placeHints ?? [],
    provenance: `public bluesky ${watch.type}: ${watch.label}`,
    publishedAt,
    watchRefs: [
      {
        id: watch.id,
        label: watch.label,
        type: watch.type
      }
    ],
    bluesky: {
      uri: post.uri,
      cid: post.cid ?? "",
      indexedAt: post.indexedAt ?? "",
      langs: post.record?.langs ?? [],
      facets: post.record?.facets ?? [],
      embed: post.embed ?? null,
      labels: post.labels ?? [],
      reply: post.record?.reply ?? null
    }
  };
}

export function normalizeBlueskyEntries(watch, entries = []) {
  return entries
    .map((entry) => normalizeBlueskyEntry(watch, entry))
    .filter(Boolean)
    .filter((item) => item.rawText && item.publishedAt);
}

export function mergeBlueskyItems(items = []) {
  const merged = new Map();

  for (const item of items) {
    const key = item.bluesky?.uri ?? item.id;
    const existing = merged.get(key);

    if (!existing) {
      merged.set(key, {
        ...item,
        placeHints: unique(item.placeHints ?? []),
        watchRefs: item.watchRefs ?? []
      });
      continue;
    }

    merged.set(key, {
      ...existing,
      placeHints: unique([...(existing.placeHints ?? []), ...(item.placeHints ?? [])]),
      watchRefs: [...(existing.watchRefs ?? []), ...(item.watchRefs ?? [])],
      provenance: unique([existing.provenance, item.provenance]).join(" + ")
    });
  }

  return [...merged.values()].map((item) => {
    const seenWatchRefs = new Set();
    const watchRefs = [];

    for (const watchRef of item.watchRefs ?? []) {
      const key = `${watchRef.id}|${watchRef.type}|${watchRef.label}`;
      if (seenWatchRefs.has(key)) {
        continue;
      }
      seenWatchRefs.add(key);
      watchRefs.push(watchRef);
    }

    return {
      ...item,
      watchRefs
    };
  });
}
