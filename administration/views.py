from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from LMSapp.accounts.views import CustomUserCreationForm
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import (
    ContentCategory, Course, Lesson, 
    Resource, Activity, ContentAnalytics, EnrollmentStatusLog
)
from .forms import CourseForm, LessonForm, ResourceForm, ActivityForm, EnrollmentFilterForm
import csv
from django.http import HttpResponse
from LMSapp.enrollment.models import ChildEnrollment
import json
from datetime import datetime, timedelta
from django.db.models import Count, Q, Sum, Avg
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from LMSapp.enrollment.models import Child
from LMSapp.lms.models import ActivityRecord, ChildProgress
from LMSapp.communication.models import Notification
from .models import FinancialRecord, ReportConfiguration

def admin_home(request):
    return render(request, "administration/enrollment_admin.html")

def user_management(request):
    # Récupérer tous les utilisateurs
    users = User.objects.all().order_by('last_name', 'first_name')
    
    # Ajouter une propriété 'role' à chaque utilisateur
    for user in users:
        if hasattr(user, 'parentprofile'):
            user.role = 'parent'
        elif hasattr(user, 'teacherprofile'):
            user.role = 'teacher'
        elif hasattr(user, 'child'):
            user.role = 'child'
        elif user.is_superuser:
            user.role = 'admin'
        else:
            user.role = 'unknown'
    
    # Statistiques
    total_users = users.count()
    parent_count = CustomUserCreationForm.objects.count()
    teacher_count = CustomUserCreationForm.objects.count()
    child_count = CustomUserCreationForm.objects.count()
    
    # Pagination
    paginator = Paginator(users, 25)  # 25 utilisateurs par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calcul des indices pour l'affichage
    start_index = page_obj.start_index()
    end_index = page_obj.end_index()
    
    # Liste des parents pour le formulaire enfant
    parents = User.objects.filter(parentprofile__isnull=False)
    
    context = {
        'users': page_obj,
        'total_users': total_users,
        'parent_count': parent_count,
        'teacher_count': teacher_count,
        'child_count': child_count,
        'start_index': start_index,
        'end_index': end_index,
        'parents': parents,
        'page_range': paginator.page_range,
    }
    
    return render(request, 'administration/user_management.html', context)


def is_content_manager(user):
    return user.groups.filter(name='Content Managers').exists() or user.is_superuser

@login_required
@user_passes_test(is_content_manager)
def content_management(request):
    # Récupérer les statistiques
    courses_count = Course.objects.count()
    lessons_count = Lesson.objects.count()
    resources_count = Resource.objects.count()
    activities_count = Activity.objects.count()
    
    # Récupérer les catégories pour les filtres
    categories = ContentCategory.objects.all()
    
    # Récupérer les cours avec pagination
    courses_list = Course.objects.select_related('category', 'creator').order_by('-created_at')
    
    # Appliquer les filtres
    category_filter = request.GET.get('category', 'all')
    status_filter = request.GET.get('status', 'all')
    type_filter = request.GET.get('type', 'all')
    
    if category_filter != 'all':
        courses_list = courses_list.filter(category__id=category_filter)
    
    if status_filter != 'all':
        courses_list = courses_list.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(courses_list, 10)
    page_number = request.GET.get('page')
    courses = paginator.get_page(page_number)
    
    context = {
        'courses_count': courses_count,
        'lessons_count': lessons_count,
        'resources_count': resources_count,
        'activities_count': activities_count,
        'categories': categories,
        'courses': courses,
        'selected_category': category_filter,
        'selected_status': status_filter,
        'selected_type': type_filter,
    }
    
    return render(request, 'administration/content_management.html', context)

@login_required
@user_passes_test(is_content_manager)
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    lessons = course.lessons.order_by('order')
    
    # Récupérer les analytics
    analytics = ContentAnalytics.objects.filter(course=course).order_by('-date')[:30]
    
    context = {
        'course': course,
        'lessons': lessons,
        'analytics': analytics,
    }
    return render(request, 'administration/course_detail.html', context)

