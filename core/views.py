from django.shortcuts import render
from .models import News, Event, Testimonial, Activity
from .models import TeamMember
from django.utils import timezone
from .models import Event, Closure
from django.core.mail import send_mail
from django.conf import settings
#from django.forms import ContactForm
from django.contrib import messages
from django.http import HttpResponse
# Create your views here.

def index(request):
    return HttpResponse("Core")

def home(request):
    context = {
        'latest_news': News.objects.filter(published=True).order_by('-date')[:3],
        'upcoming_events': Event.objects.filter(date__gte=timezone.now()).order_by('date')[:5],
        'testimonials': Testimonial.objects.filter(approved=True).order_by('-date')[:6],
    }
    return render(request, 'core/home.html', context)

def about(request):
    context = {
        'team_members': TeamMember.objects.filter(active=True).order_by('order'),
    }
    return render(request, 'core/about.html', context)

def schedule(request):
    # Emploi du temps quotidien (données statiques pour l'exemple)
    daily_schedule = [
        {'time': '7h30 - 9h00', 'title': 'Accueil des enfants', 'description': 'Activités libres', 'age_groups': 'Tous âges'},
        {'time': '9h00 - 9h30', 'title': 'Cercle du matin', 'description': 'Chants, comptines et présentation des activités', 'age_groups': 'Tous âges'},
        {'time': '9h30 - 11h30', 'title': 'Activités pédagogiques', 'description': 'Ateliers par groupe d\'âge', 'age_groups': 'Groupes spécifiques'},
        {'time': '11h30 - 12h30', 'title': 'Repas', 'description': 'Déjeuner équilibré préparé sur place', 'age_groups': 'Tous âges'},
        {'time': '12h30 - 14h30', 'title': 'Temps calme / Sieste', 'description': 'Repos pour les plus petits', 'age_groups': '0-3 ans'},
        {'time': '14h30 - 16h00', 'title': 'Activités créatives', 'description': 'Arts plastiques, musique, expression corporelle', 'age_groups': 'Tous âges'},
        {'time': '16h00 - 16h30', 'title': 'Goûter', 'description': 'Collation saine', 'age_groups': 'Tous âges'},
        {'time': '16h30 - 18h30', 'title': 'Activités libres & Départ', 'description': 'Jeux libres, lecture, départ échelonné', 'age_groups': 'Tous âges'},
    ]
    
    context = {
        'upcoming_events': Event.objects.filter(date__gte=timezone.now()).order_by('date')[:3],
        'daily_schedule': daily_schedule,
        'closures': Closure.objects.filter(end_date__gte=timezone.now()).order_by('start_date'),
    }
    return render(request, 'core/schedule.html', context)

def activities(request):
    context = {
        'regular_activities': Activity.objects.filter(is_special=False, active=True).order_by('?')[:9],
        'special_activities': Activity.objects.filter(is_special=True, active=True, date__gte=timezone.now()).order_by('date')[:6],
        'testimonials': Testimonial.objects.filter(approved=True).order_by('?')[:4],
    }
    return render(request, 'core/activities.html', context)
