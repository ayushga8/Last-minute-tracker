from django.urls import path
from . import views

urlpatterns = [
    path('', views.habit_list_view, name='habit_list'),
    path('<int:pk>/done/', views.habit_mark_done_view, name='habit_mark_done'),
    path('<int:pk>/delete/', views.habit_delete_view, name='habit_delete'),
    path('goals/', views.goal_list_view, name='goal_list'),
    path('goals/<int:pk>/progress/', views.goal_update_progress_view, name='goal_update_progress'),
    path('goals/<int:pk>/delete/', views.goal_delete_view, name='goal_delete'),
]
