from django.urls import path, include
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("", views.Feed.as_view(), name="feed"),
    path("contact/", include("contact.urls")),
    path(
        "privacy/", TemplateView.as_view(template_name="privacy.html"), name="privacy"
    ),
]
