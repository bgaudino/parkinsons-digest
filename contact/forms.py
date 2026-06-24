from django import forms

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["name", "email", "message"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "input",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "input",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "textarea",
                    "rows": 6,
                    "placeholder": "How can Parkinson's Digest be improved?",
                }
            ),
        }
