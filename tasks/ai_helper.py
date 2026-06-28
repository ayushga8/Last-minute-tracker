"""
Gemini AI integration for task prioritization.
Uses the new google-genai SDK (replaces deprecated google-generativeai).
"""
import json
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_client():
    """Initialize the Gemini client."""
    try:
        from google import genai
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning('GEMINI_API_KEY not configured')
            return None
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f'Failed to initialize Gemini client: {e}')
        return None


def get_ai_prioritization(user):
    """
    Send user's task list to Gemini and get prioritized recommendations.
    Returns a list of suggestion dicts.
    """
    from .models import Task, AIRecommendation

    client = _get_client()
    if not client:
        return []

    # Get active tasks
    tasks = Task.objects.filter(
        created_by=user,
        status__in=['pending', 'in_progress'],
    ).order_by('deadline')

    if not tasks.exists():
        return []

    # Build context for Gemini
    now = timezone.now()
    task_descriptions = []
    for t in tasks:
        hours_left = max(0, (t.deadline - now).total_seconds() / 3600)
        task_descriptions.append(
            f"- \"{t.title}\" | Category: {t.category} | "
            f"Deadline: {t.deadline.strftime('%Y-%m-%d %H:%M')} | "
            f"Hours left: {hours_left:.1f}h | "
            f"Estimated work: {t.estimated_hours}h | "
            f"Importance: {t.importance_weight}/10 | "
            f"Status: {t.get_status_display()}"
        )

    task_context = '\n'.join(task_descriptions)

    prompt = f"""You are a productivity AI assistant. Analyze the following task list and provide:

1. **Priority Ranking**: Rank tasks from most to least urgent, considering deadlines, importance, and estimated work time.
2. **Time Block Suggestions**: Suggest an optimal schedule for today, breaking tasks into focused work blocks.
3. **Clash Warnings**: Identify any deadline conflicts or tasks that can't realistically be completed in time.
4. **Quick Tips**: 1-2 actionable productivity tips based on the workload.

Current date/time: {now.strftime('%Y-%m-%d %H:%M')}

Tasks:
{task_context}

Respond in this JSON format:
{{
    "priority_ranking": ["task title 1", "task title 2", ...],
    "time_blocks": [
        {{"time": "9:00-11:00", "task": "task title", "reason": "why this slot"}},
        ...
    ],
    "clash_warnings": ["warning message 1", ...],
    "tips": ["tip 1", "tip 2"]
}}
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )

        response_text = response.text.strip()
        # Clean markdown code fences if present
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])

        suggestions = json.loads(response_text)

        # Clear old recommendations for this user
        AIRecommendation.objects.filter(user=user).delete()

        saved_recommendations = []

        # Save priority ranking
        if suggestions.get('priority_ranking'):
            ranking_text = '**Recommended Priority Order:**\n'
            for i, title in enumerate(suggestions['priority_ranking'], 1):
                ranking_text += f'{i}. {title}\n'
            rec = AIRecommendation.objects.create(
                user=user,
                suggestion_text=ranking_text,
                recommendation_type='ranking',
            )
            saved_recommendations.append(rec)

        # Save time blocks
        if suggestions.get('time_blocks'):
            blocks_text = '**Suggested Schedule:**\n'
            for block in suggestions['time_blocks']:
                blocks_text += f"⏰ {block['time']} → {block['task']}\n   _{block.get('reason', '')}_\n"
            rec = AIRecommendation.objects.create(
                user=user,
                suggestion_text=blocks_text,
                recommendation_type='time_block',
            )
            saved_recommendations.append(rec)

        # Save clash warnings
        if suggestions.get('clash_warnings'):
            for warning in suggestions['clash_warnings']:
                rec = AIRecommendation.objects.create(
                    user=user,
                    suggestion_text=f'⚠️ {warning}',
                    recommendation_type='clash',
                )
                saved_recommendations.append(rec)

        # Save tips
        if suggestions.get('tips'):
            tips_text = '**Productivity Tips:**\n'
            for tip in suggestions['tips']:
                tips_text += f'💡 {tip}\n'
            rec = AIRecommendation.objects.create(
                user=user,
                suggestion_text=tips_text,
                recommendation_type='general',
            )
            saved_recommendations.append(rec)

        return saved_recommendations

    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse Gemini response as JSON: {e}')
        # Save raw response as general suggestion
        try:
            AIRecommendation.objects.filter(user=user).delete()
            rec = AIRecommendation.objects.create(
                user=user,
                suggestion_text=response.text[:2000],
                recommendation_type='general',
            )
            return [rec]
        except Exception:
            return []
    except Exception as e:
        logger.error(f'Gemini API error: {e}')
        return []


def get_priority_preview(task_data):
    """
    Quick AI assessment for a new task being created.
    Returns a short priority suggestion string.
    """
    client = _get_client()
    if not client:
        return None

    prompt = f"""Given this task, provide a one-line priority assessment:
Title: {task_data.get('title', 'Untitled')}
Deadline: {task_data.get('deadline', 'Not set')}
Category: {task_data.get('category', 'General')}
Estimated hours: {task_data.get('estimated_hours', 1)}
Importance (1-10): {task_data.get('importance_weight', 5)}

Respond with ONLY a single short sentence about its priority level and a brief tip."""

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f'Gemini preview error: {e}')
        return None
