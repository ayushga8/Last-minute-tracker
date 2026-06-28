import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from .utils import (
    get_google_calendar_flow,
    get_calendar_service,
    create_calendar_event,
    fetch_calendar_events,
)

logger = logging.getLogger(__name__)


@login_required
def calendar_auth_view(request):
    """Initiate Google Calendar OAuth2 flow."""
    try:
        flow = get_google_calendar_flow(request)
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
        )
        request.session['calendar_oauth_state'] = state
        return redirect(authorization_url)
    except Exception as e:
        messages.error(request, f'Failed to initiate Calendar authorization: {str(e)}')
        return redirect('settings')


@login_required
def calendar_callback_view(request):
    """Handle Google Calendar OAuth2 callback."""
    try:
        flow = get_google_calendar_flow(request)
        flow.fetch_token(authorization_response=request.build_absolute_uri())

        credentials = flow.credentials
        request.user.calendar_tokens = {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'scopes': credentials.scopes,
        }
        request.user.save(update_fields=['calendar_tokens'])

        messages.success(request, '✅ Google Calendar connected successfully!')
    except Exception as e:
        logger.error(f'Calendar OAuth callback error: {e}')
        messages.error(request, f'Calendar authorization failed: {str(e)}')

    return redirect('settings')


@login_required
def calendar_disconnect_view(request):
    """Disconnect Google Calendar."""
    if request.method == 'POST':
        request.user.calendar_tokens = None
        request.user.save(update_fields=['calendar_tokens'])
        messages.success(request, 'Google Calendar disconnected.')
    return redirect('settings')


@login_required
def sync_tasks_to_calendar_view(request):
    """Push all tasks with deadlines to Google Calendar."""
    from tasks.models import Task

    service = get_calendar_service(request.user)
    if not service:
        messages.error(request, 'Google Calendar not connected. Please authorize first.')
        return redirect('settings')

    tasks = Task.objects.filter(
        created_by=request.user,
        status__in=['pending', 'in_progress'],
        google_event_id__isnull=True,
    )

    synced = 0
    for task in tasks:
        event_id = create_calendar_event(service, task)
        if event_id:
            task.google_event_id = event_id
            task.save(update_fields=['google_event_id'])
            synced += 1

    messages.success(request, f'📅 Synced {synced} tasks to Google Calendar!')
    return redirect('calendar_view')


@login_required
def import_calendar_events_view(request):
    """Import Google Calendar events as tasks."""
    from tasks.models import Task

    service = get_calendar_service(request.user)
    if not service:
        messages.error(request, 'Google Calendar not connected.')
        return redirect('settings')

    events = fetch_calendar_events(service)
    imported = 0

    for event in events:
        event_id = event.get('id')
        # Skip if already imported
        if Task.objects.filter(google_event_id=event_id, created_by=request.user).exists():
            continue

        start = event.get('start', {})
        deadline_str = start.get('dateTime') or start.get('date')
        if not deadline_str:
            continue

        # Parse deadline
        from django.utils.dateparse import parse_datetime, parse_date
        import datetime as dt

        deadline = parse_datetime(deadline_str)
        if not deadline:
            date = parse_date(deadline_str)
            if date:
                deadline = timezone.make_aware(
                    dt.datetime.combine(date, dt.time(23, 59)),
                    timezone.get_current_timezone(),
                )
            else:
                continue

        Task.objects.create(
            title=event.get('summary', 'Imported Event'),
            description=event.get('description', ''),
            deadline=deadline,
            category='Calendar Import',
            google_event_id=event_id,
            created_by=request.user,
        )
        imported += 1

    messages.success(request, f'📥 Imported {imported} events from Google Calendar!')
    return redirect('calendar_view')


@login_required
def calendar_view(request):
    """Calendar view page with FullCalendar.js."""
    from tasks.models import Task

    tasks = Task.objects.filter(created_by=request.user).exclude(status='completed')
    has_calendar = bool(request.user.calendar_tokens)

    return render(request, 'calendar_sync/calendar_view.html', {
        'tasks': tasks,
        'has_calendar': has_calendar,
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
