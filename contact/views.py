from django.views.generic import CreateView, TemplateView

from .forms import FeedbackForm


class FeedbackCreateView(CreateView):
    form_class = FeedbackForm
    template_name = "contact/feedback_form.html"
    success_url = "/contact/thanks/"


class ThanksView(TemplateView):
    template_name = "contact/thanks.html"
