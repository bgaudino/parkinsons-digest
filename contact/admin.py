from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "submitted_at", "status")
    search_fields = ("name", "email", "message")
    list_filter = ("status",)
    readonly_fields = (
        "name",
        "email",
        "message",
        "submitted_at",
    )