@login_required
@user_passes_test(is_content_manager)
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.creator = request.user
            course.save()
            return redirect('content_management')
    else:
        form = CourseForm()
    
    context = {'form': form}
    return render(request, 'administration/course_form.html', context)

@login_required
@user_passes_test(is_content_manager)
def edit_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('content_management')
    else:
        form = CourseForm(instance=course)
    
    context = {'form': form, 'course': course}
    return render(request, 'administration/course_form.html', context)

@login_required
@user_passes_test(is_content_manager)
def delete_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    if request.method == 'POST':
        course.delete()
        return redirect('content_management')
    
    context = {'course': course}
    return render(request, 'administration/delete_course.html', context)

@login_required
@user_passes_test(is_content_manager)
def change_course_status(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [Course.DRAFT, Course.PUBLISHED, Course.ARCHIVED]:
            course.status = new_status
            course.save()
        return redirect('content_management')
    
    context = {'course': course}
    return render(request, 'administration/change_status.html', context)

@login_required
@user_passes_test(is_content_manager)
def lesson_detail(request, course_slug, lesson_slug):
    lesson = get_object_or_404(Lesson, slug=lesson_slug, course__slug=course_slug)
    resources = lesson.resources.all()
    activities = lesson.activities.all()
    
    context = {
        'lesson': lesson,
        'resources': resources,
        'activities': activities,
    }
    return render(request, 'administration/lesson_detail.html', context)

# Vues similaires pour les leçons, ressources et activités
# (create_lesson, edit_lesson, delete_lesson, etc.)

@login_required
@user_passes_test(is_content_manager)
def content_analytics(request):
    # Récupérer les statistiques globales
    categories = ContentCategory.objects.annotate(
        course_count=Count('courses'),
        lesson_count=Count('courses__lessons'),
        resource_count=Count('courses__lessons__resources'),
        activity_count=Count('courses__lessons__activities'),
    )
    
    # Top cours par vues
    top_courses = Course.objects.annotate(
        total_views=Sum('analytics__views')
    ).order_by('-total_views')[:5]
    
    # Évolution des vues
    analytics = ContentAnalytics.objects.values('date').annotate(
        total_views=Sum('views'),
        total_downloads=Sum('downloads'),
        total_completions=Sum('completions'),
    ).order_by('date')
    
    context = {
        'categories': categories,
        'top_courses': top_courses,
        'analytics': analytics,
    }
    return render(request, 'administration/content_analytics.html', context)

def enrollment_admin(request):
    # Apply filters
    form = EnrollmentFilterForm(request.GET or None)
    enrollments = ChildEnrollment.objects.select_related('child', 'parent').order_by('-created_at')
    
    if form.is_valid():
        status = form.cleaned_data.get('status')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        age_group = form.cleaned_data.get('age_group')
        search = form.cleaned_data.get('search')
        
        if status:
            enrollments = enrollments.filter(status=status)
        if start_date:
            enrollments = enrollments.filter(created_at__gte=start_date)
        if end_date:
            enrollments = enrollments.filter(created_at__lte=end_date)
        if age_group:
            enrollments = enrollments.filter(child__age_group=age_group)
        if search:
            enrollments = enrollments.filter(
                Q(child__first_name__icontains=search) |
                Q(child__last_name__icontains=search) |
                Q(parent__user__first_name__icontains=search) |
                Q(parent__user__last_name__icontains=search)
            )
    
    # Export to CSV
    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="enrollments.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Child', 'Parent', 'Enrollment Date', 
            'Age Group', 'Status', 'Medical Notes'
        ])
        
        for e in enrollments:
            writer.writerow([
                e.id,
                f"{e.child.first_name} {e.child.last_name}",
                f"{e.parent.user.get_full_name()}",
                e.created_at.strftime('%Y-%m-%d'),
                e.child.age_group,
                e.get_status_display(),
                e.medical_notes[:100] + '...' if e.medical_notes else ''
            ])
        return response
    
    # Pagination
    paginator = Paginator(enrollments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'administration/enrollment_admin.html', {
        'page_obj': page_obj,
        'filter_form': form
    })

