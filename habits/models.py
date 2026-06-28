from django.db import models
from django.conf import settings
from django.utils import timezone


class Habit(models.Model):
    """User habit with streak tracking and gamification."""

    class Frequency(models.TextChoices):
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    frequency = models.CharField(
        max_length=10,
        choices=Frequency.choices,
        default=Frequency.DAILY,
    )
    streak_count = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_done = models.DateField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='habits',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'habits'
        ordering = ['-streak_count']
        unique_together = ['name', 'user']

    def __str__(self):
        return f'{self.name} (🔥 {self.streak_count})'

    def mark_done(self):
        """Mark habit as done for today. Returns (success, message)."""
        today = timezone.now().date()

        if self.last_done == today:
            return False, 'Already completed today!'

        if self.frequency == self.Frequency.DAILY:
            if self.last_done and (today - self.last_done).days == 1:
                # Consecutive day — extend streak
                self.streak_count += 1
            elif self.last_done and (today - self.last_done).days > 1:
                # Streak broken — reset
                self.streak_count = 1
            else:
                # First time or no previous data
                self.streak_count = 1
        elif self.frequency == self.Frequency.WEEKLY:
            if self.last_done and (today - self.last_done).days <= 7:
                self.streak_count += 1
            elif self.last_done and (today - self.last_done).days > 7:
                self.streak_count = 1
            else:
                self.streak_count = 1

        # Update longest streak
        if self.streak_count > self.longest_streak:
            self.longest_streak = self.streak_count

        self.last_done = today
        self.save()
        return True, f'🔥 Streak: {self.streak_count} days!'

    def check_streak_broken(self):
        """Check if streak is broken (called by scheduler). Returns True if broken."""
        if not self.last_done:
            return False

        today = timezone.now().date()
        gap = (today - self.last_done).days

        if self.frequency == self.Frequency.DAILY and gap > 1 and self.streak_count > 0:
            old_streak = self.streak_count
            self.streak_count = 0
            self.save()
            return True
        elif self.frequency == self.Frequency.WEEKLY and gap > 7 and self.streak_count > 0:
            old_streak = self.streak_count
            self.streak_count = 0
            self.save()
            return True
        return False

    @property
    def badges(self):
        """Return earned badge emojis based on longest streak."""
        earned = []
        if self.longest_streak >= 7:
            earned.append(('🏅', '7-Day Warrior'))
        if self.longest_streak >= 14:
            earned.append(('⭐', '14-Day Star'))
        if self.longest_streak >= 30:
            earned.append(('🏆', '30-Day Champion'))
        if self.longest_streak >= 60:
            earned.append(('💎', '60-Day Diamond'))
        if self.longest_streak >= 90:
            earned.append(('👑', '90-Day Legend'))
        return earned

    @property
    def is_done_today(self):
        return self.last_done == timezone.now().date()


class Goal(models.Model):
    """User goal linked to habits with progress tracking."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    target_date = models.DateField()
    progress_percent = models.IntegerField(
        default=0,
        help_text='Progress from 0 to 100',
    )
    linked_habits = models.ManyToManyField(
        Habit, blank=True, related_name='goals',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goals',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'goals'
        ordering = ['target_date']

    def __str__(self):
        return f'{self.title} ({self.progress_percent}%)'

    def update_progress_from_habits(self):
        """Recalculate progress based on linked habit streaks."""
        habits = self.linked_habits.all()
        if not habits.exists():
            return

        # Calculate average streak completion as percentage
        total_days = (self.target_date - self.created_at.date()).days or 1
        avg_streak = sum(h.streak_count for h in habits) / habits.count()
        self.progress_percent = min(100, int((avg_streak / total_days) * 100))
        self.save()

    @property
    def days_remaining(self):
        return (self.target_date - timezone.now().date()).days

    @property
    def is_overdue(self):
        return self.target_date < timezone.now().date() and self.progress_percent < 100

    @property
    def progress_color(self):
        if self.progress_percent >= 75:
            return '#22c55e'
        elif self.progress_percent >= 50:
            return '#eab308'
        elif self.progress_percent >= 25:
            return '#f97316'
        else:
            return '#ef4444'
