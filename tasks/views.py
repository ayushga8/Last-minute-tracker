import json
import logging
import threading
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from .models import Task, AIRecommendation
from .forms import TaskForm, TaskFilterForm
from .ai_helper import get_ai_prioritization, get_priority_preview

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    """Main dashboard with task summary, AI suggestions, habits, and upcoming deadlines."""
    user = request.user
    now = timezone.now()

    # Task stats
    all_tasks = Task.objects.filter(created_by=user)
    total_tasks = all_tasks.count()
    overdue_tasks = all_tasks.filter(deadline__lt=now).exclude(status='completed').count()
    completed_today = all_tasks.filter(
        status='completed',
        updated_at__date=now.date(),
    ).count()
    in_progress = all_tasks.filter(status='in_progress').count()

    # Upcoming deadlines (next 7 days)
    upcoming = all_tasks.filter(
        deadline__gte=now,
        deadline__lte=now + timezone.timedelta(days=7),
    ).exclude(status='completed').order_by('deadline')[:5]

    # AI recommendations
    recommendations = AIRecommendation.objects.filter(user=user)[:5]

    # Habit streaks (imported here to avoid circular imports)
    from habits.models import Habit
    habits = Habit.objects.filter(user=user).order_by('-streak_count')[:5]

    # Unread notifications
    from scheduler.models import Notification
    unread_notifications = Notification.objects.filter(
        user=user, read=False
    ).order_by('-created_at')[:5]

    context = {
        'total_tasks': total_tasks,
        'overdue_tasks': overdue_tasks,
        'completed_today': completed_today,
        'in_progress': in_progress,
        'upcoming_tasks': upcoming,
        'recommendations': recommendations,
        'habits': habits,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'dashboard.html', context)


@login_required
def task_list_view(request):
    """List all tasks with filtering and sorting."""
    tasks = Task.objects.filter(created_by=request.user)
    filter_form = TaskFilterForm(request.GET)

    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        priority = filter_form.cleaned_data.get('priority')
        category = filter_form.cleaned_data.get('category')
        sort = filter_form.cleaned_data.get('sort')

        if status:
            tasks = tasks.filter(status=status)
        if priority:
            tasks = tasks.filter(priority_tag=priority)
        if category:
            tasks = tasks.filter(category__icontains=category)
        if sort:
            tasks = tasks.order_by(sort)
        else:
            tasks = tasks.order_by('deadline', '-priority_score')

    # Recalculate scores for display
    for task in tasks:
        task.calculate_priority_score()

    context = {
        'tasks': tasks,
        'filter_form': filter_form,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_create_view(request):
    """Create a new task with optional AI priority preview."""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            # Trigger AI prioritization in background thread
            try:
                t = threading.Thread(target=get_ai_prioritization, args=(request.user,))
                t.daemon = True
                t.start()
            except Exception as e:
                logger.error(f"Failed to start AI thread: {e}")
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('task_list')
    else:
        form = TaskForm()

    return render(request, 'tasks/task_form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
def task_edit_view(request, pk):
    """Edit an existing task."""
    task = get_object_or_404(Task, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            # Trigger AI prioritization in background thread
            try:
                t = threading.Thread(target=get_ai_prioritization, args=(request.user,))
                t.daemon = True
                t.start()
            except Exception as e:
                logger.error(f"Failed to start AI thread: {e}")
            messages.success(request, f'Task "{task.title}" updated!')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)

    return render(request, 'tasks/task_form.html', {
        'form': form,
        'task': task,
        'is_edit': True,
    })


@login_required
def task_delete_view(request, pk):
    """Delete a task."""
    task = get_object_or_404(Task, pk=pk, created_by=request.user)

    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('task_list')

    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_detail_view(request, pk):
    """View task details."""
    task = get_object_or_404(Task, pk=pk, created_by=request.user)
    task.calculate_priority_score()
    recommendations = AIRecommendation.objects.filter(user=request.user, task=task)

    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'recommendations': recommendations,
    })


@login_required
def task_complete_view(request, pk):
    """Mark a task as completed."""
    task = get_object_or_404(Task, pk=pk, created_by=request.user)
    task.status = Task.Status.COMPLETED
    task.save()
    messages.success(request, f'🎉 "{task.title}" completed!')
    return redirect(request.META.get('HTTP_REFERER', 'task_list'))


@login_required
def ai_refresh_view(request):
    """Manually trigger AI re-prioritization."""
    try:
        recommendations = get_ai_prioritization(request.user)
        if recommendations:
            messages.success(request, '✨ AI suggestions refreshed!')
        else:
            messages.info(request, 'No tasks to analyze or Gemini API not configured.')
    except Exception as e:
        messages.error(request, f'AI refresh failed: {str(e)}')

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def ai_preview_view(request):
    """AJAX endpoint for AI priority preview on task creation."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            preview = get_priority_preview(data)
            return JsonResponse({'preview': preview or 'Unable to generate preview.'})
        except Exception as e:
            return JsonResponse({'preview': f'Preview unavailable: {str(e)}'})
    return JsonResponse({'error': 'POST required'}, status=400)
