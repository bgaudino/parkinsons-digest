from unittest.mock import patch

from django.contrib.gis.geos import Point
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from feed.models import (
    Article,
    FeedItem,
    Paper,
    Trial,
    TrialLocation,
    TrialPhase,
    TrialStatus,
)


class DictEntry(dict):
    """Stand-in for a feedparser entry: dict membership + attribute access."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


def trial_data(**status):
    return {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT123", "briefTitle": "A Trial"},
            "descriptionModule": {"briefSummary": "summary"},
            "designModule": {"phases": [TrialPhase.PHASE_2]},
            "statusModule": {"overallStatus": TrialStatus.RECRUITING, **status},
        }
    }


class TrialIngestTests(SimpleTestCase):
    def test_full_date_passes_through(self):
        data = trial_data(startDateStruct={"date": "2024-03-15"})
        trial = Trial.ingest(data, commit=False)
        self.assertEqual(trial.start_date, "2024-03-15")

    def test_year_month_gets_first_of_month(self):
        data = trial_data(completionDateStruct={"date": "2024-03"})
        trial = Trial.ingest(data, commit=False)
        self.assertEqual(trial.completion_date, "2024-03-01")

    def test_missing_date_is_none(self):
        trial = Trial.ingest(trial_data(), commit=False)
        self.assertIsNone(trial.start_date)

    def test_missing_phase_defaults_to_na(self):
        data = trial_data()
        data["protocolSection"]["designModule"] = {}
        trial = Trial.ingest(data, commit=False)
        self.assertEqual(trial.phase, TrialPhase.NA)


class PaperIngestTests(SimpleTestCase):
    def test_authors_joined_and_date_parsed(self):
        data = {
            "uid": "42",
            "title": "Paper",
            "fulljournalname": "Journal",
            "epubdate": "2024 Mar 15",
            "authors": [{"name": "Smith J"}, {"name": "Doe A"}],
        }
        paper = Paper.ingest(data, commit=False)
        self.assertEqual(paper.authors, "Smith J, Doe A")
        self.assertEqual(paper.date.year, 2024)
        self.assertEqual(paper.date.month, 3)

    def test_missing_epubdate_is_none(self):
        data = {"uid": "42", "title": "Paper", "fulljournalname": "Journal"}
        paper = Paper.ingest(data, commit=False)
        self.assertIsNone(paper.date)


class ArticleIngestTests(SimpleTestCase):
    def test_published_rfc822_parsed(self):
        entry = DictEntry(
            title="Post",
            link="https://example.com/post",
            summary="body",
            published="Fri, 15 Mar 2024 10:00:00 +0000",
        )
        article = Article.ingest(entry, "Source", commit=False)
        self.assertEqual(article.date.year, 2024)
        self.assertEqual(article.source, "Source")


class IngestSaveTests(TestCase):
    def test_trial_saved_with_feed_item(self):
        Trial.ingest(trial_data(startDateStruct={"date": "2024-03-15"}))
        trial = Trial.objects.get(nct_id="NCT123")
        self.assertEqual(trial.title, "A Trial")
        self.assertTrue(FeedItem.objects.filter(trial=trial).exists())

    def test_trial_ingest_is_idempotent(self):
        Trial.ingest(trial_data())
        Trial.ingest(trial_data())
        self.assertEqual(Trial.objects.filter(nct_id="NCT123").count(), 1)
        self.assertEqual(FeedItem.objects.count(), 1)

    def test_paper_saved_with_feed_item(self):
        Paper.ingest(
            {
                "uid": "42",
                "title": "Paper",
                "fulljournalname": "Journal",
                "authors": [{"name": "Smith J"}],
            }
        )
        paper = Paper.objects.get(pmid=42)
        self.assertTrue(FeedItem.objects.filter(paper=paper).exists())

    def test_article_saved_with_feed_item(self):
        entry = DictEntry(title="Post", link="https://example.com/post", summary="body")
        Article.ingest(entry, "Source")
        article = Article.objects.get(link="https://example.com/post")
        self.assertTrue(FeedItem.objects.filter(article=article).exists())


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
)
class FeedViewTests(TestCase):
    def test_feed_renders(self):
        trial = Trial.objects.create(
            nct_id="NCT1",
            title="A Trial",
            summary="s",
            status=TrialStatus.RECRUITING,
            phase=TrialPhase.PHASE_2,
        )
        FeedItem.objects.create(trial=trial)
        response = self.client.get(reverse("feed"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A Trial")

    @patch("feed.filters.get_latlong")
    def test_zipcode_filters_to_nearby_trials(self, get_latlong):
        # Chicago-ish reference point the zip code resolves to.
        get_latlong.return_value = (41.80, -87.60)

        near = Trial.objects.create(
            nct_id="NEAR",
            title="Near Trial",
            summary="s",
            status=TrialStatus.RECRUITING,
            phase=TrialPhase.PHASE_2,
        )
        far = Trial.objects.create(
            nct_id="FAR",
            title="Far Trial",
            summary="s",
            status=TrialStatus.RECRUITING,
            phase=TrialPhase.PHASE_2,
        )
        FeedItem.objects.create(trial=near)
        FeedItem.objects.create(trial=far)
        TrialLocation.objects.create(trial=near, point=Point(-87.61, 41.81, srid=4326))
        TrialLocation.objects.create(trial=far, point=Point(-80.0, 40.0, srid=4326))

        response = self.client.get(reverse("feed"), {"zipcode": "60601"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Near Trial")
        self.assertNotContains(response, "Far Trial")
