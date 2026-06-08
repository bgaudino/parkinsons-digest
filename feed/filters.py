import django_filters

from django.db.models import Q

from feed.models import FeedItem, TrialStatus, TrialPhase


class FeedItemFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    content_type = django_filters.CharFilter(
        field_name="content_type", method="filter_content_type"
    )
    status = django_filters.ChoiceFilter(
        field_name="trial__status", lookup_expr="iexact", choices=TrialStatus.choices
    )
    phase = django_filters.ChoiceFilter(
        field_name="trial__phase", lookup_expr="iexact", choices=TrialPhase.choices
    )

    class Meta:
        model = FeedItem
        fields = ("content_type", "status", "phase")

    def filter_content_type(self, queryset, name, value):
        match value:
            case "research":
                queryset = queryset.filter(paper__isnull=False)
            case "trial":
                queryset = queryset.filter(trial__isnull=False)
            case "article":
                queryset = queryset.filter(article__isnull=False)
            case _:
                return queryset
        return queryset

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(trial__title__icontains=value)
            | Q(trial__summary__icontains=value)
            | Q(trial__nct_id__icontains=value)
            | Q(trial__status__icontains=value)
            | Q(trial__phase__icontains=value)
            | Q(article__title__icontains=value)
            | Q(article__summary__icontains=value)
            | Q(article__source__icontains=value)
            | Q(paper__title__icontains=value)
            | Q(paper__summary__icontains=value)
            | Q(paper__authors__icontains=value)
            | Q(paper__journal__icontains=value)
        )
