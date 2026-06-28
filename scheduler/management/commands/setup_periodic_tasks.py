"""
Management command to run periodic tasks.
Usage: python manage.py setup_periodic_tasks
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run scheduler periodic tasks manually'

    def handle(self, *args, **options):
        from scheduler.tasks import (
            check_deadline_reminders,
            send_daily_digest,
            check_broken_streaks,
        )

        self.stdout.write('Running periodic tasks...\n')

        check_deadline_reminders()
        self.stdout.write(self.style.SUCCESS('  ✓ Deadline reminders checked'))

        check_broken_streaks()
        self.stdout.write(self.style.SUCCESS('  ✓ Broken streaks checked'))

        self.stdout.write(self.style.SUCCESS('\nAll tasks completed! ✨'))
