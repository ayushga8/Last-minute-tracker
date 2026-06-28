"""
Google Calendar API utility functions.
Handles OAuth2 flow, token management, and Calendar event CRUD.
"""
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.conf import settings

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_google_calendar_flow(request):
    """Create an OAuth2 flow for Google Calendar authorization."""
    client_config = {
        'web': {
            'client_id': settings.GOOGLE_CALENDAR_CLIENT_ID,
            'client_secret': settings.GOOGLE_CALENDAR_CLIENT_SECRET,
            'redirect_uris': [request.build_absolute_uri('/calendar/callback/')],
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=request.build_absolute_uri('/calendar/callback/'),
    )
    return flow


def get_calendar_service(user):
    """Build Google Calendar service from stored user tokens."""
    if not user.calendar_tokens:
        return None

    try:
        creds = Credentials(
            token=user.calendar_tokens.get('access_token'),
            refresh_token=user.calendar_tokens.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.GOOGLE_CALENDAR_CLIENT_ID,
            client_secret=settings.GOOGLE_CALENDAR_CLIENT_SECRET,
        )

        # Refresh if expired
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            # Update stored tokens
            user.calendar_tokens['access_token'] = creds.token
            user.save(update_fields=['calendar_tokens'])

        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f'Failed to build Calendar service for {user.email}: {e}')
        return None


def create_calendar_event(service, task):
    """Create a Google Calendar event from a Task."""
    event = {
        'summary': task.title,
        'description': task.description or f'Priority: {task.get_priority_tag_display()}\nCategory: {task.category}',
        'start': {
            'dateTime': task.deadline.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'end': {
            'dateTime': (task.deadline + __import__('datetime').timedelta(hours=task.estimated_hours)).isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'colorId': {
            'critical': '11',  # Red
            'high': '6',      # Orange
            'medium': '5',    # Yellow
            'low': '10',      # Green
        }.get(task.priority_tag, '0'),
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 60},
                {'method': 'popup', 'minutes': 30},
            ],
        },
    }

    try:
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
        ).execute()
        return created_event.get('id')
    except Exception as e:
        logger.error(f'Failed to create calendar event: {e}')
        return None


def update_calendar_event(service, event_id, task):
    """Update an existing Google Calendar event."""
    event = {
        'summary': task.title,
        'description': task.description or f'Priority: {task.get_priority_tag_display()}',
        'start': {
            'dateTime': task.deadline.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'end': {
            'dateTime': (task.deadline + __import__('datetime').timedelta(hours=task.estimated_hours)).isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
    }

    try:
        service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
        ).execute()
        return True
    except Exception as e:
        logger.error(f'Failed to update calendar event {event_id}: {e}')
        return False


def delete_calendar_event(service, event_id):
    """Delete a Google Calendar event."""
    try:
        service.events().delete(
            calendarId='primary',
            eventId=event_id,
        ).execute()
        return True
    except Exception as e:
        logger.error(f'Failed to delete calendar event {event_id}: {e}')
        return False


def fetch_calendar_events(service, time_min=None, time_max=None, max_results=50):
    """Fetch events from user's primary Google Calendar."""
    from django.utils import timezone
    import datetime

    if not time_min:
        time_min = timezone.now().isoformat()
    if not time_max:
        time_max = (timezone.now() + datetime.timedelta(days=30)).isoformat()

    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime',
        ).execute()
        return events_result.get('items', [])
    except Exception as e:
        logger.error(f'Failed to fetch calendar events: {e}')
        return []
