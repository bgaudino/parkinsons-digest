import logging

from django.core.management.base import BaseCommand

import feedparser

from feed.models import Article, FeedItem

logger = logging.getLogger(__name__)


FEEDS = [
    "https://parkinsonsnewstoday.com/feed/",
    "https://www.apdaparkinson.org/doctor-blogs/a-closer-look/feed/",
    "https://briangrant.org/feed/",
    "https://parkingsuns.com/feed/",
    "https://parkinsons.ie/feed/",
    "https://charconeurotech.com/feed/",
    "https://pdwise.com/feed/",
    "https://journals.sagepub.com/action/showFeed?ui=0&mi=ehikzz&ai=2b4&jc=pkn&type=etoc&feed=rss&_gl=1*6di3a1*_up*MQ..*_ga*MjUwODc4ODI5LjE3ODA0NDkzODU.*_ga_60R758KFDG*czE3ODA0NDkzODUkbzEkZzAkdDE3ODA0NDkzODUkajYwJGwxJGgxNTE1OTcwNDI5",
    "https://journals.sagepub.com/action/showFeed?ui=0&mi=ehikzz&ai=2b4&jc=pkn&type=axatoc&feed=rss&_gl=1*13n62b2*_up*MQ..*_ga*MjUwODc4ODI5LjE3ODA0NDkzODU.*_ga_60R758KFDG*czE3ODA0NDkzODUkbzEkZzAkdDE3ODA0NDkzODUkajYwJGwxJGgxNTE1OTcwNDI5",
    "https://medlineplus.gov/feeds/topics/parkinsonsdisease.xml",
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        for url in FEEDS:
            feed = feedparser.parse(url, sanitize_html=True)
            if feed.bozo:
                logger.error(f"Error parsing feed: {url} - {feed.bozo_exception}")
                continue

            logger.info(f"Parsing feed: {url} with {len(feed.entries)} entries")
            source = feed.feed.title
            entries = [
                Article.ingest(entry, source, commit=False) for entry in feed.entries
            ]
            Article.objects.bulk_create(
                entries,
                update_conflicts=True,
                unique_fields=["link"],
                update_fields=["title", "summary", "date", "raw"],
            )
            items = [FeedItem(article=entry) for entry in entries]
            FeedItem.objects.bulk_create(items, ignore_conflicts=True)
            logger.info(f"Finished parsing feed: {url}")
