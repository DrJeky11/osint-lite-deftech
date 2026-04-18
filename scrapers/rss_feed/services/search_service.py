try:
    from ..models import RSSFeedMetadata, RSSRequest
    from .rss_client import fetch_feed, normalize_entry, normalize_feed
except ImportError:
    from models import RSSFeedMetadata, RSSRequest
    from services.rss_client import fetch_feed, normalize_entry, normalize_feed


def build_request_description(req: RSSRequest, feed: RSSFeedMetadata) -> str:
    bits = [f"feed_url={req.feed_url}"]
    if feed.title:
        bits.append(f"feed_title={feed.title}")
    bits.append(f"max_entries={req.max_entries}")
    return ", ".join(bits)


async def fetch_entries(req: RSSRequest) -> tuple[RSSFeedMetadata, list[dict]]:
    parsed_feed = await fetch_feed(str(req.feed_url))
    feed_metadata = RSSFeedMetadata(**normalize_feed(parsed_feed))

    entries = [
        normalize_entry(entry, fallback_id=f"entry-{index + 1}")
        for index, entry in enumerate(parsed_feed.entries[: req.max_entries])
    ]

    return feed_metadata, entries

