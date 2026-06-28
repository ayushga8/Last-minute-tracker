from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .models import Habit, Goal
from .forms import HabitForm, GoalForm


@login_required
def habit_list_view(request):
    """List all habits with streak info and mark-done button."""
    habits = Habit.objects.filter(user=request.user)

    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
            messages.success(request, f'Habit "{habit.name}" created!')
            return redirect('habit_list')
    else:
        form = HabitForm()

    context = {
        'habits': habits,
        'form': form,
    }
    return render(request, 'habits/habit_list.html', context)


@login_required
def habit_mark_done_view(request, pk):
    """Mark a habit as done (supports AJAX)."""
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    success, message = habit.mark_done()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': success,
            'message': message,
            'streak': habit.streak_count,
            'badges': habit.badges,
            'is_done_today': habit.is_done_today,
        })

    if success:
        messages.success(request, message)
    else:
        messages.info(request, message)
    return redirect('habit_list')


@login_required
def habit_delete_view(request, pk):
    """Delete a habit."""
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    if request.method == 'POST':
        name = habit.name
        habit.delete()
        messages.success(request, f'Habit "{name}" deleted.')
    return redirect('habit_list')


@login_required
def goal_list_view(request):
    """List all goals with progress bars."""
    goals = Goal.objects.filter(user=request.user)

    # Recalculate progress for goals with linked habits
    for goal in goals:
        goal.update_progress_from_habits()

    if request.method == 'POST':
        form = GoalForm(request.POST, user=request.user)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            form.save_m2m()
            messages.success(request, f'Goal "{goal.title}" created!')
            return redirect('goal_list')
    else:
        form = GoalForm(user=request.user)

    context = {
        'goals': goals,
        'form': form,
    }
    return render(request, 'habits/goal_list.html', context)


@login_required
def goal_update_progress_view(request, pk):
    """Manually update goal progress."""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    if request.method == 'POST':
        try:
            progress = int(request.POST.get('progress', 0))
            goal.progress_percent = max(0, min(100, progress))
            goal.save()
            messages.success(request, f'Goal progress updated to {goal.progress_percent}%!')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid progress value.')

    return redirect('goal_list')


@login_required
def goal_delete_view(request, pk):
    """Delete a goal."""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        title = goal.title
        goal.delete()
        messages.success(request, f'Goal "{title}" deleted.')
    return redirect('goal_list')
