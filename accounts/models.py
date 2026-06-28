from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user model for Last-Minute Life Saver."""
    email = models.EmailField(unique=True)
    avatar_url = models.URLField(blank=True, default='')
    calendar_tokens = models.JSONField(
        blank=True, null=True, default=None,
        help_text='Stores Google Calendar OAuth2 tokens (access_token, refresh_token, etc.)'
    )
    notification_email = models.BooleanField(default=True)
    notification_in_app = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email
