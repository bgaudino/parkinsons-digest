from django.db.models import Case, When, DateTimeField

from django.views.generic import ListView

from .models import FeedItem


class Feed(ListView):
    queryset = (
        FeedItem.objects.select_related("trial", "article", "paper")
        .annotate(
            date=Case(
                When(trial__isnull=False, then="trial__date"),
                When(article__isnull=False, then="article__date"),
                When(paper__isnull=False, then="paper__date"),
                output_field=DateTimeField(),
            )
        )
        .order_by("-date")
    )
    template_name = "feed/feed.html"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        content_type = self.request.GET.get("type")
        if content_type == "trial":
            qs = qs.filter(trial__isnull=False)
        elif content_type == "news":
            qs = qs.filter(article__isnull=False)
        elif content_type == "research":
            qs = qs.filter(paper__isnull=False)
        return qs
