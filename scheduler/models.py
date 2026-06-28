from django.db import models
from django.conf import settings


class Notification(models.Model):
    """User notification for reminders, digests, and encouragements."""

    class NotificationType(models.TextChoices):
        EMAIL = 'email', 'Email'
        IN_APP = 'in_app', 'In-App'
        BOTH = 'both', 'Email + In-App'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    task = models.ForeignKey(
        'tasks.Task', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notifications',
    )
    message = models.TextField()
    notification_type = models.CharField(
        max_length=10,
        choices=NotificationType.choices,
        default=NotificationType.IN_APP,
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email}: {self.message[:50]}'
