from django.urls import path


from . import views

urlpatterns = [
    path("feedback/", views.FeedbackCreateView.as_view(), name="feedback"),
    path("thanks/", views.ThanksView.as_view(), name="thanks"),
]
