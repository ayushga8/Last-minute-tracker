from django.db import models
from django.conf import settings
from django.utils import timezone


class Task(models.Model):
    """User task with priority scoring and deadline tracking."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        OVERDUE = 'overdue', 'Overdue'

    class PriorityTag(models.TextChoices):
        CRITICAL = 'critical', 'Critical'
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    deadline = models.DateTimeField()
    priority_score = models.FloatField(default=0.0, help_text='Auto-calculated urgency score')
    priority_tag = models.CharField(
        max_length=10,
        choices=PriorityTag.choices,
        default=PriorityTag.MEDIUM,
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
    )
    category = models.CharField(max_length=100, blank=True, default='General')
    estimated_hours = models.FloatField(default=1.0, help_text='Estimated hours to complete')
    importance_weight = models.IntegerField(
        default=5,
        help_text='Importance from 1 (low) to 10 (critical)',
    )
    google_event_id = models.CharField(
        max_length=255, blank=True, null=True,
        help_text='Google Calendar event ID for sync',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tasks'
        ordering = ['deadline', '-priority_score']

    def __str__(self):
        return f'{self.title} ({self.get_priority_tag_display()})'

    def calculate_priority_score(self):
        """
        Auto-calculate urgency score:
        (deadline_proximity × importance_weight) / estimated_hours
        """
        now = timezone.now()
        if self.deadline <= now:
            proximity = 100.0  # Past deadline = maximum urgency
        else:
            hours_remaining = (self.deadline - now).total_seconds() / 3600
            # Inverse: closer deadline = higher score, capped at 100
            proximity = max(0, min(100, 100 - hours_remaining))

        estimated = max(self.estimated_hours, 0.5)  # Prevent division by zero
        self.priority_score = round((proximity * self.importance_weight) / estimated, 2)

        # Auto-tag based on score
        if self.priority_score >= 150:
            self.priority_tag = self.PriorityTag.CRITICAL
        elif self.priority_score >= 80:
            self.priority_tag = self.PriorityTag.HIGH
        elif self.priority_score >= 30:
            self.priority_tag = self.PriorityTag.MEDIUM
        else:
            self.priority_tag = self.PriorityTag.LOW

        return self.priority_score

    def save(self, *args, **kwargs):
        self.calculate_priority_score()
        # Auto-mark overdue
        if self.deadline <= timezone.now() and self.status not in (self.Status.COMPLETED, self.Status.OVERDUE):
            self.status = self.Status.OVERDUE
        super().save(*args, **kwargs)

    @property
    def time_remaining(self):
        """Return timedelta until deadline."""
        return self.deadline - timezone.now()

    @property
    def is_overdue(self):
        return self.deadline <= timezone.now() and self.status != self.Status.COMPLETED

    @property
    def priority_color(self):
        """CSS color class for urgency."""
        colors = {
            'critical': '#ef4444',
            'high': '#f97316',
            'medium': '#eab308',
            'low': '#22c55e',
        }
        return colors.get(self.priority_tag, '#6b7280')


class AIRecommendation(models.Model):
    """AI-generated suggestions from Gemini API."""

    class RecommendationType(models.TextChoices):
        PRIORITY_RANKING = 'ranking', 'Priority Ranking'
        TIME_BLOCK = 'time_block', 'Time Block Suggestion'
        CLASH_WARNING = 'clash', 'Clash Warning'
        GENERAL = 'general', 'General Suggestion'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_recommendations',
    )
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='ai_recommendations',
    )
    suggestion_text = models.TextField()
    recommendation_type = models.CharField(
        max_length=20,
        choices=RecommendationType.choices,
        default=RecommendationType.GENERAL,
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_recommendations'
        ordering = ['-generated_at']

    def __str__(self):
        return f'AI: {self.suggestion_text[:60]}...'
