"""
Periodic tasks for the smart scheduler.
These run as simple functions (no Celery required).
Can be triggered via management commands or cron jobs.
"""
import logging
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


def check_deadline_reminders():
    """Find tasks with deadlines approaching and send reminders."""
    from tasks.models import Task
    from scheduler.models import Notification

    now = timezone.now()
    one_hour = now + timezone.timedelta(hours=1)
    twenty_four_hours = now + timezone.timedelta(hours=24)

    urgent_tasks = Task.objects.filter(
        deadline__gte=now,
        deadline__lte=one_hour,
        status__in=['pending', 'in_progress'],
    ).select_related('created_by')

    for task in urgent_tasks:
        exists = Notification.objects.filter(
            user=task.created_by,
            task=task,
            message__contains='⏰ URGENT',
            created_at__gte=now - timezone.timedelta(hours=2),
        ).exists()

        if not exists:
            msg = f'⏰ URGENT: "{task.title}" is due in less than 1 hour!'
            _create_and_send_notification(task.created_by, task, msg)

    upcoming_tasks = Task.objects.filter(
        deadline__gte=one_hour,
        deadline__lte=twenty_four_hours,
        status__in=['pending', 'in_progress'],
    ).select_related('created_by')

    for task in upcoming_tasks:
        exists = Notification.objects.filter(
            user=task.created_by,
            task=task,
            message__contains='📅 Reminder',
            created_at__gte=now - timezone.timedelta(hours=25),
        ).exists()

        if not exists:
            hours_left = (task.deadline - now).total_seconds() / 3600
            msg = f'📅 Reminder: "{task.title}" is due in {hours_left:.0f} hours.'
            _create_and_send_notification(task.created_by, task, msg)

    logger.info(f'Checked deadline reminders: {urgent_tasks.count()} urgent, {upcoming_tasks.count()} upcoming')


def send_daily_digest():
    """Send each user their priority-sorted task list for the day."""
    from tasks.models import Task
    from scheduler.models import Notification

    now = timezone.now()
    end_of_day = now.replace(hour=23, minute=59, second=59)

    for user in User.objects.filter(is_active=True, notification_email=True):
        today_tasks = Task.objects.filter(
            created_by=user,
            deadline__lte=end_of_day,
            status__in=['pending', 'in_progress'],
        ).order_by('-priority_score')

        if not today_tasks.exists():
            continue

        task_lines = []
        for i, task in enumerate(today_tasks, 1):
            tag_emoji = {
                'critical': '🔴', 'high': '🟠',
                'medium': '🟡', 'low': '🟢',
            }.get(task.priority_tag, '⚪')
            task_lines.append(
                f'{i}. {tag_emoji} {task.title} — '
                f'Due: {task.deadline.strftime("%I:%M %p")} | '
                f'Priority: {task.get_priority_tag_display()}'
            )

        msg = f"🌅 Good morning! Here's your priority digest for today:\n\n"
        msg += '\n'.join(task_lines)
        msg += f'\n\nTotal: {today_tasks.count()} tasks. You\'ve got this! 💪'

        _create_and_send_notification(user, None, msg)

    logger.info('Daily digest sent to all active users')


def send_weekly_summary():
    """Send habit streak + goal progress summary."""
    from habits.models import Habit, Goal
    from scheduler.models import Notification

    for user in User.objects.filter(is_active=True, notification_email=True):
        habits = Habit.objects.filter(user=user)
        goals = Goal.objects.filter(user=user)

        if not habits.exists() and not goals.exists():
            continue

        msg = '📊 **Weekly Progress Summary**\n\n'

        if habits.exists():
            msg += '🔥 **Habit Streaks:**\n'
            for habit in habits:
                badge_text = ' '.join([b[0] for b in habit.badges]) if habit.badges else ''
                msg += f'  • {habit.name}: {habit.streak_count} day streak {badge_text}\n'

        if goals.exists():
            msg += '\n🎯 **Goal Progress:**\n'
            for goal in goals:
                bar = '█' * (goal.progress_percent // 10) + '░' * (10 - goal.progress_percent // 10)
                msg += f'  • {goal.title}: [{bar}] {goal.progress_percent}%\n'

        msg += '\nKeep pushing forward! 🚀'

        _create_and_send_notification(user, None, msg)

    logger.info('Weekly summary sent')


def check_broken_streaks():
    """Check for broken habit streaks and send encouragement."""
    from habits.models import Habit
    from scheduler.models import Notification

    for habit in Habit.objects.filter(streak_count__gt=0).select_related('user'):
        if habit.check_streak_broken():
            msg = (
                f'💔 Your streak for "{habit.name}" was broken. '
                f'Don\'t worry — every champion has setbacks! '
                f'Your best streak was {habit.longest_streak} days. '
                f'Start fresh today! 🌱'
            )
            _create_and_send_notification(habit.user, None, msg)
            logger.info(f'Streak broken notification sent for habit: {habit.name} (user: {habit.user.email})')


def _create_and_send_notification(user, task, message):
    """Create an in-app notification and optionally send an email."""
    from scheduler.models import Notification

    notification = Notification.objects.create(
        user=user,
        task=task,
        message=message,
        notification_type='both' if user.notification_email else 'in_app',
        sent=False,
    )

    if user.notification_email and user.email:
        try:
            send_mail(
                subject='🔔 Life Saver Notification',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            notification.sent = True
            notification.save()
        except Exception as e:
            logger.error(f'Failed to send notification email to {user.email}: {e}')

    return notification
