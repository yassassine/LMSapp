from django import forms
from .models import Course, Lesson, Resource, Activity
from LMSapp.enrollment.models import Child
from .models import UserStatus

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'category', 'description', 'status', 
            'level', 'duration', 'featured_image'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'title': 'Titre du cours',
            'category': 'Catégorie',
            'description': 'Description',
            'status': 'Statut',
            'level': 'Niveau',
            'duration': 'Durée estimée (heures)',
            'featured_image': 'Image mise en avant',
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['course', 'title', 'content', 'order', 'video_url']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6}),
        }
        labels = {
            'course': 'Cours associé',
            'title': 'Titre de la leçon',
            'content': 'Contenu',
            'order': 'Ordre',
            'video_url': 'URL de la vidéo (optionnel)',
        }

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['lesson', 'title', 'resource_type', 'file', 'external_link', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'lesson': 'Leçon associée',
            'title': 'Titre de la ressource',
            'resource_type': 'Type de ressource',
            'file': 'Fichier',
            'external_link': 'Lien externe',
            'description': 'Description',
        }

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['lesson', 'title', 'activity_type', 'instructions', 'max_score', 'due_date']
        widgets = {
            'instructions': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'lesson': 'Leçon associée',
            'title': 'Titre de l\'activité',
            'activity_type': 'Type d\'activité',
            'instructions': 'Instructions',
            'max_score': 'Score maximal',
            'due_date': 'Date limite (optionnel)',
        }


class EnrollmentFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'All Statuses')] + list(UserStatus.STATUS_CHOICES)
    AGE_GROUPS = [('', 'All Groups')] + Child.AGE_GROUP_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label="Status"
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="From"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="To"
    )
    age_group = forms.ChoiceField(
        choices=AGE_GROUPS,
        required=False,
        label="Age Group"
    )
    search = forms.CharField(
        required=False,
        label="Search Child/Parent",
        widget=forms.TextInput(attrs={'placeholder': 'Name...'})
    )