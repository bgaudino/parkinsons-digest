import logging

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

import requests

from feed.models import Trial, FeedItem, TrialLocation


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
            trials = []
            for study in data["studies"]:
                trial = Trial.ingest(study)
                locations = (
                    trial.raw.get("protocolSection", {})
                    .get("contactsLocationsModule", {})
                    .get("locations", [])
                )
                trial_locations = []
                for location in locations:
                    point = None
                    if (
                        location.get("geoPoint", {}).get("lat") is not None
                        and location.get("geoPoint", {}).get("lon") is not None
                    ):
                        point = Point(
                            x=location["geoPoint"]["lon"],
                            y=location["geoPoint"]["lat"],
                            srid=4326,
                        )
                    trial_locations.append(
                        TrialLocation(
                            trial=trial,
                            facility=location.get("facility", ""),
                            city=location.get("city", ""),
                            state=location.get("state", ""),
                            country=location.get("country", ""),
                            point=point,
                            raw=location,
                        )
                    )
                TrialLocation.objects.bulk_create(trial_locations)
                trials.append(trial)
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
