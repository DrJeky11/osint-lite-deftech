import test from "node:test";
import assert from "node:assert/strict";

import {
  buildBlueskyWebUrl,
  mergeBlueskyItems,
  normalizeBlueskyEntries
} from "../src/lib/bluesky.js";

test("buildBlueskyWebUrl converts AT URIs into app URLs", () => {
  assert.equal(
    buildBlueskyWebUrl("alerts.bsky.social", "at://did:plc:abc123/app.bsky.feed.post/3lqexample"),
    "https://bsky.app/profile/alerts.bsky.social/post/3lqexample"
  );
});

test("normalizeBlueskyEntries maps post views into SourceItem records", () => {
  const items = normalizeBlueskyEntries(
    {
      id: "khartoum-watch",
      label: "Khartoum Watch",
      source: "Bluesky AppView",
      sourceFamily: "bluesky",
      type: "searchPosts",
      placeHints: ["Khartoum", "Sudan"]
    },
    [
      {
        uri: "at://did:plc:test123/app.bsky.feed.post/3lqexample",
        cid: "bafytest",
        indexedAt: "2026-04-18T04:05:00.000Z",
        likeCount: 9,
        repostCount: 2,
        replyCount: 1,
        quoteCount: 0,
        author: {
          did: "did:plc:test123",
          handle: "alerts.bsky.social",
          displayName: "Alerts Desk",
          description: "Regional watch account"
        },
        record: {
          text: "Khartoum monitors report convoy movement and protest crowds near bridges.",
          createdAt: "2026-04-18T04:01:00.000Z",
          langs: ["en"]
        }
      }
    ]
  );

  assert.equal(items.length, 1);
  assert.equal(items[0].sourceFamily, "bluesky");
  assert.equal(items[0].author.handle, "alerts.bsky.social");
  assert.equal(items[0].engagement.likes, 9);
  assert.deepEqual(items[0].placeHints, ["Khartoum", "Sudan"]);
  assert.equal(items[0].bluesky.uri, "at://did:plc:test123/app.bsky.feed.post/3lqexample");
});

test("mergeBlueskyItems deduplicates repeated posts across watches and unions place hints", () => {
  const merged = mergeBlueskyItems([
    {
      id: "one",
      placeHints: ["Khartoum"],
      provenance: "public bluesky searchPosts: Khartoum Watch",
      watchRefs: [{ id: "khartoum-watch", label: "Khartoum Watch", type: "searchPosts" }],
      bluesky: { uri: "at://did:plc:test123/app.bsky.feed.post/3lqexample" }
    },
    {
      id: "two",
      placeHints: ["Sudan"],
      provenance: "public bluesky searchPosts: Sudan Watch",
      watchRefs: [{ id: "sudan-watch", label: "Sudan Watch", type: "searchPosts" }],
      bluesky: { uri: "at://did:plc:test123/app.bsky.feed.post/3lqexample" }
    }
  ]);

  assert.equal(merged.length, 1);
  assert.deepEqual(merged[0].placeHints, ["Khartoum", "Sudan"]);
  assert.equal(merged[0].watchRefs.length, 2);
});
