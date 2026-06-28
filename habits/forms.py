from django import forms
from .models import Habit, Goal


class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['name', 'description', 'frequency']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Morning meditation',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input form-textarea',
                'placeholder': 'Why this habit matters to you...',
                'rows': 3,
            }),
            'frequency': forms.Select(attrs={
                'class': 'form-input',
            }),
        }


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'description', 'target_date', 'linked_habits']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Run a marathon',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input form-textarea',
                'placeholder': 'Describe your goal...',
                'rows': 3,
            }),
            'target_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
            }),
            'linked_habits': forms.CheckboxSelectMultiple(attrs={
                'class': 'habit-checkbox',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['linked_habits'].queryset = Habit.objects.filter(user=user)
