from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    """Form for creating and editing tasks."""

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'deadline', 'category',
            'estimated_hours', 'importance_weight', 'status',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'What needs to be done?',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input form-textarea',
                'placeholder': 'Add details, notes, links...',
                'rows': 4,
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-input',
                'type': 'datetime-local',
            }, format='%Y-%m-%dT%H:%M'),
            'category': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Work, Study, Personal',
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0.5',
                'step': '0.5',
                'placeholder': '1.0',
            }),
            'importance_weight': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'max': '10',
                'placeholder': '5',
            }),
            'status': forms.Select(attrs={
                'class': 'form-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].required = False
        self.fields['deadline'].input_formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
        ]


class TaskFilterForm(forms.Form):
    """Form for filtering and sorting the task list."""
    STATUS_CHOICES = [('', 'All Statuses')] + list(Task.Status.choices)
    PRIORITY_CHOICES = [('', 'All Priorities')] + list(Task.PriorityTag.choices)
    SORT_CHOICES = [
        ('deadline', 'Deadline (soonest)'),
        ('-deadline', 'Deadline (latest)'),
        ('-priority_score', 'Priority (highest)'),
        ('priority_score', 'Priority (lowest)'),
        ('-created_at', 'Newest first'),
        ('created_at', 'Oldest first'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-input filter-select'}),
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-input filter-select'}),
    )
    category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input filter-select',
            'placeholder': 'Filter by category',
        }),
    )
    sort = forms.ChoiceField(
        choices=SORT_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-input filter-select'}),
    )
