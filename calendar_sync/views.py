import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

logger = logging.getLogger(__name__)


@login_required
def calendar_view(request):
    """Calendar view page with FullCalendar.js."""
    from tasks.models import Task

    tasks = Task.objects.filter(created_by=request.user).exclude(status='completed')

    return render(request, 'calendar_sync/calendar_view.html', {
        'tasks': tasks,
    })


@login_required
def calendar_events_json(request):
    """AJAX endpoint returning task events for FullCalendar."""
    from tasks.models import Task

    tasks = Task.objects.filter(created_by=request.user)
    events = []
    for task in tasks:
        events.append({
            'id': task.id,
            'title': task.title,
            'start': task.deadline.isoformat(),
            'end': (task.deadline + timezone.timedelta(hours=task.estimated_hours)).isoformat(),
            'color': task.priority_color,
            'url': f'/tasks/{task.id}/',
            'extendedProps': {
                'priority': task.priority_tag,
                'status': task.status,
                'category': task.category,
            },
        })

    return JsonResponse(events, safe=False)
