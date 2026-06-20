from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Q

import django_filters
import requests

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
    journal = django_filters.CharFilter(
        field_name="paper__journal", lookup_expr="iexact"
    )
    source = django_filters.CharFilter(
        field_name="article__source", lookup_expr="iexact"
    )
    zipcode = django_filters.CharFilter(method="filter_zipcode")

    class Meta:
        model = FeedItem
        fields = ("content_type", "status", "phase", "journal", "source", "zipcode")

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

    def filter_zipcode(self, queryset, name, value):
        default_radius = 25
        lat, lon = get_latlong(value)
        if lat is None or lon is None:
            return queryset.none()
        user_point = Point(lon, lat, srid=4326)
        try:
            radius = int(self.request.GET.get("distance", default_radius))
        except (ValueError, TypeError):
            radius = default_radius
        return queryset.filter(
            trial__triallocation__point__dwithin=(user_point, D(mi=radius))
        ).distinct()


def get_latlong(zipcode):
    response = requests.get(
        "https://api.openweathermap.org/geo/1.0/zip",
        params={"zip": f"{zipcode},US", "appid": settings.OPEN_WEATHER_API_KEY},
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("lat"), data.get("lon")
    else:
        return None, None
