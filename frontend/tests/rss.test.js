import test from "node:test";
import assert from "node:assert/strict";

import { normalizeFeedItems, parseFeed, stripHtml } from "../src/lib/rss.js";

test("stripHtml removes tags and decodes common entities", () => {
  assert.equal(stripHtml("<p>Alert &amp; response&nbsp;<strong>update</strong></p>"), "Alert & response update");
});

test("parseFeed handles RSS items and invalid dates safely", () => {
  const items = parseFeed(`
    <rss>
      <channel>
        <item>
          <title><![CDATA[Sudan protest expands]]></title>
          <link>https://example.com/sudan</link>
          <description><![CDATA[<p>Security forces and protesters clashed.</p>]]></description>
          <pubDate>Sat, 18 Apr 2026 03:20:00 GMT</pubDate>
          <dc:creator>Desk</dc:creator>
          <guid>sudan-1</guid>
        </item>
        <item>
          <title>Malformed date example</title>
          <link>https://example.com/bad-date</link>
          <description>Rumor and convoy mentions.</description>
          <pubDate>not a real date</pubDate>
        </item>
      </channel>
    </rss>
  `);

  assert.equal(items.length, 2);
  assert.equal(items[0].title, "Sudan protest expands");
  assert.equal(items[0].description, "Security forces and protesters clashed.");
  assert.equal(items[0].publishedAt, "2026-04-18T03:20:00.000Z");
  assert.equal(items[1].publishedAt, null);
});

test("parseFeed supports Crisis Group date formatting", () => {
  const items = parseFeed(`
    <rss>
      <channel>
        <item>
          <title>Sudan diplomacy backslides</title>
          <link>https://example.com/crisis</link>
          <description>External actors remain divided.</description>
          <pubDate>Friday, April 17, 2026 - 15:01</pubDate>
        </item>
      </channel>
    </rss>
  `);

  assert.equal(items[0].publishedAt, "2026-04-17T15:01:00.000Z");
});

test("normalizeFeedItems maps parsed entries into SourceItem records", () => {
  const normalized = normalizeFeedItems(
    {
      id: "voa-africa",
      label: "VOA Africa",
      source: "Voice of America",
      sourceFamily: "news",
      url: "https://example.com/feed.xml",
      placeHints: ["Africa"]
    },
    [
      {
        title: "Mutiny rumors grow in capital",
        link: "https://example.com/story",
        description: "Army convoy activity followed overnight protests.",
        publishedAt: "2026-04-18T02:45:00.000Z",
        author: "VOA Desk",
        guid: "story-1"
      }
    ]
  );

  assert.equal(normalized.length, 1);
  assert.equal(normalized[0].sourceFeedId, "voa-africa");
  assert.equal(normalized[0].sourceFamily, "news");
  assert.equal(normalized[0].author.name, "VOA Desk");
  assert.deepEqual(normalized[0].placeHints, ["Africa"]);
});
