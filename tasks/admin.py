from django.contrib import admin
from .models import Task, AIRecommendation


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'deadline', 'priority_tag', 'status', 'priority_score')
    list_filter = ('status', 'priority_tag', 'category')
    search_fields = ('title', 'description')
    ordering = ('deadline',)
    readonly_fields = ('priority_score', 'priority_tag', 'created_at', 'updated_at')


@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'recommendation_type', 'generated_at')
    list_filter = ('recommendation_type',)
    readonly_fields = ('generated_at',)
