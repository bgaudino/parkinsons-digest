import logging

from django.core.management.base import BaseCommand

import requests

from feed.models import Trial, FeedItem


logger = logging.getLogger(__name__)
BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
BASE_PARAMS = {
    "query.cond": "Parkinson disease",
    "pageSize": 1000,
}


class Command(BaseCommand):
    def handle(self, *args, **options):
        def get_trials(params=None):
            if params is None:
                params = {}
            response = requests.get(BASE_URL, params=BASE_PARAMS | params)
            data = response.json()
            trials = [Trial.ingest(trial, commit=False) for trial in data["studies"]]
            Trial.objects.bulk_create(
                trials,
                update_conflicts=True,
                unique_fields=["nct_id"],
                update_fields=[
                    "title",
                    "summary",
                    "status",
                    "start_date",
                    "completion_date",
                    "last_update",
                    "phase",
                    "raw",
                ],
            )
            feed_items = [FeedItem(trial=trial) for trial in trials]
            FeedItem.objects.bulk_create(
                feed_items,
                ignore_conflicts=True,
                unique_fields=["trial"],
            )
            return data

        data = get_trials()
        while page_token := data.get("nextPageToken"):
            data = get_trials({"pageToken": page_token})
            logger.info(f"Ingested page with {len(data['studies'])} trials")
