from django.db.models import Case, When, DateTimeField, F

from django.views.generic import ListView

from .models import FeedItem

from .filters import FeedItemFilter


class Feed(ListView):
    template_name = "feed/feed.html"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            FeedItem.objects.select_related("trial", "article", "paper")
            .annotate(
                date=Case(
                    When(trial__isnull=False, then="trial__date"),
                    When(article__isnull=False, then="article__date"),
                    When(paper__isnull=False, then="paper__date"),
                    output_field=DateTimeField(),
                )
            )
            .order_by(F("date").desc(nulls_last=True))
        )
        return FeedItemFilter(self.request.GET, queryset=qs).qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = FeedItemFilter(self.request.GET).form
        return context
