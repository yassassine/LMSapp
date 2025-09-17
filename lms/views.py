from django.shortcuts import render,get_object_or_404
from django.db.models import Count, Prefetch, Sum
from django.views.generic import DetailView
from .models import Course, Module, Resource, InteractiveActivity, ChildProgress, ChildProfile, User, CourseCategory, Assignment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView
from django.urls import reverse_lazy
from .models import Assignment, AssignmentSubmission, SubmittedFile
from .forms import AssignmentSubmissionForm
from django.contrib import messages
from .models import ActivityCategory, InteractiveActivity, ChildActivityProgress
from .models import ChildProfile, ProgressCategory, ChildProgress, ActivityRecord, Milestone, Reward


# Create your views here.

def get_user_progress(user):
    """Get progress data for authenticated users"""
    if not user.is_authenticated:
        return None
        
    return {
        'completed': user.enrollments.filter(status='completed').count(),
        'total': Course.objects.count(),
        'badges': 8,
        'total_badges': 20,
        'activities': 26,
        'total_activities': 40
    }

def get_course_modules(course):
    """Prefetch modules with their related resources and activities"""
    modules_prefetch = Prefetch(
        'modules',
        queryset=Module.objects.prefetch_related(
            Prefetch('resources', queryset=Resource.objects.all()),
            Prefetch('activities', queryset=InteractiveActivity.objects.all())
        ).order_by('order')
    )
    
    return Course.objects.prefetch_related(modules_prefetch).get(pk=course.pk)

def get_child_progress(user, course):
    """Get child progress for parent users"""
    if not user.is_parent:
        return None
        
    children = ChildProfile.objects.filter(parent=user)
    return ChildProgress.objects.filter(
        child__in=children, 
        course=course
    ).select_related('child')

def get_assignment_stats(queryset):
    """Get assignment statistics"""
    return {
        'total_assignments': queryset.count(),
        'pending_count': queryset.filter(status='pending').count(),
        'submitted_count': queryset.filter(status='submitted').count(),
        'completed_count': queryset.filter(status='completed').count()
    }

def get_active_child(user, child_id=None):
    """Get active child for the user"""
    if not user.is_parent:
        return None
        
    if child_id:
        return User.objects.get(id=child_id)
    return user.children.first()

def get_activities_with_progress(activities, active_child):
    """Get activities with progress data"""
    activities_with_progress = []
    
    for activity in activities:
        progress = None
        if active_child:
            try:
                progress = ChildActivityProgress.objects.get(
                    child=active_child, 
                    activity=activity
                )
            except ChildActivityProgress.DoesNotExist:
                progress = ChildActivityProgress(
                    child=active_child,
                    activity=activity,
                    stars_earned=0,
                    completion_rate=0
                )
        activities_with_progress.append({
            'activity': activity,
            'progress': progress
        })
    
    return activities_with_progress

def get_category_progress(categories, activities, active_child):
    """Get progress by category"""
    category_progress = {}
    
    for category in categories:
        if active_child:
            category_activities = activities.filter(category=category)
            completed = ChildActivityProgress.objects.filter(
                child=active_child,
                activity__in=category_activities,
                completion_rate=100
            ).count()
            total = category_activities.count()
            progress = round((completed / total) * 100) if total > 0 else 0
        else:
            progress = 0
        category_progress[category.name] = progress
    
    return category_progress

