import { createHash } from "node:crypto";

function decodeEntities(value = "") {
  return value
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, "\"")
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, " ");
}

export function stripHtml(value = "") {
  return decodeEntities(value)
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function firstMatch(block, patterns) {
  for (const pattern of patterns) {
    const match = pattern.exec(block);
    if (match?.[1]) {
      return decodeEntities(match[1].trim());
    }
  }

  return "";
}

function collectBlocks(xml) {
  const rssBlocks = [...xml.matchAll(/<item\b[\s\S]*?<\/item>/gi)].map((match) => match[0]);
  if (rssBlocks.length) {
    return rssBlocks;
  }
  return [...xml.matchAll(/<entry\b[\s\S]*?<\/entry>/gi)].map((match) => match[0]);
}

const MONTHS = {
  january: 0,
  february: 1,
  march: 2,
  april: 3,
  may: 4,
  june: 5,
  july: 6,
  august: 7,
  september: 8,
  october: 9,
  november: 10,
  december: 11
};

function parsePublishedAt(value) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (!Number.isNaN(parsed.getTime())) {
    return parsed.toISOString();
  }

  const crisisGroupMatch = value.match(
    /^[A-Za-z]+,\s+([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})\s+-\s+(\d{1,2}):(\d{2})$/
  );
  if (!crisisGroupMatch) {
    return null;
  }

  const [, monthName, day, year, hour, minute] = crisisGroupMatch;
  const month = MONTHS[monthName.toLowerCase()];
  if (month === undefined) {
    return null;
  }

  return new Date(Date.UTC(Number(year), month, Number(day), Number(hour), Number(minute))).toISOString();
}

export function parseFeed(xml) {
  const blocks = collectBlocks(xml);

  return blocks.map((block) => {
    const title = firstMatch(block, [/<title>([\s\S]*?)<\/title>/i]);
    const link =
      firstMatch(block, [/<link>([\s\S]*?)<\/link>/i]) ||
      firstMatch(block, [/<link[^>]+href="([^"]+)"/i]);
    const description = firstMatch(block, [
      /<description>([\s\S]*?)<\/description>/i,
      /<content:encoded>([\s\S]*?)<\/content:encoded>/i,
      /<summary>([\s\S]*?)<\/summary>/i,
      /<content[^>]*>([\s\S]*?)<\/content>/i
    ]);
    const publishedAt = firstMatch(block, [
      /<pubDate>([\s\S]*?)<\/pubDate>/i,
      /<published>([\s\S]*?)<\/published>/i,
      /<updated>([\s\S]*?)<\/updated>/i,
      /<dc:date>([\s\S]*?)<\/dc:date>/i
    ]);
    const author = firstMatch(block, [
      /<dc:creator>([\s\S]*?)<\/dc:creator>/i,
      /<author>([\s\S]*?)<\/author>/i,
      /<name>([\s\S]*?)<\/name>/i
    ]);
    const guid = firstMatch(block, [/<guid[^>]*>([\s\S]*?)<\/guid>/i, /<id>([\s\S]*?)<\/id>/i]);

    return {
      title: stripHtml(title),
      link: stripHtml(link),
      description: stripHtml(description),
      publishedAt: parsePublishedAt(publishedAt),
      author: stripHtml(author),
      guid: stripHtml(guid)
    };
  });
}

export function normalizeFeedItems(feed, parsedItems) {
  return parsedItems
    .filter((item) => item.title && item.publishedAt && (item.link || item.guid))
    .slice(0, 12)
    .map((item) => {
      const stableKey = item.link || item.guid || `${feed.id}:${item.title}`;
      const hash = createHash("sha1").update(stableKey).digest("hex").slice(0, 10);
      return {
        id: `${feed.id}-${hash}`,
        sourceFeedId: feed.id,
        sourceFamily: feed.sourceFamily,
        source: feed.source,
        sourceLabel: feed.label,
        title: item.title,
        rawText: item.description || item.title,
        language: "en",
        url: item.link || feed.url,
        author: {
          name: item.author || feed.source,
          profileLocation: feed.placeHints[0] ?? ""
        },
        engagement: {},
        placeHints: feed.placeHints,
        provenance: `live rss feed: ${feed.label}`,
        publishedAt: item.publishedAt,
        fetchedFrom: feed.url
      };
    });
}
