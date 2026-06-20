from datetime import datetime
from email.utils import parsedate_to_datetime

from django.db import models
from django.contrib.gis.db.models import PointField


class ContentBase(models.Model):
    title = models.CharField()
    summary = models.TextField()
    date = models.DateTimeField(null=True, blank=True)
    raw = models.JSONField(default=dict)

    class Meta:
        abstract = True


class TrialStatus(models.TextChoices):
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING", "Active, not recruiting"
    APPROVED_FOR_MARKETING = "APPROVED_FOR_MARKETING", "Approved for marketing"
    AVAILABLE = "AVAILABLE", "Available"
    COMPLETED = "COMPLETED", "Completed"
    ENROLLING_BY_INVITATION = "ENROLLING_BY_INVITATION", "Enrolling by invitation"
    NOT_YET_RECRUITING = "NOT_YET_RECRUITING", "Not yet recruiting"
    NO_LONGER_AVAILABLE = "NO_LONGER_AVAILABLE", "No longer available"
    RECRUITING = "RECRUITING", "Recruiting"
    SUSPENDED = "SUSPENDED", "Suspended"
    TEMPORARILY_NOT_AVAILABLE = (
        "TEMPORARILY_NOT_AVAILABLE",
        "Temporarily not available",
    )
    TERMINATED = "TERMINATED", "Terminated"
    UNKNOWN = "UNKNOWN", "Unknown"
    WITHDRAWN = "WITHDRAWN", "Withdrawn"


class TrialPhase(models.TextChoices):
    PHASE_1 = "PHASE1", "Phase 1"
    PHASE_2 = "PHASE2", "Phase 2"
    PHASE_3 = "PHASE3", "Phase 3"
    PHASE_4 = "PHASE4", "Phase 4"
    PHASE_1_2 = "PHASE1/PHASE2", "Phase 1/2"
    PHASE_2_3 = "PHASE2/PHASE3", "Phase 2/3"
    EARLY_PHASE_1 = "EARLY_PHASE1", "Early Phase 1"
    NA = "NA", "N/A"


class Trial(ContentBase):
    nct_id = models.CharField(unique=True)
    status = models.CharField(choices=TrialStatus.choices)
    phase = models.CharField(choices=TrialPhase.choices)
    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    last_update = models.DateField(null=True, blank=True)
    date = models.GeneratedField(
        expression=models.Case(
            models.When(last_update__isnull=False, then="last_update"),
            models.When(completion_date__isnull=False, then="completion_date"),
            models.When(start_date__isnull=False, then="start_date"),
            default=None,
            output_field=models.DateTimeField(),
        ),
        output_field=models.DateTimeField(),
        db_persist=True,
    )

    def __str__(self):
        return self.title

    @property
    def link(self):
        return f"https://clinicaltrials.gov/ct2/show/{self.nct_id}"

    @classmethod
    def ingest(cls, data, commit=True):
        def parse_date(date_str):
            if not date_str:
                return None
            parts = date_str.split("-")
            if len(parts) == 3:
                return date_str
            year, month = parts
            return f"{year}-{month}-01"

        protocal_section = data["protocolSection"]
        description_module = protocal_section["descriptionModule"]
        id_module = protocal_section["identificationModule"]
        status_module = protocal_section["statusModule"]
        design_module = protocal_section["designModule"]
        phase = design_module.get("phases", [TrialPhase.NA])[0]
        if commit:
            instance, _ = cls.objects.update_or_create(
                nct_id=id_module["nctId"],
                defaults={
                    "title": id_module["briefTitle"],
                    "summary": description_module["briefSummary"],
                    "status": status_module["overallStatus"],
                    "phase": phase,
                    "start_date": parse_date(
                        status_module.get("startDateStruct", {}).get("date")
                    ),
                    "completion_date": parse_date(
                        status_module.get("completionDateStruct", {}).get("date")
                    ),
                    "last_update": parse_date(
                        status_module.get("lastUpdatePostDateStruct", {}).get("date")
                    ),
                    "raw": data,
                },
            )
            FeedItem.objects.get_or_create(trial=instance)
            return instance
        return cls(
            nct_id=id_module["nctId"],
            title=id_module["briefTitle"],
            summary=description_module["briefSummary"],
            status=status_module["overallStatus"],
            phase=phase,
            start_date=parse_date(status_module.get("startDateStruct", {}).get("date")),
            completion_date=parse_date(
                status_module.get("completionDateStruct", {}).get("date")
            ),
            last_update=parse_date(
                status_module.get("lastUpdatePostDateStruct", {}).get("date")
            ),
            raw=data,
        )


