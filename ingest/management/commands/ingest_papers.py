import logging

from django.core.management.base import BaseCommand

import requests

from feed.models import Paper, FeedItem


logger = logging.getLogger(__name__)

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
BASE_PARAMS = {
    "db": "pubmed",
    "retmode": "json",
    "sort": "pub date",
}


class Command(BaseCommand):
    def handle(self, *args, **options):
        r = requests.get(
            f"{BASE_URL}esearch.fcgi",
            params={
                **BASE_PARAMS,
                "term": "Parkinson disease[Title/Abstract]",
                "retmax": 300,
            },
        )

        data = r.json()
        pmids = data["esearchresult"]["idlist"]
        r = requests.get(
            f"{BASE_URL}esummary.fcgi",
            params={
                **BASE_PARAMS,
                "id": ",".join(pmids),
            },
        )
        data = r.json()
        results = data["result"]
        ids = results["uids"]
        papers = [
            Paper.ingest(result, commit=False) for id in ids for result in [results[id]]
        ]

        Paper.objects.bulk_create(
            papers,
            update_conflicts=True,
            unique_fields=["pmid"],
            update_fields=[
                "title",
                "authors",
                "journal",
                "date",
                "raw",
            ],
        )

        feed_items = [FeedItem(paper=paper) for paper in papers]
        FeedItem.objects.bulk_create(
            feed_items,
            update_conflicts=True,
            unique_fields=["paper"],
            update_fields=["paper"],
        )

        logger.info(f"Ingested {len(papers)} papers")

    def parse_date(self, date_str):
        return date_str.replace(" ", "-")