# View functions and classes
def course_list(request):
    # Récupérer tous les cours
    courses = Course.objects.all().order_by('-created_at')
    
    # Récupérer les catégories avec le nombre de cours
    categories = CourseCategory.objects.annotate(course_count=Count('course'))
    
    # Get progress data
    progress = get_user_progress(request.user)
    
    context = {
        'courses': courses,
        'categories': categories,
        'courses_count': courses.count(),
        'progress': progress
    }
    return render(request, 'lms/course_list.html', context)


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'lms/course_detail.html'
    context_object_name = 'course'
    
    def get_object(self, queryset=None):
        return get_object_or_404(
            Course.objects.select_related('teacher'),
            pk=self.kwargs['pk'],
            slug=self.kwargs['slug']
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        
        # Prefetch modules with relations
        course = get_course_modules(course)
        
        # Get child progress
        child_progress = get_child_progress(self.request.user, course)
        
        # Calculate overall progress
        progress = {
            'overall': 65,
            'resources': 80,
            'activities': 40
        }
        
        context.update({
            'modules': course.modules.all(),
            'progress': progress,
            'child_progress': child_progress
        })
        
        return context


class AssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment
    template_name = 'lms/assignment_list.html'
    context_object_name = 'assignments'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrer par enfants (pour les parents)
        if self.request.user.is_parent:
            children = self.request.user.children.all()
            queryset = queryset.filter(children__in=children).distinct()
        
        # Filtrer par statut
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Filtrer par cours
        course_id = self.request.GET.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
            
        return queryset.prefetch_related('children').order_by('-due_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get assignment statistics
        assignments = self.get_queryset()
        context.update(get_assignment_stats(assignments))
        
        return context


class AssignmentSubmitView(FormView):
    template_name = 'lms/assignment_submit.html'
    form_class = AssignmentSubmissionForm
    success_url = reverse_lazy('lms:assignment_submit_success')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment_id = self.kwargs['assignment_id']
        assignment = get_object_or_404(Assignment, id=assignment_id)
        
        # Récupérer les soumissions précédentes
        previous_submissions = AssignmentSubmission.objects.filter(
            assignment=assignment,
            child__in=self.request.user.children.all()
        ).order_by('-created_at')
        
        context.update({
            'assignment': assignment,
            'previous_submissions': previous_submissions,
            'children': self.request.user.children.all()
        })
        return context
    
    def form_valid(self, form):
        # Créer la soumission
        submission = form.save(commit=False)
        submission.assignment = get_object_or_404(Assignment, id=self.kwargs['assignment_id'])
        submission.submitted_by = self.request.user
        submission.status = 'draft' if 'save_draft' in self.request.POST else 'submitted'
        submission.save()
        
        # Gestion des fichiers
        files = self.request.FILES.getlist('files')
        for file in files:
            SubmittedFile.objects.create(
                submission=submission,
                file=file,
                original_filename=file.name,
                file_size=file.size
            )
        
        # Message de succès
        if submission.status == 'submitted':
            messages.success(self.request, 'Devoir soumis avec succès!')
        else:
            messages.info(self.request, 'Brouillon enregistré avec succès')
        
        return super().form_valid(form)


class InteractiveActivitiesView(LoginRequiredMixin, TemplateView):
    template_name = 'lms/interactive_activities.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer l'enfant actif (simplifié)
        active_child = get_active_child(self.request.user)
        
        # Récupérer toutes les catégories
        categories = ActivityCategory.objects.all()
        
        # Récupérer toutes les activités avec progression
        activities = InteractiveActivity.objects.all()
        activities_with_progress = get_activities_with_progress(activities, active_child)
        
        # Calculer la progression par catégorie
        category_progress = get_category_progress(categories, activities, active_child)
        
        # Calculer le total des étoiles
        total_stars = 0
        if active_child:
            total_stars = ChildActivityProgress.objects.filter(
                child=active_child
            ).aggregate(Sum('stars_earned'))['stars_earned__sum'] or 0
        
        context.update({
            'active_child': active_child,
            'categories': categories,
            'activities': activities_with_progress,
            'category_progress': category_progress,
            'total_stars': total_stars
        })
        return context


class ProgressTrackingView(LoginRequiredMixin, TemplateView):
    template_name = 'lms/progress_tracking.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer l'enfant actif
        child_id = self.request.GET.get('child')
        active_child = get_active_child(self.request.user, child_id)
        
        if not active_child:
            return context
        
        # Récupérer les données de progression
        categories = ProgressCategory.objects.all()
        progress_data = []
        
        for category in categories:
            try:
                progress = ChildProgress.objects.get(child=active_child, category=category)
                progress_data.append({
                    'category': category,
                    'score': progress.score
                })
            except ChildProgress.DoesNotExist:
                progress_data.append({
                    'category': category,
                    'score': 0
                })
        
        # Récupérer les activités récentes
        recent_activities = ActivityRecord.objects.filter(child=active_child).order_by('-date')[:5]
        
        # Récupérer les objectifs
        milestones = Milestone.objects.filter(child=active_child)
        
        # Récupérer les récompenses
        rewards = Reward.objects.filter(child=active_child)
        total_stars = rewards.filter(reward_type='star').count()
        
        # Préparer les données pour les graphiques
        category_names = [cat.name for cat in categories]
        scores = [item['score'] for item in progress_data]
        
        # Comparaison avec le groupe (simulé)
        group_avg = {
            'Mathématiques': 75,
            'Langage': 80,
            'Arts': 85,
            'Science': 70,
            'Musique': 75
        }
        
        context.update({
            'active_child': active_child,
            'child_profile': active_child.child_profile,
            'progress_data': progress_data,
            'recent_activities': recent_activities,
            'milestones': milestones,
            'rewards': rewards,
            'total_stars': total_stars,
            'category_names': category_names,
            'scores': scores,
            'group_avg': group_avg
        })
        return context