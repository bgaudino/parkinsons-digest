from django.contrib import admin

from . import models


@admin.register(models.Trial)
class TrialAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "date")
    search_fields = (
        "nct_id",
        "title",
        "summary",
    )
    list_filter = ("status",)


@admin.register(models.Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "date")
    search_fields = ("title", "summary")


@admin.register(models.Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ("title", "date")
    search_fields = ("pmid", "title", "summary")
