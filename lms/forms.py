# lms/forms.py

from django import forms
from .models import Resource, InteractiveActivity, ChildProgress,AssignmentSubmission

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'resource_type', 'file', 'url', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ActivityForm(forms.ModelForm):
    class Meta:
        model = InteractiveActivity
        fields = ['title', 'activity_type', 'description', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ProgressForm(forms.ModelForm):
    class Meta:
        model = ChildProgress
        fields = ['overall_progress', 'resources_viewed', 'activities_completed']


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['child', 'comments']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Ajoutez des notes pour l\'enseignant...'}),
        }
    
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': False}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_parent:
            self.fields['child'].queryset = user.children.all()