def update_enrollment_status(request, enrollment_id, new_status):
    enrollment = get_object_or_404(ChildEnrollment, id=enrollment_id)
    old_status = enrollment.status
    
    if old_status != new_status:
        enrollment.status = new_status
        enrollment.save()
        
        # Log status change
        EnrollmentStatusLog.objects.create(
            enrollment=enrollment,
            old_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            notes=f"Changed via admin panel"
        )
    
    return HttpResponse(status=204)  # No content response for AJAX

class ReportsView(View):
    template_name = 'administration/reports.html'
    
    def get(self, request):
        # Configuration par défaut
        default_config = {
            'period': 'current_year',
            'age_group': 'all',
            'class_group': 'all',
            'report_type': 'all'
        }
        
        # Appliquer les filtres
        filters = self.get_filters(request, default_config)
        
        # Calculer les statistiques
        stats = self.calculate_statistics(filters)
        context = {
            'stats': stats,
            'filters': filters,
            'default_config': default_config
        }
        return render(request, self.template_name, context)
    
    def get_filters(self, request, default_config):
        period = request.GET.get('period', default_config['period'])
        age_group = request.GET.get('age_group', default_config['age_group'])
        class_group = request.GET.get('class_group', default_config['class_group'])
        report_type = request.GET.get('report_type', default_config['report_type'])
        
        return {
            'period': period,
            'age_group': age_group,
            'class_group': class_group,
            'report_type': report_type
        }
    
    def calculate_statistics(self, filters):
        # Calculer les dates en fonction de la période
        start_date, end_date = self.get_date_range(filters['period'])
        
        # Statistiques de base
        total_children = Child.objects.count()
        capacity = 90  # Capacité maximale théorique
        occupancy_rate = round((total_children / capacity) * 100) if capacity > 0 else 0
        
        # Activités
        activities_count = Activity.objects.filter(
            date__range=(start_date, end_date))
        if filters['age_group'] != 'all':
            activities_count = activities_count.filter(age_group=filters['age_group'])
        activities_count = activities_count.count()
        
        # Taux de rétention (simplifié)
        retention_rate = 89  # À remplacer par un calcul réel
        
        # Répartition par âge
        age_distribution = Child.objects.values('age_group').annotate(
            total=Count('id')).order_by('age_group')
        
        # Statut des inscriptions
        enrollment_status = ChildEnrollment.objects.values('status').annotate(
            total=Count('id'))
        
        # Progrès des enfants
        progress_data = self.get_child_progress(filters)
        
        # Activités populaires
        popular_activities = self.get_popular_activities(filters)
        
        # Données financières
        financial_data = self.get_financial_data(start_date, end_date)
        
        return {
            'total_children': total_children,
            'occupancy_rate': occupancy_rate,
            'activities_count': activities_count,
            'retention_rate': retention_rate,
            'age_distribution': list(age_distribution),
            'enrollment_status': list(enrollment_status),
            'child_progress': progress_data,
            'popular_activities': popular_activities,
            'financial_data': financial_data,
            'period_labels': self.get_period_labels(filters['period'])
        }
    
    def get_date_range(self, period):
        today = timezone.now().date()
        if period == 'last_month':
            start_date = today.replace(day=1) - timedelta(days=30)
            end_date = today.replace(day=1) - timedelta(days=1)
        elif period == 'current_quarter':
            quarter = (today.month - 1) // 3 + 1
            start_date = datetime(today.year, 3 * quarter - 2, 1).date()
            end_date = today
        elif period == 'last_year':
            start_date = today.replace(year=today.year-1, month=1, day=1)
            end_date = today.replace(year=today.year-1, month=12, day=31)
        else:  # current_year (par défaut)
            start_date = today.replace(month=1, day=1)
            end_date = today
        
        return start_date, end_date
    
    def get_period_labels(self, period):
        if period == 'last_month':
            return ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4']
        elif period in ['current_quarter', 'last_year']:
            return ['Mois 1', 'Mois 2', 'Mois 3']
        else:  # current_year
            return ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
    
    def get_child_progress(self, filters):
        progress_categories = [
            'social_development',
            'cognitive_skills',
            'creative_expression',
            'fine_motor',
            'gross_motor'
        ]
        
        progress_data = {}
        for category in progress_categories:
            avg_progress = ChildProgress.objects.filter(
                progress_type=category
            ).aggregate(avg=Avg('progress_value'))['avg'] or 0
            
            progress_data[category] = {
                'average': round(avg_progress),
                'trend': 5  # Tendance simulée
            }
        
        return progress_data
    
    def get_popular_activities(self, filters):
        activities = Activity.objects.annotate(
            participation_count=Count('participations')
        ).order_by('-participation_count')[:5]
        
        result = []
        for activity in activities:
            satisfaction = ActivityRecord.objects.filter(
                activity=activity
            ).aggregate(avg=Avg('satisfaction_rating'))['avg'] or 0
            
            result.append({
                'name': activity.name,
                'type': activity.activity_type,
                'participation_rate': activity.participation_rate,
                'satisfaction': round(satisfaction),
                'trend': 8  # Tendance simulée
            })
        
        return result
    
    def get_financial_data(self, start_date, end_date):
        income = FinancialRecord.objects.filter(
            record_type='income',
            date__range=(start_date, end_date)
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expenses = FinancialRecord.objects.filter(
            record_type='expense',
            date__range=(start_date, end_date)
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'income': income,
            'expenses': expenses,
            'net_profit': income - expenses
        }

class ReportsDataView(View):
    def get(self, request):
        report_type = request.GET.get('type')
        
        if report_type == 'enrollment_trend':
            data = self.get_enrollment_trend_data()
        elif report_type == 'age_distribution':
            data = self.get_age_distribution_data()
        elif report_type == 'financial':
            data = self.get_financial_data()
        else:
            data = {}
        
        return JsonResponse(data)
    
    def get_enrollment_trend_data(self):
        # Données simulées - à remplacer par des données réelles
        months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
        current_year = [32, 45, 52, 58, 64, 70, 72, 75, 78, 80, 82, 84]
        last_year = [28, 38, 44, 50, 56, 62, 65, 68, 70, 72, 74, 75]
        
        return {
            'labels': months,
            'datasets': [
                {
                    'label': '2024-2025',
                    'data': current_year,
                    'borderColor': '#0d6efd'
                },
                {
                    'label': '2023-2024',
                    'data': last_year,
                    'borderColor': '#6c757d'
                }
            ]
        }
    
    def get_age_distribution_data(self):
        # Données réelles de la base de données
        distribution = Child.objects.values('age_group').annotate(
            count=Count('id')).order_by('age_group')
        
        labels = []
        data = []
        colors = []
        
        for group in distribution:
            labels.append(group['age_group'])
            data.append(group['count'])
            
            if 'Petits' in group['age_group']:
                colors.append('#0d6efd')
            else:
                colors.append('#198754')
        
        return {
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': colors
            }]
        }
    
    def get_financial_data(self):
        # Données des 6 derniers mois
        months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin']
        income = [11200, 11800, 12200, 12400, 12600, 12840]
        expenses = [7800, 7950, 8100, 8200, 8300, 8230]
        
        return {
            'labels': months,
            'datasets': [
                {
                    'label': 'Revenus',
                    'data': income,
                    'backgroundColor': '#198754'
                },
                {
                    'label': 'Dépenses',
                    'data': expenses,
                    'backgroundColor': '#dc3545'
                }
            ]
        }