class TrialLocation(models.Model):
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE)
    facility = models.CharField(blank=True)
    city = models.CharField(blank=True)
    state = models.CharField(blank=True)
    country = models.CharField(blank=True)
    point = PointField(null=True, geography=True, spatial_index=True)
    raw = models.JSONField(default=dict)

    def __str__(self):
        return ", ".join(
            filter(bool, [self.facility, self.city, self.state, self.country])
        )


class Article(ContentBase):
    source = models.CharField()
    link = models.URLField(unique=True)

    def __str__(self):
        return self.title

    @classmethod
    def ingest(cls, entry, source, commit=True):
        published = None
        if "published" in entry:
            published = parsedate_to_datetime(entry.published)
        elif "updated" in entry:
            published = entry.updated
        if commit:
            instance, _ = cls.objects.update_or_create(
                link=entry.link,
                defaults={
                    "title": entry.title,
                    "summary": entry.summary,
                    "date": published,
                    "source": source,
                    "raw": entry,
                },
            )
            FeedItem.objects.get_or_create(article=instance)
            return instance
        return cls(
            title=entry.title,
            link=entry.link,
            summary=entry.summary,
            date=published,
            source=source,
            raw=entry,
        )


class Paper(ContentBase):
    pmid = models.BigIntegerField(unique=True)
    authors = models.TextField()
    journal = models.CharField()

    def __str__(self):
        return self.title

    @property
    def link(self):
        return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"

    @classmethod
    def ingest(cls, data, commit=True):
        published = None
        if date := data.get("epubdate"):
            published = datetime.strptime(date, "%Y %b %d")
        authors = ", ".join([a["name"] for a in data.get("authors", [])])
        if commit:
            instance, _ = cls.objects.update_or_create(
                pmid=data["uid"],
                defaults={
                    "title": data["title"],
                    "authors": authors,
                    "journal": data["fulljournalname"],
                    "date": published,
                    "raw": data,
                },
            )
            FeedItem.objects.get_or_create(paper=instance)
            return instance
        return cls(
            pmid=data["uid"],
            title=data["title"],
            authors=authors,
            journal=data["fulljournalname"],
            date=published,
            raw=data,
        )


class FeedItem(models.Model):
    trial = models.OneToOneField(Trial, on_delete=models.CASCADE, null=True, blank=True)
    article = models.OneToOneField(
        Article, on_delete=models.CASCADE, null=True, blank=True
    )
    paper = models.OneToOneField(Paper, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        trial__isnull=False, article__isnull=True, paper__isnull=True
                    )
                    | models.Q(
                        trial__isnull=True, article__isnull=False, paper__isnull=True
                    )
                    | models.Q(
                        trial__isnull=True, article__isnull=True, paper__isnull=False
                    )
                ),
                name="only_one_content_type",
            )
        ]

    def __str__(self):
        return f"FeedItem: {self.content}"

    @property
    def content(self):
        if self.trial:
            return self.trial
        elif self.article:
            return self.article
        elif self.paper:
            return self.paper

    @property
    def is_paper(self):
        return self.paper is not None

    @property
    def is_article(self):
        return self.article is not None

    @property
    def is_trial(self):
        return self.trial is not None

    @property
    def content_type(self):
        if self.trial:
            return "trial"
        elif self.article:
            return "article"
        elif self.paper:
            return "research"
