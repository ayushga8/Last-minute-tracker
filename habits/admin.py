from django.contrib import admin
from .models import Habit, Goal


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'frequency', 'streak_count', 'longest_streak', 'last_done')
    list_filter = ('frequency', 'user')
    search_fields = ('name',)


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'target_date', 'progress_percent')
    list_filter = ('user',)
    search_fields = ('title',)
    filter_horizontal = ('linked_habits',)
