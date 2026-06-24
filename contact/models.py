from django.db import models


class FeedbackStatus(models.TextChoices):
    NEW = "new", "New"
    REVIEWED = "reviewed", "Reviewed"
    IMPLEMENTED = "implemented", "Implemented"
    REJECTED = "rejected", "Rejected"


class Feedback(models.Model):
    name = models.CharField(blank=True)
    email = models.EmailField(blank=True)
    message = models.TextField()
    status = models.CharField(
        choices=FeedbackStatus.choices,
        default=FeedbackStatus.NEW,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.name or 'Anonymous'} at {self.submitted_at}"

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name_plural = "Feedback"
