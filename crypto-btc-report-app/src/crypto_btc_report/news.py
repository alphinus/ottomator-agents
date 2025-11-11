from __future__ import annotations

import datetime as dt
import time
from typing import Any, Iterable, Optional

import feedparser

class NewsFetchError(RuntimeError):
    pass


class CryptoNewsFetcher:
    """Fetch crypto-focused headlines from free RSS feeds."""

    def __init__(self, rss_feeds: Optional[Iterable[str]] = None) -> None:
        self.rss_feeds = list(rss_feeds or [])
        if not self.rss_feeds:
            raise NewsFetchError("At least one RSS feed must be configured.")

    def fetch_headlines(
        self,
        query: str = "bitcoin",
        lookback_hours: int = 24,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        cut_off = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) - dt.timedelta(hours=lookback_hours)
        keywords = self._extract_keywords(query)
        results: list[dict[str, Any]] = []

        for feed_url in self.rss_feeds:
            parsed = feedparser.parse(feed_url)
            source_title = parsed.feed.get("title") if parsed.feed else feed_url
            for entry in parsed.entries:
                published_dt = self._parse_published(entry)
                if not published_dt or published_dt < cut_off:
                    continue
                text_blob = " ".join(
                    filter(
                        None,
                        [entry.get("title"), entry.get("summary"), entry.get("description")],
                    )
                ).lower()
                if keywords and not any(keyword in text_blob for keyword in keywords):
                    continue
                results.append(
                    {
                        "title": entry.get("title"),
                        "url": entry.get("link"),
                        "source": source_title,
                        "published_at": published_dt.isoformat(),
                        "summary": entry.get("summary") or entry.get("description"),
                    }
                )

        if not results:
            raise NewsFetchError("No headlines found in configured RSS feeds. Try adjusting RSS_FEEDS or keywords.")

        # Deduplicate and keep top N sorted by recency
        deduped: dict[str, dict[str, Any]] = {}
        for article in sorted(results, key=lambda item: item["published_at"], reverse=True):
            url = article.get("url")
            if url and url not in deduped:
                deduped[url] = article
        return list(deduped.values())[:limit]

    @staticmethod
    def _parse_published(entry: Any) -> Optional[dt.datetime]:
        published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if not published_struct:
            return None
        timestamp = time.mktime(published_struct)
        return dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)

    @staticmethod
    def _extract_keywords(query: str) -> list[str]:
        if not query:
            return []
        sanitized = query.replace("OR", " ").replace("AND", " ")
        return [token.strip().lower() for token in sanitized.split() if token.strip()]
