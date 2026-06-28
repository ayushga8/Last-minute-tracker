"""
Management command to register Celery Beat periodic tasks.
Run: python manage.py setup_periodic_tasks
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Setup Celery Beat periodic tasks for the scheduler'

    def handle(self, *args, **options):
        self.stdout.write('Setting up periodic tasks...\n')

        # --- Interval Schedules ---
        hourly, _ = IntervalSchedule.objects.get_or_create(
            every=1, period=IntervalSchedule.HOURS,
        )

        # --- Crontab Schedules ---
        # Daily at 8:00 AM IST
        daily_8am, _ = CrontabSchedule.objects.get_or_create(
            minute='0', hour='8',
            day_of_week='*', day_of_month='*', month_of_year='*',
            timezone='Asia/Kolkata',
        )

        # Daily at 2:00 AM (for streak checks)
        daily_2am, _ = CrontabSchedule.objects.get_or_create(
            minute='0', hour='2',
            day_of_week='*', day_of_month='*', month_of_year='*',
            timezone='Asia/Kolkata',
        )

        # Weekly on Sunday at 9:00 AM
        weekly_sunday, _ = CrontabSchedule.objects.get_or_create(
            minute='0', hour='9',
            day_of_week='0',  # Sunday
            day_of_month='*', month_of_year='*',
            timezone='Asia/Kolkata',
        )

        # --- Periodic Tasks ---
        PeriodicTask.objects.update_or_create(
            name='Check Deadline Reminders',
            defaults={
                'task': 'scheduler.check_deadline_reminders',
                'interval': hourly,
                'enabled': True,
            },
        )
        self.stdout.write(self.style.SUCCESS('  ✓ Deadline reminders (hourly)'))

        PeriodicTask.objects.update_or_create(
            name='Send Daily Digest',
            defaults={
                'task': 'scheduler.send_daily_digest',
                'crontab': daily_8am,
                'enabled': True,
            },
        )
        self.stdout.write(self.style.SUCCESS('  ✓ Daily digest (8:00 AM)'))

        PeriodicTask.objects.update_or_create(
            name='Check Broken Streaks',
            defaults={
                'task': 'scheduler.check_broken_streaks',
                'crontab': daily_2am,
                'enabled': True,
            },
        )
        self.stdout.write(self.style.SUCCESS('  ✓ Broken streak check (2:00 AM)'))

        PeriodicTask.objects.update_or_create(
            name='Send Weekly Summary',
            defaults={
                'task': 'scheduler.send_weekly_summary',
                'crontab': weekly_sunday,
                'enabled': True,
            },
        )
        self.stdout.write(self.style.SUCCESS('  ✓ Weekly summary (Sunday 9:00 AM)'))

        self.stdout.write(self.style.SUCCESS('\nAll periodic tasks configured! ✨'))
