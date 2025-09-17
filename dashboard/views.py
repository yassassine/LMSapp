from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from LMSapp.accounts.models import User
from LMSapp.communication.models import Message, Notification
from LMSapp.core.models import Event
from .models import ChildProgress, Reward
from LMSapp.lms.models import ActivityCategory, InteractiveActivity, Assignment
from django.utils import timezone
from datetime import timedelta
from LMSapp import core
# Create your views here.

def dashboard_home(request):
    return render(request, "dashboard/home.html")

@login_required
def parent_dashboard(request):
    # Récupérer le parent et ses enfants
    parent = request.user
    children = User.objects.filter(parent=parent)
    
    # Récupérer les données pour le tableau de bord
    context = {
        'parent': parent,
        'children_count': children.count(),
        'unread_notifications_count': Notification.objects.filter(user=parent, is_read=False).count(),
        'unread_messages_count': Message.objects.filter(recipient=parent, is_read=False).count(),
        'children': children,
        'selected_child': None,
    }
    
    # Filtrer par enfant si spécifié
    child_id = request.GET.get('child')
    if child_id:
        try:
            context['selected_child'] = User.objects.get(id=child_id, parent=parent)
        except User.DoesNotExist:
            pass
    
    # Compétences des enfants
    progress_categories = {
        'social': 'Compétences Sociales',
        'cognitive': 'Compétences Cognitives',
        'physical': 'Développement Physique',
        'emotional': 'Développement Émotionnel',
    }
    
    progress_data = {}
    for category, label in progress_categories.items():
        progress_data[category] = ChildProgress.objects.filter(
            child__in=children, 
            category=category
        ).order_by('skill')
    
    context['progress_data'] = progress_data
    
    # Activités récentes (des enfants du parent)
    context['recent_activities'] = ActivityCategory.objects.filter(
        participants__in=children
    ).distinct().order_by('-date')[:4]
    
    # Événements à venir
    context['upcoming_events'] = Event.objects.filter(
        models.Q(is_public=True) | models.Q(invited_users__in=[parent])
    ).distinct().order_by('date')[:5]
    
    # Messages récents
    context['recent_messages'] = Message.objects.filter(
        recipient=parent
    ).order_by('-sent_at')[:5]
    
    # Rappels importants
    context['important_reminders'] = Notification.objects.filter(
        user=parent,
        is_important=True,
        is_read=False
    ).order_by('-created_at')[:3]
    
    return render(request, 'dashboard/parent_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    teacher = request.user
    class_group = teacher.class_group
    
    # Récupérer les élèves de la classe
    students = User.objects.filter(class_group=class_group, role='CHILD')
    
    # Statistiques de base
    context = {
        'teacher': teacher,
        'students_count': students.count(),
        'unread_notifications_count': Notification.objects.filter(user=teacher, is_read=False).count(),
        'pending_assignments_count': Assignment.objects.filter(
            course__teacher=teacher,
            submissions__is_graded=False
        ).distinct().count(),
        'students': students.annotate(
            progress_percentage=models.Avg('progress__progress'),
            late_assignments=models.Count('assignment_submissions', filter=models.Q(assignment_submissions__is_late=True)),
        ).prefetch_related('parent'),
    }
    
    # Cours à venir (7 prochains jours)
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    context['upcoming_courses'] = core.models.Course.objects.filter(
        teacher=teacher,
        date__range=[today, next_week]
    ).order_by('date', 'start_time')[:5]
    
    # Devoirs à corriger
    context['pending_assignments'] = Assignment.objects.filter(
        course__teacher=teacher
    ).annotate(
        pending_count=models.Count('submissions', filter=models.Q(submissions__is_graded=False)),
        submission_count=models.Count('submissions'),
        submission_percentage=core.ExpressionWrapper(
            models.F('submission_count') * 100 / models.Count('course__students'),
            output_field=models.IntegerField()
        )
    ).filter(pending_count__gt=0).order_by('due_date')[:5]
    
    # Activités récentes
    context['recent_activities'] = ActivityCategory.objects.filter(
        teacher=teacher
    ).order_by('-date')[:3]
    
    # Événements à venir
    context['upcoming_events'] = Event.objects.filter(
        models.Q(organizer=teacher) | models.Q(invited_users=teacher)
    ).distinct().order_by('date')[:3]
    
    # Messages des parents
    context['recent_parent_messages'] = Message.objects.filter(
        recipient=teacher,
        sender__role='PARENT'
    ).order_by('-sent_at')[:5]
    
    # Statistiques de classe
    context['class_stats'] = {
        'avg_progress': core.Progress.objects.filter(
            child__class_group=class_group
        ).aggregate(avg=models.Avg('progress'))['avg'] or 0,
        'completed_assignments': core.AssignmentSubmission.objects.filter(
            assignment__course__teacher=teacher,
            is_submitted=True
        ).count(),
        'late_assignments': core.AssignmentSubmission.objects.filter(
            assignment__course__teacher=teacher,
            is_late=True
        ).count(),
        'activities_count': ActivityCategory.objects.filter(teacher=teacher).count(),
        'pending_corrections': core.AssignmentSubmission.objects.filter(
            assignment__course__teacher=teacher,
            is_graded=False
        ).count(),
        'absences': core.Attendance.objects.filter(
            child__class_group=class_group,
            status='ABSENT',
            date__month=today.month
        ).count(),
    }
    
    return render(request, 'dashboard/teacher_dashboard.html', context)

def child_dashboard(request):
    # Récupérer l'enfant connecté (supposons que le parent/enfant est authentifié)
    child = get_object_or_404(User, user=request.user)
    
    # Calculer les statistiques
    completed_activities = ActivityCategory.objects.filter(participants=child, is_completed=True).count()
    
    # Récupérer les données du tableau de bord
    recent_activities = ActivityCategory.objects.filter(
        participants=child
    ).order_by('-created_at')[:5]
    
    # Jeux éducatifs par catégorie
    math_games = InteractiveActivity.objects.filter(category='math', min_age__lte=child.age)[:3]
    language_games = InteractiveActivity.objects.filter(category='language', min_age__lte=child.age)[:3]
    science_games = InteractiveActivity.objects.filter(category='science', min_age__lte=child.age)[:3]
    
    # Récompenses débloquées
    unlocked_rewards = Reward.objects.filter(child=child)[:10]
    
    # Devoirs en attente
    pending_assignments = Assignment.objects.filter(
        assigned_to=child,
        is_submitted=False
    ).order_by('due_date')[:3]
    
    context = {
        'child': child,
        'completed_activities': completed_activities,
        'recent_activities': recent_activities,
        'math_games': math_games,
        'language_games': language_games,
        'science_games': science_games,
        'unlocked_rewards': unlocked_rewards,
        'pending_assignments': pending_assignments,
    }
    
    return render(request, 'dashboard/child_dashboard.html', context)